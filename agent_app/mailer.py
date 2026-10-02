"""Mail accounts: SMTP sending and IMAP fetching.

Passwords (Gmail app passwords) live only in Windows Credential Manager (keyring service
"jobsearch-mail"); they are entered by the user in the Settings page and never returned by the API.
"""
import email
import email.header
import email.utils
import imaplib
import mimetypes
import re
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path

import keyring

from . import store

KEYRING_SERVICE = "jobsearch-mail"
ATS_DOMAINS = ("herp.cloud", "talentio.com", "hrmos.co", "jobcan", "saiyo.jp", "i-webs.jp", "wantedly.com")

def accounts():
    """Mail accounts come from owner.json ("mail_accounts") in the data folder."""
    accs = store.get_setting("mail_accounts") or store.owner().get("mail_accounts") or []
    for a in accs:
        a["has_password"] = bool(keyring.get_password(KEYRING_SERVICE, a["address"]))
    return accs


def account(acc_id):
    for a in accounts():
        if a["id"] == acc_id or a["address"] == acc_id:
            return a
    raise ValueError(f"unknown mail account {acc_id}")


def default_account():
    accs = accounts()
    return store.get_setting("default_account") or (accs[0]["id"] if accs else None)


def set_password(acc_id, password):
    a = account(acc_id)
    pw = password.replace(" ", "")
    with smtplib.SMTP(a["smtp_host"], a["smtp_port"], timeout=30) as s:   # verify before saving
        s.starttls()
        s.login(a["address"], pw)
    keyring.set_password(KEYRING_SERVICE, a["address"], pw)


def _password(a):
    pw = keyring.get_password(KEYRING_SERVICE, a["address"])
    if not pw:
        raise RuntimeError(f"邮箱 {a['address']} 还没有设置应用专用密码（设置页面）")
    return pw


PLACEHOLDER = re.compile(r"【要記入|\[TO FILL|\[placeholder|［要|○○|\[.*?記入.*?\]", re.I)


def check_email(p):
    problems = []
    if not p.get("to"):
        problems.append("没有收件人")
    for addr in p.get("to", []) + p.get("cc", []):
        if not re.fullmatch(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", addr):
            problems.append(f"可疑地址: {addr}")
    if not p.get("subject"):
        problems.append("主题为空")
    for hit in PLACEHOLDER.findall((p.get("subject") or "") + (p.get("body") or "")):
        problems.append(f"正文里还有占位符: {hit}")
    for f in p.get("attachments", []):
        if not (store.HOME / f).exists() and not Path(f).exists():
            problems.append(f"附件不存在: {f}")
    return problems


def send(p):
    """p: {account, to[], cc[], subject, body, attachments[], in_reply_to?}  → Message-ID"""
    a = account(p.get("account") or default_account())
    problems = check_email(p)
    if problems:
        raise RuntimeError("; ".join(problems))
    msg = EmailMessage()
    msg["From"] = formataddr((a["display_name"], a["address"]))
    msg["To"] = ", ".join(p["to"])
    if p.get("cc"):
        msg["Cc"] = ", ".join(p["cc"])
    msg["Subject"] = p["subject"]
    msg["Message-ID"] = make_msgid(domain=a["address"].split("@")[1])
    if p.get("in_reply_to"):
        msg["In-Reply-To"] = p["in_reply_to"]
        msg["References"] = p["in_reply_to"]
    msg.set_content(p["body"])
    for f in p.get("attachments", []):
        path = store.HOME / f if (store.HOME / f).exists() else Path(f)
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        msg.add_attachment(path.read_bytes(), maintype=maintype, subtype=subtype, filename=path.name)
    rcpts = p["to"] + p.get("cc", []) + [a["address"]]          # bcc self keeps a copy
    with smtplib.SMTP(a["smtp_host"], a["smtp_port"], timeout=60) as s:
        s.starttls()
        s.login(a["address"], _password(a))
        s.send_message(msg, to_addrs=rcpts)
    sent_dir = store.HOME / "outbox" / "sent"
    sent_dir.mkdir(parents=True, exist_ok=True)
    (sent_dir / f"{datetime.now():%Y%m%d_%H%M%S}_{re.sub(r'[^\w]+', '_', p['subject'])[:40]}.eml").write_bytes(bytes(msg))
    return msg["Message-ID"]


def _decode(s):
    if not s:
        return ""
    return str(email.header.make_header(email.header.decode_header(s)))


def _body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                html = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
                return re.sub(r"<[^>]+>", " ", html)
        return ""
    return msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", "replace")


def _match_company(from_addr, subject, body):
    cid = store.match_company_by_email(from_addr)
    if cid:
        return cid
    # ATS mails (HERP, HRMOS, Talentio, jobcan …) come from shared domains → match by company name
    text = f"{subject}\n{body[:1500]}"
    applied = store.rows("""SELECT DISTINCT c.id, c.name, c.name_ja FROM outreach o JOIN companies c
                            ON c.id=o.company_id""")
    for c in applied:
        for n in (c["name_ja"], c["name"]):
            if not n:
                continue
            core = re.sub(r"(株式会社|Co\.,?\s*Ltd\.?|Inc\.?|Corporation|Corp\.?|,)", "", n, flags=re.I).strip()
            if len(core) >= 3 and core.lower() in text.lower():
                return c["id"]
    return None


def fetch(acc_id=None, days=14, only_jobs=True):
    """Fetch recent mail from INBOX into the inbox table. Returns number of new messages stored."""
    targets = [account(acc_id)] if acc_id else [a for a in accounts() if a["has_password"]]
    new = 0
    since = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
    for a in targets:
        m = imaplib.IMAP4_SSL(a["imap_host"])
        try:
            m.login(a["address"], _password(a))
            m.select("INBOX", readonly=True)
            _, data = m.uid("search", None, f'(SINCE "{since}")')
            uids = data[0].split()[-300:]
            known = {r["uid"] for r in store.rows("SELECT uid FROM inbox WHERE account=?", (a["id"],))}
            for uid in uids:
                uid_s = uid.decode()
                if uid_s in known:
                    continue
                _, msgdata = m.uid("fetch", uid, "(BODY.PEEK[])")
                msg = email.message_from_bytes(msgdata[0][1])
                name, addr = email.utils.parseaddr(_decode(msg.get("From")))
                subject = _decode(msg.get("Subject"))
                body = _body(msg)[:20000]
                cid = _match_company(addr, subject, body)
                is_job = bool(cid) or any(d in addr.lower() for d in ATS_DOMAINS) or re.search(
                    r"(選考|応募|採用|面談|面接|エントリー|application|interview|recruit)", subject, re.I)
                if only_jobs and not is_job:
                    continue
                try:
                    dt = email.utils.parsedate_to_datetime(msg.get("Date")).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    dt = ""
                store.execute("""INSERT OR IGNORE INTO inbox(account,uid,message_id,from_addr,from_name,subject,
                                 date,body,company_id) VALUES(?,?,?,?,?,?,?,?,?)""",
                              (a["id"], uid_s, msg.get("Message-ID"), addr, name, subject, dt, body, cid))
                new += 1
        finally:
            try:
                m.logout()
            except Exception:
                pass
    return new
