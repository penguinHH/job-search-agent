"""Job-application mail sender (SMTP). Sends ONE prepared message at a time.

Mail files live in outbox/mail/*.md and look like:

    ---
    to: recruit@example.co.jp
    cc:
    subject: 2027年度新卒採用 ... お問い合わせ
    company_id: 123
    attachments: outbox/common/Resume.docx   # optional, ';'-separated
    pdf: yes            # optional: convert .docx attachments to PDF with Word before sending
    ---
    本文 ...

Setup (run by YOU in a terminal — the password is typed by you and stored in Windows
Credential Manager; it is never written to disk or shown to anyone):

    python send_mail.py setup

Usage:
    python send_mail.py list                         # mail files and their status
    python send_mail.py preview outbox/mail/x.md     # render + safety checks, sends nothing
    python send_mail.py test                         # send a test mail to yourself
    python send_mail.py send outbox/mail/x.md --confirm
    python send_mail.py log outbox/mail/x.md --message-id <id>   # record a mail sent via the Gmail connector
"""
import argparse
import getpass
import json
import mimetypes
import re
import shutil
import smtplib
import subprocess
import sys
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path

import keyring

sys.stdout.reconfigure(encoding="utf-8")

from config import HOME as ROOT, owner
from db import connect

CONFIG = ROOT / "profile" / "mail_config.json"      # non-secret settings only
MAIL_DIR = ROOT / "outbox" / "mail"
SENT_DIR = ROOT / "outbox" / "sent"
KEYRING_SERVICE = "jobsearch-smtp"
PLACEHOLDER = re.compile(r"【要記入|\[TO FILL|\[placeholder|［要|［例|［講義|［データ|○○|\[.*?記入.*?\]", re.I)

_acc = (owner().get("mail_accounts") or [{}])[-1]
DEFAULT_CONFIG = {
    "from_name": _acc.get("display_name", ""),
    "from_addr": _acc.get("address", ""),
    "smtp_host": _acc.get("smtp_host", "smtp.gmail.com"),
    "smtp_port": _acc.get("smtp_port", 587),
    "username": _acc.get("address", ""),
    "bcc_self": True,                    # keep a copy in your own inbox
}

MAIL_LOG_SQL = """CREATE TABLE IF NOT EXISTS mail_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, to_addr TEXT, cc TEXT, subject TEXT,
    attachments TEXT, message_id TEXT, source_file TEXT, archived_copy TEXT,
    sent_at TEXT DEFAULT (datetime('now','localtime')))"""


def load_config() -> dict:
    if not CONFIG.exists():
        CONFIG.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**DEFAULT_CONFIG, **json.loads(CONFIG.read_text(encoding="utf-8"))}


def parse_mail(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        raise SystemExit(f"{path}: missing '---' header block")
    head, body = m.groups()
    meta = {}
    for line in head.splitlines():
        line = re.sub(r"\s+#.*$", "", line)
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    split = lambda v: [x.strip() for x in re.split(r"[;,]", v or "") if x.strip()]
    return {
        "to": split(meta.get("to")), "cc": split(meta.get("cc")), "subject": meta.get("subject", ""),
        "company_id": int(meta["company_id"]) if meta.get("company_id", "").isdigit() else None,
        "attachments": [ROOT / a for a in split(meta.get("attachments"))],
        "pdf": meta.get("pdf", "").lower() in ("yes", "true", "1"), "body": body.strip() + "\n",
    }


def docx_to_pdf(src: Path) -> Path:
    out = SENT_DIR / "_pdf" / (src.stem + ".pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    ps = (f"$w=New-Object -ComObject Word.Application;$w.Visible=$false;"
          f"$d=$w.Documents.Open('{src}',$false,$true);$d.SaveAs2('{out}',17);$d.Close($false);$w.Quit()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, capture_output=True)
    return out


def checks(mail: dict) -> list[str]:
    problems = []
    if not mail["to"]:
        problems.append("no recipient (to:)")
    for addr in mail["to"] + mail["cc"]:
        if not re.fullmatch(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", addr):
            problems.append(f"suspicious address: {addr}")
    if not mail["subject"]:
        problems.append("empty subject")
    for hit in PLACEHOLDER.findall(mail["subject"] + mail["body"]):
        problems.append(f"placeholder left in text: {hit}")
    for a in mail["attachments"]:
        if not a.exists():
            problems.append(f"attachment not found: {a}")
        elif a.suffix.lower() == ".docx":
            from build_profile import extract_text
            t = extract_text(a)
            for hit in set(PLACEHOLDER.findall(t)):
                problems.append(f"placeholder inside attachment {a.name}: {hit}")
    return problems


def build(mail: dict, cfg: dict) -> tuple[EmailMessage, list[Path]]:
    msg = EmailMessage()
    msg["From"] = formataddr((cfg["from_name"], cfg["from_addr"]))
    msg["To"] = ", ".join(mail["to"])
    if mail["cc"]:
        msg["Cc"] = ", ".join(mail["cc"])
    msg["Subject"] = mail["subject"]
    msg["Message-ID"] = make_msgid(domain=cfg["from_addr"].split("@")[1])
    msg.set_content(mail["body"])
    files = []
    for a in mail["attachments"]:
        f = docx_to_pdf(a) if mail["pdf"] and a.suffix.lower() == ".docx" else a
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        msg.add_attachment(f.read_bytes(), maintype=maintype, subtype=subtype, filename=f.name)
        files.append(f)
    return msg, files


def show(mail: dict, cfg: dict):
    print(f"From:    {cfg['from_name']} <{cfg['from_addr']}>")
    print(f"To:      {', '.join(mail['to'])}")
    if mail["cc"]:
        print(f"Cc:      {', '.join(mail['cc'])}")
    print(f"Subject: {mail['subject']}")
    print(f"Attach:  {', '.join(str(a.relative_to(ROOT)) for a in mail['attachments']) or '-'}"
          f"{'  (docx→PDF)' if mail['pdf'] else ''}")
    print(f"Company: {mail['company_id'] or '-'}\n" + "-" * 60 + f"\n{mail['body']}" + "-" * 60)


def smtp_send(msg: EmailMessage, cfg: dict, extra_bcc: list[str]):
    pw = keyring.get_password(KEYRING_SERVICE, cfg["username"])
    if not pw:
        raise SystemExit("No SMTP password stored. Run `python send_mail.py setup` yourself first.")
    rcpts = [a.strip() for h in ("To", "Cc") for a in (msg.get(h) or "").split(",") if a.strip()] + extra_bcc
    with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"], timeout=30) as s:
        s.starttls()
        s.login(cfg["username"], pw)
        s.send_message(msg, to_addrs=[re.sub(r".*<(.+)>", r"\1", r) for r in rcpts])


def cmd_setup():
    cfg = load_config()
    print(f"Settings file: {CONFIG}\n  from: {cfg['from_addr']}  server: {cfg['smtp_host']}:{cfg['smtp_port']}")
    print("For Gmail / Google Workspace use an *App Password* (Google account → Security →")
    print("2-Step Verification → App passwords), not your normal password.")
    pw = getpass.getpass(f"App password for {cfg['username']} (input hidden): ").replace(" ", "")
    if not pw:
        raise SystemExit("aborted")
    keyring.set_password(KEYRING_SERVICE, cfg["username"], pw)
    try:
        with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"], timeout=30) as s:
            s.starttls(); s.login(cfg["username"], pw)
        print("Login OK - password saved in Windows Credential Manager.")
    except smtplib.SMTPAuthenticationError as e:
        keyring.delete_password(KEYRING_SERVICE, cfg["username"])
        raise SystemExit(f"Login failed ({e.smtp_code}); nothing saved. Check the app password / account policy.")


def record(mail: dict, msg: EmailMessage, src: Path, copy: Path):
    conn = connect()
    conn.execute(MAIL_LOG_SQL)
    conn.execute("INSERT INTO mail_log(company_id,to_addr,cc,subject,attachments,message_id,source_file,archived_copy)"
                 " VALUES (?,?,?,?,?,?,?,?)",
                 (mail["company_id"], ", ".join(mail["to"]), ", ".join(mail["cc"]), mail["subject"],
                  "; ".join(a.name for a in mail["attachments"]), msg["Message-ID"], str(src), str(copy)))
    if mail["company_id"]:
        conn.execute("INSERT INTO outreach(company_id, stage, note, draft_path) VALUES (?,?,?,?)",
                     (mail["company_id"], "sent", f"email sent: {mail['subject']} → {', '.join(mail['to'])}",
                      str(copy)))
    conn.commit()


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup"); sub.add_parser("list"); sub.add_parser("test")
    p = sub.add_parser("preview"); p.add_argument("file")
    p = sub.add_parser("send"); p.add_argument("file"); p.add_argument("--confirm", action="store_true")
    p = sub.add_parser("log"); p.add_argument("file"); p.add_argument("--message-id", required=True)
    a = ap.parse_args()
    MAIL_DIR.mkdir(parents=True, exist_ok=True); SENT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = load_config()

    if a.cmd == "setup":
        cmd_setup()
    elif a.cmd == "list":
        sent = {r[0] for r in connect().execute("SELECT source_file FROM mail_log")} if \
            connect().execute("SELECT name FROM sqlite_master WHERE name='mail_log'").fetchone() else set()
        for f in sorted(MAIL_DIR.glob("*.md")):
            m = parse_mail(f)
            state = "SENT" if str(f) in sent else ("NEEDS FIX" if checks(m) else "ready")
            print(f"{state:9s}  {f.name:45s}  → {', '.join(m['to'])}  | {m['subject'][:50]}")
    elif a.cmd == "log":
        src = Path(a.file).resolve()
        mail = parse_mail(src)
        msg = EmailMessage()
        msg["Message-ID"] = a.message_id
        copy = SENT_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{src.stem}.md"
        shutil.copy(src, copy)
        record(mail, msg, src, copy)
        print(f"logged ✓ {src.name} (gmail id {a.message_id})")
    elif a.cmd == "test":
        msg = EmailMessage()
        msg["From"] = formataddr((cfg["from_name"], cfg["from_addr"])); msg["To"] = cfg["from_addr"]
        msg["Subject"] = "送信テスト / send_mail.py test"; msg.set_content("This is a test from send_mail.py.")
        smtp_send(msg, cfg, [])
        print(f"test mail sent to {cfg['from_addr']}")
    else:
        src = Path(a.file).resolve()
        mail = parse_mail(src)
        show(mail, cfg)
        problems = checks(mail)
        if problems:
            print("\n✗ NOT READY:\n  - " + "\n  - ".join(problems))
            if a.cmd == "send":
                raise SystemExit(1)
        else:
            print("\n✓ checks passed")
        if a.cmd == "send":
            if not a.confirm:
                raise SystemExit("\nDry run only. Re-run with --confirm to actually send.")
            msg, files = build(mail, cfg)
            smtp_send(msg, cfg, [cfg["from_addr"]] if cfg.get("bcc_self") else [])
            copy = SENT_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{src.stem}.eml"
            copy.write_bytes(bytes(msg))
            record(mail, msg, src, copy)
            print(f"\nSENT ✓  Message-ID {msg['Message-ID']}\n  copy: {copy}")


if __name__ == "__main__":
    main()
