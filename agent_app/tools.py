"""Tools the agent can call. Each tool = JSON schema + Python implementation.

Outward-facing actions never happen directly: `queue_email` and submit-like browser clicks
create an entry in the approval queue (`actions`), which the user approves in the GUI.
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from . import mailer, store
from .browser import browser

ROOT = store.ROOT          # code
HOME = store.HOME          # personal data folder (资料)
FINAL = HOME / "outbox" / "common" / "final"


def _j(obj):
    return json.dumps(obj, ensure_ascii=False, default=str)


def _p(path):
    """Paths the agent passes are relative to the project root; keep them inside it."""
    p = (HOME / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if not p.is_relative_to(HOME):
        raise ValueError("path must be inside the data folder")
    return p


# ---------------------------------------------------------------- implementations
def search_companies(query="", type=None, category="A", applied=None, min_score=None, prefecture=None,
                     limit=25, offset=0):
    r = store.search_companies(query, type, category, None, applied, min_score, prefecture, min(limit, 80), offset)
    return _j(r)


def get_company(company_id, full=False):
    c = store.company(company_id, full)
    return _j(c) if c else f"company {company_id} not found"


def add_company(name, website, types="2", prefecture="", note="", enrich=True):
    from urllib.parse import urlparse
    domain = urlparse(website).netloc.replace("www.", "")
    ex = store.row("SELECT id,name FROM companies WHERE domain=? OR name=?", (domain, name))
    if ex:
        return f"already in database: #{ex['id']} {ex['name']}"
    cid = store.execute("""INSERT INTO companies(source,source_id,name,website,domain,status,region,prefecture,
                           category,types,type_basis,sources) VALUES('manual',?,?,?,?,'active','japan',?,'A',?,?,'manual')""",
                        (domain or name, name, website, domain, prefecture, types, f"manual: {note}"))
    if enrich:
        enrich_company(cid)
    return f"added #{cid} {name}"


def enrich_company(company_id):
    sys.path.insert(0, str(ROOT / "scrapers"))
    from enrich import enrich_one
    c = store.row("SELECT id, website FROM companies WHERE id=?", (company_id,))
    out = enrich_one(c)
    cols = [k for k in out if k != "id"]
    store.execute(f"UPDATE companies SET {', '.join(f'{k}=?' for k in cols)} WHERE id=?",
                  [out[k] for k in cols] + [company_id])
    return _j({k: (str(v)[:300] if v else v) for k, v in out.items()})


def score_company(company_id, score, roles=None, reasons=None, concerns=None):
    store.set_score(company_id, score, roles, reasons, concerns)
    return f"score {score} saved for #{company_id}"


def update_stage(company_id, stage, note=""):
    store.set_stage(company_id, stage, note)
    return f"#{company_id} → {stage}"


def get_pipeline():
    return _j(store.pipeline())


def get_profile():
    p = store.profile()
    return _j({"profile_md": p["markdown"], "structured": p["structured"]})


def edit_profile(old_text, new_text):
    p = store.profile()
    md = p["markdown"]
    if old_text not in md:
        return "old_text not found in profile.md - read it with get_profile first"
    store.save_profile_md(md.replace(old_text, new_text, 1))
    return "profile.md updated"


def list_questions(status="open"):
    return _j(store.questions(status))


def ask_user(question, topic="", needed_for="", priority="normal"):
    qid = store.ask(question, topic, needed_for, priority)
    return f"question #{qid} added to the user's to-do list"


def record_answer(question_id, answer):
    store.answer(question_id, answer)
    return f"#{question_id} answered"


def fetch_url(url, max_chars=12000):
    r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126"})
    r.encoding = r.apparent_encoding if r.encoding in (None, "ISO-8859-1") else r.encoding
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        t = a.get_text(" ", strip=True)
        if t and re.search(r"採用|募集|応募|recruit|career|job|apply|entry|エントリー|contact|お問い合わせ", t + a["href"], re.I):
            from urllib.parse import urljoin
            links.append(f"{t[:40]} -> {urljoin(r.url, a['href'])}")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
    return _j({"url": r.url, "status": r.status_code, "title": soup.title.get_text(strip=True) if soup.title else "",
               "relevant_links": links[:40], "text": text[:max_chars]})


def search_web(query, max_results=8):
    """Plain web search (DuckDuckGo HTML) for providers without a built-in search tool."""
    from urllib.parse import parse_qs, unquote, urlparse
    r = requests.post("https://html.duckduckgo.com/html/", data={"q": query, "kl": "jp-jp"}, timeout=25,
                      headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126"})
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for res in soup.select(".result")[:max_results]:
        a = res.select_one("a.result__a")
        if not a:
            continue
        href = a.get("href", "")
        if "uddg=" in href:
            href = unquote(parse_qs(urlparse(href).query).get("uddg", [href])[0])
        snip = res.select_one(".result__snippet")
        out.append({"title": a.get_text(" ", strip=True), "url": href,
                    "snippet": snip.get_text(" ", strip=True) if snip else ""})
    return _j(out)


def save_document(kind, title, content, filename, company_id=None, lang="ja", status="draft", missing=None):
    folder = "common"
    if company_id:
        c = store.row("SELECT name FROM companies WHERE id=?", (company_id,))
        folder = re.sub(r"[^\w\-]+", "_", c["name"]).strip("_")[:40] if c else "common"
    path = HOME / "outbox" / folder / Path(filename).name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    store.archive_document(path, kind, company_id, title, lang, status, missing, content)
    return f"saved {path.relative_to(HOME).as_posix()}"


def list_documents(company_id=None):
    docs = store.documents(company_id)
    finals = [p.relative_to(HOME).as_posix() for p in FINAL.glob("*.pdf")] if FINAL.exists() else []
    return _j({"documents": docs[:80], "ready_pdfs": finals})


def read_document(path, max_chars=15000):
    p = _p(path)
    if p.suffix.lower() == ".docx":
        sys.path.insert(0, str(ROOT))
        from build_profile import extract_text
        return extract_text(p)[:max_chars]
    if p.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join(pg.extract_text() or "" for pg in PdfReader(str(p)).pages)[:max_chars]
    return p.read_text(encoding="utf-8", errors="replace")[:max_chars]


def _to_pdf(docx: Path, pdf: Path):
    ps = (f"$w=New-Object -ComObject Word.Application;$w.Visible=$false;"
          f"$d=$w.Documents.Open('{docx}',$false,$true);$d.SaveAs2('{pdf}',17);$d.Close($false);$w.Quit()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, capture_output=True, timeout=180)


def build_resume(variant="all", date=None):
    """Regenerate CV files with the recipes in owner.json ("resume_builds") and export PDFs."""
    builds = store.owner().get("resume_builds") or {}
    if not builds:
        return "no resume_builds configured in owner.json"
    now = datetime.now()
    date_ja = date or f"{now.year}年{now.month}月{now.day}日"
    done = []
    for name, b in builds.items():
        if variant not in ("all", name):
            continue
        args = [a.replace("{date_ja}", date_ja) for a in b.get("args", [])]
        subprocess.run([sys.executable, str(HOME / b["script"]), *args], check=True, cwd=HOME, capture_output=True)
        pdf = HOME / b["pdf"]
        pdf.parent.mkdir(parents=True, exist_ok=True)
        _to_pdf(HOME / b["docx"], pdf)
        done.append(b["pdf"])
    return _j({"generated": done})


def queue_email(to, subject, body, company_id=None, cc=None, attachments=None, account=None, in_reply_to=None,
                purpose=""):
    p = {"account": account or mailer.default_account(), "to": to, "cc": cc or [], "subject": subject,
         "body": body, "attachments": attachments or [], "in_reply_to": in_reply_to, "purpose": purpose}
    problems = mailer.check_email(p)
    if problems:
        return "NOT queued - fix first: " + "; ".join(problems)
    aid = store.add_action("email", subject, p, company_id)
    return f"email queued for approval as action #{aid}. It is NOT sent until the user approves it in the GUI."


def list_actions(status="pending"):
    acts = store.actions(None if status == "all" else status)
    for a in acts:
        p = a["payload"]
        a["payload"] = {k: (v[:300] if isinstance(v, str) else v) for k, v in p.items()}
    return _j(acts[:50])


def check_inbox(days=7, account=None):
    try:
        n = mailer.fetch(account, days)
    except Exception as e:  # noqa: BLE001
        return f"fetch failed: {e}"
    new = store.rows("""SELECT i.id,i.account,i.from_addr,i.from_name,i.subject,i.date,i.company_id,c.name company,
                        substr(i.body,1,300) preview FROM inbox i LEFT JOIN companies c ON c.id=i.company_id
                        WHERE i.status='new' ORDER BY i.date DESC LIMIT 40""")
    return _j({"fetched_new": n, "unread": new})


def read_mail(mail_id, mark_read=True):
    m = store.row("SELECT * FROM inbox WHERE id=?", (mail_id,))
    if not m:
        return "not found"
    if mark_read and m["status"] == "new":
        store.execute("UPDATE inbox SET status='read' WHERE id=?", (mail_id,))
    return _j(m)


def link_mail(mail_id, company_id, status="handled"):
    store.execute("UPDATE inbox SET company_id=?, status=? WHERE id=?", (company_id, status, mail_id))
    return "ok"


# ---- browser
def _short(snap, only_form=False):
    if isinstance(snap, dict) and "fields" in snap:
        snap = dict(snap)
        snap["text"] = snap.get("text", "")[:1500 if only_form else 3000]
    return _j(snap)


def browser_open(url):
    return _short(browser.open(url))


def browser_read():
    return _short(browser.snapshot())


def browser_fill(field_id, value):
    return _j(browser.fill(field_id, value))


def browser_select(field_id, option):
    return _j(browser.select(field_id, option))


def browser_check(field_id, checked=True):
    return _j(browser.check(field_id, checked))


def browser_upload(field_id, files):
    return _j(browser.upload(field_id, files))


def browser_click(field_id, company_id=None, summary=""):
    snap = browser.snapshot()
    field = next((f for f in snap["fields"] if f["id"] == field_id), None)
    if not field:
        return "field not found - call browser_read again (ids change after navigation)"
    if browser.looks_like_submit(field):
        aid = store.add_action("form_submit", f"提交表单: {snap['title'][:60]}",
                               {"url": snap["url"], "title": snap["title"], "field_id": field_id,
                                "button": field.get("text") or field.get("label"), "summary": summary,
                                "captcha": snap.get("captcha")}, company_id)
        return (f"This button submits/advances an application, so it was queued for approval as action #{aid}. "
                f"The user will review the filled page and approve. {'A CAPTCHA is on the page - the user must solve it.' if snap.get('captcha') else ''}")
    return _short(browser.click(field_id))


# ---------------------------------------------------------------- schemas
def S(props, required=()):
    return {"type": "object", "properties": props, "required": list(required)}


STR, INT, BOOL = {"type": "string"}, {"type": "integer"}, {"type": "boolean"}
STRS = {"type": "array", "items": {"type": "string"}}

TOOLS = [
    ("search_companies", "Search the local startup database (Japanese class-A startups with contact info). "
     "type: '1' chemistry/materials, '2' IT, '1,2' both. applied=false → not yet contacted. Results ordered by fit score.",
     S({"query": STR, "type": {"type": "string", "enum": ["1", "2", "1,2", "other"]}, "category": STR,
        "applied": BOOL, "min_score": INT, "prefecture": STR, "limit": INT, "offset": INT}), search_companies),
    ("get_company", "Full record of one company: scraped site text, careers page, contacts, score, pipeline history, "
     "documents, mails, queued actions.", S({"company_id": INT, "full": BOOL}, ["company_id"]), get_company),
    ("add_company", "Add a company that is not in the database yet (and scrape its website).",
     S({"name": STR, "website": STR, "types": STR, "prefecture": STR, "note": STR}, ["name", "website"]), add_company),
    ("enrich_company", "Re-scrape a company's website (description, careers page, emails, contact form).",
     S({"company_id": INT}, ["company_id"]), enrich_company),
    ("score_company", "Store a 0-100 fit score with roles/reasons/concerns (English, cite facts).",
     S({"company_id": INT, "score": INT, "roles": STRS, "reasons": STRS, "concerns": STRS},
       ["company_id", "score"]), score_company),
    ("update_stage", "Record pipeline progress: shortlisted / drafted / sent / replied / interview / offer / rejected / closed.",
     S({"company_id": INT, "stage": {"type": "string", "enum": store.STAGES}, "note": STR},
       ["company_id", "stage"]), update_stage),
    ("get_pipeline", "Latest stage per company, with follow-up-due flags (sent ≥7 days ago).", S({}), get_pipeline),
    ("get_profile", "The candidate's profile (profile.md, Chinese) - the only source of facts about the candidate.",
     S({}), get_profile),
    ("edit_profile", "Edit profile.md by replacing an exact text fragment (use to record new facts the user gives).",
     S({"old_text": STR, "new_text": STR}, ["old_text", "new_text"]), edit_profile),
    ("list_questions", "Open questions waiting for the user's answer.",
     S({"status": {"type": "string", "enum": ["open", "answered", "all"]}}), list_questions),
    ("ask_user", "Add a question to the user's to-do list when a needed fact is missing (never invent facts).",
     S({"question": STR, "topic": STR, "needed_for": STR, "priority": {"type": "string", "enum": ["high", "normal"]}},
       ["question"]), ask_user),
    ("record_answer", "Mark a to-do question as answered.", S({"question_id": INT, "answer": STR},
                                                             ["question_id", "answer"]), record_answer),
    ("fetch_url", "Fetch a web page as text plus application-related links (careers pages, ATS boards, job posts).",
     S({"url": STR, "max_chars": INT}, ["url"]), fetch_url),
    ("save_document", "Save an application document (cover letter, form message, research note, interview prep) "
     "as a file under outbox/ and register it.",
     S({"kind": STR, "title": STR, "content": STR, "filename": STR, "company_id": INT, "lang": STR,
        "status": STR, "missing": STRS}, ["kind", "title", "content", "filename"]), save_document),
    ("list_documents", "Registered documents and the ready-to-send PDFs (CVs).", S({"company_id": INT}),
     list_documents),
    ("read_document", "Read a document file (md/txt/docx/pdf) inside the project.", S({"path": STR}, ["path"]),
     read_document),
    ("build_resume", "Regenerate the CV PDFs from the profile scripts. variant: 'all' or a recipe name from owner.json resume_builds.",
     S({"variant": STR, "date": STR}), build_resume),
    ("queue_email", "Prepare an email (application, inquiry, reply, follow-up). It goes to the approval queue; "
     "the user approves before it is sent. attachments are project-relative paths (e.g. the PDFs in "
     "outbox/common/final). account: a mail account id from the settings (default if omitted). Use in_reply_to (Message-ID) when replying.",
     S({"to": STRS, "subject": STR, "body": STR, "company_id": INT, "cc": STRS, "attachments": STRS,
        "account": STR, "in_reply_to": STR, "purpose": STR}, ["to", "subject", "body"]), queue_email),
    ("list_actions", "The approval queue: emails / form submissions waiting for the user (status: pending / done / "
     "rejected / failed / all), with results of executed ones.",
     S({"status": {"type": "string", "enum": ["pending", "done", "rejected", "failed", "all"]}}), list_actions),
    ("check_inbox", "Fetch new job-related mail (IMAP) and list unread messages matched to companies.",
     S({"days": INT, "account": STR}), check_inbox),
    ("read_mail", "Read one fetched mail in full.", S({"mail_id": INT}, ["mail_id"]), read_mail),
    ("link_mail", "Attach a mail to a company and mark it handled.",
     S({"mail_id": INT, "company_id": INT, "status": STR}, ["mail_id", "company_id"]), link_mail),
    ("browser_open", "Open a URL in the visible Chrome window used for web application forms. Returns form fields "
     "with ids (a0, a1, ...), labels, options and whether a CAPTCHA is present.", S({"url": STR}, ["url"]),
     browser_open),
    ("browser_read", "Re-read the current page's fields (ids change after navigation).", S({}), browser_read),
    ("browser_fill", "Type a value into a text field / textarea.", S({"field_id": STR, "value": STR},
                                                                     ["field_id", "value"]), browser_fill),
    ("browser_select", "Choose an option of a <select> by its visible text.",
     S({"field_id": STR, "option": STR}, ["field_id", "option"]), browser_select),
    ("browser_check", "Tick (or untick) a checkbox / radio.", S({"field_id": STR, "checked": BOOL}, ["field_id"]),
     browser_check),
    ("browser_upload", "Attach files (project-relative paths) to a file input.",
     S({"field_id": STR, "files": STRS}, ["field_id", "files"]), browser_upload),
    ("browser_click", "Click a button or link. Buttons that submit or advance an application are NOT clicked; they "
     "are queued for the user's approval.", S({"field_id": STR, "company_id": INT, "summary": STR}, ["field_id"]),
     browser_click),
]

TOOL_SCHEMAS = [{"name": n, "description": d, "input_schema": s} for n, d, s, _ in TOOLS]
TOOL_FUNCS = {n: f for n, _, _, f in TOOLS}
# extra tool for providers that have no server-side web search (OpenAI-compatible / open models)
SEARCH_TOOL = {"name": "search_web", "description": "Search the web (titles, URLs, snippets). Follow up with fetch_url.",
               "input_schema": S({"query": STR, "max_results": INT}, ["query"])}
TOOL_FUNCS["search_web"] = search_web
SERVER_TOOLS = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 8}]


def run_tool(name, args):
    fn = TOOL_FUNCS.get(name)
    if not fn:
        return f"unknown tool {name}", True
    try:
        out = fn(**(args or {}))
        return (out if isinstance(out, str) else _j(out)), False
    except Exception as e:  # noqa: BLE001 - returned to the model as a tool error
        return f"{type(e).__name__}: {e}", True
