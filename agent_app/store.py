"""Database access shared by the agent tools and the HTTP API.

Re-uses the existing schema in db.py and adds the tables the agent app needs:
actions (approval queue), inbox (fetched mail), chats (conversation history), settings.
"""
import json
import re
import sqlite3
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db import connect as _connect  # noqa: E402
from config import HOME, owner  # noqa: E402,F401

STAGES = ["shortlisted", "drafted", "sent", "replied", "interview", "offer", "rejected", "closed"]
STAGE_LABEL = {"shortlisted": "候选", "drafted": "准备中", "sent": "已投递", "replied": "已回复",
               "interview": "面试", "offer": "Offer", "rejected": "未通过", "closed": "结束"}

EXTRA_SCHEMA = """
CREATE TABLE IF NOT EXISTS actions (            -- outward actions waiting for the user's approval
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT,          -- email / form_submit
    company_id  INTEGER,
    title       TEXT,
    payload     TEXT,          -- JSON (email: account,to,cc,subject,body,attachments,reply_to_uid)
    status      TEXT DEFAULT 'pending',   -- pending / approved / done / rejected / failed
    result      TEXT,
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    decided_at  TEXT
);
CREATE TABLE IF NOT EXISTS inbox (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    account     TEXT,
    uid         TEXT,
    message_id  TEXT,
    from_addr   TEXT,
    from_name   TEXT,
    subject     TEXT,
    date        TEXT,
    body        TEXT,
    company_id  INTEGER,
    status      TEXT DEFAULT 'new',     -- new / read / handled
    UNIQUE(account, uid)
);
CREATE TABLE IF NOT EXISTS chats (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT,
    messages    TEXT,          -- JSON list in Anthropic API format
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    updated_at  TEXT
);
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""

_local = threading.local()


CHAT_EXTRA_COLUMNS = {"provider": "TEXT", "events": "TEXT", "session_id": "TEXT", "oa_messages": "TEXT"}


def db() -> sqlite3.Connection:
    """One connection per thread (FastAPI runs sync handlers in a thread pool)."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = _connect()
        conn.executescript(EXTRA_SCHEMA)
        have = {r["name"] for r in conn.execute("PRAGMA table_info(chats)")}
        for col, typ in CHAT_EXTRA_COLUMNS.items():
            if col not in have:
                conn.execute(f"ALTER TABLE chats ADD COLUMN {col} {typ}")
        conn.commit()
        _local.conn = conn
    return conn


def rows(sql, args=()):
    return [dict(r) for r in db().execute(sql, args).fetchall()]


def row(sql, args=()):
    r = db().execute(sql, args).fetchone()
    return dict(r) if r else None


def execute(sql, args=()):
    cur = db().execute(sql, args)
    db().commit()
    return cur.lastrowid


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------- settings
def get_setting(key, default=None):
    r = row("SELECT value FROM settings WHERE key=?", (key,))
    return json.loads(r["value"]) if r else default


def set_setting(key, value):
    execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value, ensure_ascii=False)))


# ---------------------------------------------------------------- companies
LATEST_STAGE = """(SELECT stage FROM outreach o WHERE o.company_id=c.id ORDER BY o.id DESC LIMIT 1)"""


def search_companies(q="", type_=None, category="A", stage=None, applied=None, min_score=None,
                     prefecture=None, limit=50, offset=0, order="score"):
    where, args = ["1=1"], []
    if category:
        where.append("c.category=?"); args.append(category)
    if category == "A":
        where.append("c.tier IS NULL")
    if type_:
        where.append("c.types=?"); args.append(type_)
    if prefecture:
        where.append("c.prefecture LIKE ?"); args.append(f"%{prefecture}%")
    if min_score is not None:
        where.append("m.score>=?"); args.append(min_score)
    if stage:
        where.append(f"{LATEST_STAGE}=?"); args.append(stage)
    if applied is True:
        where.append(f"{LATEST_STAGE} IS NOT NULL")
    elif applied is False:
        where.append(f"{LATEST_STAGE} IS NULL")
    for w in [w for w in re.split(r"\s+", q or "") if w]:
        where.append("(c.name LIKE ? OR c.name_ja LIKE ? OR c.description LIKE ? OR c.tech_field LIKE ? "
                     "OR c.homepage_text LIKE ? OR c.careers_text LIKE ?)")
        args += [f"%{w}%"] * 6
    orders = {"score": "m.score IS NULL, m.score DESC, c.id", "name": "c.name", "recent": "c.id DESC"}
    sql = (f"SELECT c.id,c.name,c.name_ja,c.website,c.prefecture,c.types,c.category,c.tier,c.careers_url,"
           f"c.contact_emails,c.contact_form_url,c.tech_field,substr(c.description,1,200) AS description,"
           f"m.score,m.fit_roles,{LATEST_STAGE} AS stage "
           f"FROM companies c LEFT JOIN matches m ON m.company_id=c.id WHERE {' AND '.join(where)} "
           f"ORDER BY {orders.get(order, orders['score'])} LIMIT ? OFFSET ?")
    total = row(f"SELECT count(*) n FROM companies c LEFT JOIN matches m ON m.company_id=c.id "
                f"WHERE {' AND '.join(where)}", args)["n"]
    return {"total": total, "items": rows(sql, args + [limit, offset])}


def company(cid, full=False):
    c = row("SELECT * FROM companies WHERE id=?", (cid,))
    if not c:
        return None
    if not full:
        for k in ("homepage_text", "careers_text"):
            c[k] = (c[k] or "")[:1500]
    c["match"] = row("SELECT * FROM matches WHERE company_id=?", (cid,))
    c["history"] = rows("SELECT * FROM outreach WHERE company_id=? ORDER BY id", (cid,))
    c["documents"] = rows("SELECT id,kind,title,path,lang,status,updated_at FROM documents WHERE company_id=?", (cid,))
    c["mails"] = rows("SELECT id,account,from_addr,subject,date,status FROM inbox WHERE company_id=? ORDER BY date DESC",
                      (cid,))
    c["actions"] = rows("SELECT id,kind,title,status,created_at FROM actions WHERE company_id=? ORDER BY id DESC", (cid,))
    return c


def set_score(cid, score, roles=None, reasons=None, concerns=None):
    execute("INSERT INTO matches(company_id,score,fit_roles,reasons,concerns,scored_at) VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(company_id) DO UPDATE SET score=excluded.score,fit_roles=excluded.fit_roles,"
            "reasons=excluded.reasons,concerns=excluded.concerns,scored_at=excluded.scored_at",
            (cid, score, json.dumps(roles or [], ensure_ascii=False), json.dumps(reasons or [], ensure_ascii=False),
             json.dumps(concerns or [], ensure_ascii=False), now()))


def set_stage(cid, stage, note="", draft_path=None):
    if stage not in STAGES:
        raise ValueError(f"stage must be one of {STAGES}")
    return execute("INSERT INTO outreach(company_id,stage,note,draft_path) VALUES(?,?,?,?)",
                   (cid, stage, note, draft_path))


def pipeline():
    items = rows(f"""SELECT c.id, c.name, c.types, c.prefecture, m.score, o.stage, o.note, o.created_at
        FROM outreach o JOIN companies c ON c.id=o.company_id LEFT JOIN matches m ON m.company_id=c.id
        WHERE o.id IN (SELECT max(id) FROM outreach GROUP BY company_id) ORDER BY o.created_at DESC""")
    first_sent = {r["company_id"]: r["t"] for r in rows(
        "SELECT company_id, min(created_at) t FROM outreach WHERE stage='sent' GROUP BY company_id")}
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    for it in items:
        it["sent_at"] = first_sent.get(it["id"])
        it["followup_due"] = it["stage"] == "sent" and bool(it["sent_at"]) and it["sent_at"] < cutoff
    return items


def stats():
    p = pipeline()
    by = {s: 0 for s in STAGES}
    for it in p:
        by[it["stage"]] = by.get(it["stage"], 0) + 1
    return {
        "companies": row("SELECT count(*) n FROM companies WHERE category='A' AND tier IS NULL")["n"],
        "by_type": {r["types"] or "-": r["n"] for r in rows(
            "SELECT types, count(*) n FROM companies WHERE category='A' AND tier IS NULL GROUP BY types")},
        "pipeline": by,
        "followups_due": [it for it in p if it["followup_due"]],
        "pending_actions": row("SELECT count(*) n FROM actions WHERE status='pending'")["n"],
        "new_mail": row("SELECT count(*) n FROM inbox WHERE status='new'")["n"],
        "open_questions": row("SELECT count(*) n FROM open_items WHERE status='open'")["n"],
    }


# ---------------------------------------------------------------- profile / questions / documents
def profile():
    from config import PROFILE_MD
    s = row("SELECT json, updated_at FROM profile_summary WHERE id=1")
    return {"markdown": PROFILE_MD.read_text(encoding="utf-8") if PROFILE_MD.exists() else "",
            "structured": json.loads(s["json"]) if s and s["json"] else None,
            "path": str(PROFILE_MD)}


def save_profile_md(text):
    from config import PROFILE_MD
    PROFILE_MD.write_text(text, encoding="utf-8")


def questions(status="open"):
    if status == "all":
        return rows("SELECT * FROM open_items ORDER BY status='open' DESC, priority='high' DESC, id")
    return rows("SELECT * FROM open_items WHERE status=? ORDER BY priority='high' DESC, id", (status,))


def ask(question, topic="", needed_for="", priority="normal"):
    return execute("INSERT INTO open_items(topic,question,needed_for,priority) VALUES(?,?,?,?)",
                   (topic, question, needed_for, priority))


def answer(item_id, text, drop=False):
    execute("UPDATE open_items SET status=?, answer=?, answered_at=? WHERE id=?",
            ("dropped" if drop else "answered", text, now(), item_id))


def documents(company_id=None):
    if company_id:
        return rows("SELECT id,company_id,kind,title,path,lang,status,missing,updated_at,created_at FROM documents "
                    "WHERE company_id=? ORDER BY id DESC", (company_id,))
    return rows("""SELECT d.id,d.company_id,c.name company,d.kind,d.title,d.path,d.lang,d.status,d.missing,
                   d.updated_at,d.created_at FROM documents d LEFT JOIN companies c ON c.id=d.company_id
                   ORDER BY d.id DESC""")


def archive_document(path, kind, company_id=None, title="", lang="ja", status="draft", missing=None, text=""):
    execute("""INSERT INTO documents(company_id,kind,title,path,lang,status,missing,text,updated_at)
               VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET company_id=excluded.company_id,
               kind=excluded.kind,title=excluded.title,lang=excluded.lang,status=excluded.status,
               missing=excluded.missing,text=excluded.text,updated_at=excluded.updated_at""",
            (company_id, kind, title, str(path), lang, status, json.dumps(missing or [], ensure_ascii=False),
             text, now()))


# ---------------------------------------------------------------- actions (approval queue)
def add_action(kind, title, payload, company_id=None):
    return execute("INSERT INTO actions(kind,company_id,title,payload) VALUES(?,?,?,?)",
                   (kind, company_id, title, json.dumps(payload, ensure_ascii=False)))


def actions(status=None):
    sql = "SELECT a.*, c.name company FROM actions a LEFT JOIN companies c ON c.id=a.company_id"
    if status:
        r = rows(sql + " WHERE a.status=? ORDER BY a.id DESC", (status,))
    else:
        r = rows(sql + " ORDER BY a.id DESC LIMIT 200")
    for a in r:
        a["payload"] = json.loads(a["payload"] or "{}")
    return r


def update_action(aid, status, result=None, payload=None):
    if payload is not None:
        execute("UPDATE actions SET payload=? WHERE id=?", (json.dumps(payload, ensure_ascii=False), aid))
    execute("UPDATE actions SET status=?, result=?, decided_at=? WHERE id=?", (status, result, now(), aid))


# ---------------------------------------------------------------- inbox
def match_company_by_email(addr):
    if not addr or "@" not in addr:
        return None
    domain = addr.split("@", 1)[1].lower()
    parts = domain.split(".")
    for i in range(len(parts) - 1):
        d = ".".join(parts[i:])
        r = row("SELECT id FROM companies WHERE domain=? OR contact_emails LIKE ? OR website LIKE ? LIMIT 1",
                (d, f"%@{d}%", f"%{d}%"))
        if r and d not in ("gmail.com", "jp", "co.jp", "com", "ne.jp", "ac.jp"):
            return r["id"]
    return None
