"""Company intelligence index (RAG) for the job-search agent.

For every company an "intel document" is assembled from everything the database knows - the latest website
visit, careers page, source description, fit score, pipeline history, mails, notes and documents - split into
chunks and indexed twice:
  * dense vectors from a local multilingual embedding model (fastembed, ONNX; ja/zh/en, no API key), and
  * an SQLite FTS5 trigram index for exact names / keywords.
search() fuses both rankings (reciprocal rank fusion).

Freshness:
  * daily (every 24 h, while the GUI runs, or `python -m agent_app.intel daily` from a scheduler): re-scrape
    every company website, then rebuild the whole index;
  * on progress: SQLite triggers mark a company dirty whenever its pipeline stage, mails, notes, documents,
    score or scraped data change (also when the change comes from jobdb.py / Claude Code). A background worker
    re-indexes it within seconds; pipeline / mail events also re-scrape its website first (at most every 6 h).
"""
import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from . import store

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MODEL_DIR = Path(os.environ.get("JOBAGENT_MODELS") or store.HOME / "data" / "models")   # shared across accounts
CHUNK_CHARS, CHUNK_OVERLAP = 320, 60
FULL_EVERY = timedelta(hours=24)
RESCRAPE_MIN_GAP = timedelta(hours=6)
SCRAPE_WORKERS = 12

SCHEMA = """
CREATE TABLE IF NOT EXISTS intel_chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id  INTEGER,
    section     TEXT,
    text        TEXT,
    vec         BLOB
);
CREATE INDEX IF NOT EXISTS idx_intel_chunks_company ON intel_chunks(company_id);
CREATE TABLE IF NOT EXISTS intel_meta (
    company_id  INTEGER PRIMARY KEY,
    doc_hash    TEXT,
    indexed_at  TEXT,
    scraped_at  TEXT
);
CREATE TABLE IF NOT EXISTS intel_dirty (
    company_id  INTEGER,
    reason      TEXT,
    created_at  TEXT DEFAULT (datetime('now','localtime'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS intel_fts USING fts5(text, chunk_id UNINDEXED, company_id UNINDEXED,
                                                        tokenize='trigram');
"""

# "progress" sources also trigger a website re-scrape; the rest only re-index
TRIGGERS = {
    "outreach": ("INSERT", "NEW.company_id", "progress"),
    "inbox": ("INSERT", "NEW.company_id", "progress"),
    "matches": ("INSERT", "NEW.company_id", "score"),
    "notes": ("INSERT", "NEW.company_id", "note"),
    "documents": ("INSERT", "NEW.company_id", "document"),
}
UPDATE_TRIGGERS = {
    "inbox": ("company_id", "NEW.company_id", "progress"),
    "matches": ("score, reasons, concerns", "NEW.company_id", "score"),
    "notes": ("body, title, company_id", "NEW.company_id", "note"),
    "documents": ("text, company_id", "NEW.company_id", "document"),
    "companies": ("description, site_description, homepage_text, careers_text, title, website", "NEW.id", "scraped"),
}

_init_lock = threading.Lock()
_model_lock = threading.Lock()
_embed_lock = threading.Lock()
_model = None
_inited = False
_cache = {"version": None, "ids": None, "cids": None, "mat": None}
STATUS = {"running": None, "last_error": None}


# ---------------------------------------------------------------- setup
def init():
    global _inited
    with _init_lock:
        if _inited:
            return
        db = store.db()
        db.executescript(SCHEMA)
        for table, (event, cid, reason) in TRIGGERS.items():
            db.execute(f"""CREATE TRIGGER IF NOT EXISTS intel_{table}_ins AFTER {event} ON {table}
                           WHEN {cid} IS NOT NULL BEGIN
                           INSERT INTO intel_dirty(company_id, reason) VALUES({cid}, '{reason}'); END""")
        for table, (cols, cid, reason) in UPDATE_TRIGGERS.items():
            db.execute(f"""CREATE TRIGGER IF NOT EXISTS intel_{table}_upd AFTER UPDATE OF {cols} ON {table}
                           WHEN {cid} IS NOT NULL BEGIN
                           INSERT INTO intel_dirty(company_id, reason) VALUES({cid}, '{reason}'); END""")
        db.commit()
        _inited = True


def model():
    global _model
    with _model_lock:
        if _model is None:
            import os
            os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
            from fastembed import TextEmbedding
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            _model = TextEmbedding(MODEL_NAME, cache_dir=str(MODEL_DIR))
        return _model


def embed(texts):
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    m = model()
    with _embed_lock:
        v = np.array(list(m.embed(texts, batch_size=64)), dtype=np.float32)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


# ---------------------------------------------------------------- intel document
def _clip(s, n):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s[:n]


def build_doc(cid):
    """[(section, text)] for one company - everything worth retrieving."""
    c = store.row("SELECT * FROM companies WHERE id=?", (cid,))
    if not c:
        return []
    secs = []
    head = " / ".join(x for x in (c["name"], c["name_ja"] if c["name_ja"] != c["name"] else None) if x)
    facts = [f"{k}: {c[k]}" for k in ("prefecture", "address", "tech_field", "sector", "types", "university",
                                      "founded", "website", "careers_url", "contact_emails", "contact_form_url")
             if c.get(k)]
    secs.append(("profile", f"{head}. " + "; ".join(facts)))
    site = " ".join(filter(None, [c.get("title"), c.get("site_description")]))
    if site or c.get("homepage_text"):
        secs.append(("website", _clip(site + " " + (c.get("homepage_text") or ""), 5000)))
    if c.get("description"):
        secs.append(("source_description", _clip(c["description"], 2500)))
    if c.get("careers_text") and not str(c["careers_text"]).startswith("[fetch failed"):
        secs.append(("careers", _clip(c["careers_text"], 5000)))
    m = store.row("SELECT * FROM matches WHERE company_id=?", (cid,))
    if m:
        secs.append(("fit", _clip(f"fit score {m['score']}. roles: {m['fit_roles']}. reasons: {m['reasons']}. "
                                  f"concerns: {m['concerns']}", 2500)))
    hist = store.rows("SELECT stage, note, created_at FROM outreach WHERE company_id=? ORDER BY id", (cid,))
    if hist:
        secs.append(("pipeline", _clip(" | ".join(f"{h['created_at'][:10]} {h['stage']}: {h['note'] or ''}"
                                                  for h in hist), 4000)))
    for mail in store.rows("SELECT subject, date, from_name, body FROM inbox WHERE company_id=? ORDER BY date DESC "
                           "LIMIT 8", (cid,)):
        secs.append(("mail", _clip(f"{mail['date']} {mail['from_name'] or ''}: {mail['subject']} — {mail['body']}",
                                   1500)))
    for n in store.rows("SELECT kind, title, body, status FROM notes WHERE company_id=?", (cid,)):
        secs.append((f"note_{n['kind']}", _clip(f"{n['title']} ({n['status']}): {n['body']}", 3000)))
    for d in store.rows("SELECT kind, title, text FROM documents WHERE company_id=? AND text IS NOT NULL", (cid,)):
        secs.append((f"doc_{d['kind']}", _clip(f"{d['title']}: {d['text']}", 3000)))
    return [(s, t) for s, t in secs if t]


def chunk(name, section, text):
    out, i = [], 0
    while i < len(text):
        piece = text[i:i + CHUNK_CHARS]
        out.append(f"[{name} | {section}] {piece}")
        if i + CHUNK_CHARS >= len(text):
            break
        i += CHUNK_CHARS - CHUNK_OVERLAP
    return out


def index_company(cid, force=False):
    """(Re)index one company. Returns the number of chunks (0 if unchanged and not forced)."""
    init()
    doc = build_doc(cid)
    name = (store.row("SELECT name FROM companies WHERE id=?", (cid,)) or {}).get("name", str(cid))
    h = hashlib.sha1(json.dumps(doc, ensure_ascii=False).encode()).hexdigest()
    meta = store.row("SELECT doc_hash FROM intel_meta WHERE company_id=?", (cid,))
    if meta and meta["doc_hash"] == h and not force:
        return 0
    texts = [t for s, body in doc for t in chunk(name, s, body)]
    sections = [s for s, body in doc for _ in chunk(name, s, body)]
    vecs = embed(texts)
    db = store.db()
    old = [r["id"] for r in store.rows("SELECT id FROM intel_chunks WHERE company_id=?", (cid,))]
    if old:
        db.execute(f"DELETE FROM intel_fts WHERE chunk_id IN ({','.join('?' * len(old))})", old)
    db.execute("DELETE FROM intel_chunks WHERE company_id=?", (cid,))
    for sec, t, v in zip(sections, texts, vecs):
        cur = db.execute("INSERT INTO intel_chunks(company_id, section, text, vec) VALUES(?,?,?,?)",
                         (cid, sec, t, v.astype(np.float32).tobytes()))
        db.execute("INSERT INTO intel_fts(text, chunk_id, company_id) VALUES(?,?,?)", (t, cur.lastrowid, cid))
    db.execute("INSERT INTO intel_meta(company_id, doc_hash, indexed_at) VALUES(?,?,?) ON CONFLICT(company_id) "
               "DO UPDATE SET doc_hash=excluded.doc_hash, indexed_at=excluded.indexed_at", (cid, h, store.now()))
    db.commit()
    _cache["version"] = None
    return len(texts)


def rebuild_all(progress=None):
    init()
    ids = [r["id"] for r in store.rows("SELECT id FROM companies ORDER BY id")]
    n = 0
    for i, cid in enumerate(ids):
        n += index_company(cid)
        if progress and i % 100 == 0:
            progress(f"indexed {i}/{len(ids)}")
    store.db().execute("DELETE FROM intel_dirty WHERE reason!='progress'")
    store.db().commit()
    return {"companies": len(ids), "chunks_written": n}


# ---------------------------------------------------------------- scraping
def scrape(ids):
    """Re-visit company websites (same logic as scrapers/enrich.py) and update the companies table."""
    sys.path.insert(0, str(store.ROOT / "scrapers"))
    from concurrent.futures import ThreadPoolExecutor
    from enrich import enrich_one
    rows = store.rows(f"SELECT id, website, description, contact_emails, phone FROM companies WHERE id IN "
                      f"({','.join('?' * len(ids))})", ids) if ids else []
    cols = ["title", "site_description", "homepage_text", "careers_url", "careers_text", "contact_emails",
            "contact_form_url", "phone", "enriched_at", "enrich_error"]
    with ThreadPoolExecutor(SCRAPE_WORKERS) as pool:
        results = list(pool.map(enrich_one, rows))
    old = {r["id"]: r for r in rows}
    db = store.db()
    for res in results:
        o = old[res["id"]]
        if res.get("enrich_error"):                # keep what we had when the site is down
            db.execute("UPDATE companies SET enrich_error=? WHERE id=?", (res["enrich_error"], res["id"]))
            continue
        if o["phone"]:
            res.pop("phone", None)
        merged = set(filter(None, (o["contact_emails"] or "").split(","))) | \
            set(filter(None, (res.get("contact_emails") or "").split(",")))
        res["contact_emails"] = ",".join(sorted(merged)[:10]) or None
        use = [k for k in cols if k in res]
        db.execute(f"UPDATE companies SET {', '.join(k + '=?' for k in use)} WHERE id=?",
                   [res[k] for k in use] + [res["id"]])
        db.execute("INSERT INTO intel_meta(company_id, scraped_at) VALUES(?,?) ON CONFLICT(company_id) "
                   "DO UPDATE SET scraped_at=excluded.scraped_at", (res["id"], store.now()))
    db.commit()
    return sum(1 for r in results if not r.get("enrich_error"))


def daily_update(progress=print):
    """Full refresh: re-scrape every company website, then rebuild the whole index."""
    init()
    STATUS["running"] = "daily"
    try:
        ids = [r["id"] for r in store.rows("SELECT id FROM companies WHERE website IS NOT NULL")]
        progress(f"scraping {len(ids)} websites …")
        ok = 0
        for i in range(0, len(ids), 200):
            ok += scrape(ids[i:i + 200])
            progress(f"scraped {min(i + 200, len(ids))}/{len(ids)}")
        r = rebuild_all(progress)
        store.set_setting("intel_last_full", store.now())
        store.set_setting("intel_last_full_result", {"scraped_ok": ok, **r})
        return {"scraped_ok": ok, **r}
    finally:
        STATUS["running"] = None


def process_dirty():
    """Handle companies marked by the triggers. Returns the ids processed."""
    init()
    top = store.row("SELECT max(rowid) m FROM intel_dirty")["m"]
    if not top:
        return []
    rows = store.rows("SELECT company_id, group_concat(reason) reasons FROM intel_dirty WHERE rowid<=? "
                      "GROUP BY company_id", (top,))
    store.execute("DELETE FROM intel_dirty WHERE rowid<=?", (top,))
    done = []
    for r in rows:
        cid = r["company_id"]
        if "progress" in (r["reasons"] or ""):
            meta = store.row("SELECT scraped_at FROM intel_meta WHERE company_id=?", (cid,))
            last = meta and meta["scraped_at"]
            if not last or datetime.fromisoformat(last) < datetime.now() - RESCRAPE_MIN_GAP:
                scrape([cid])
                store.execute("DELETE FROM intel_dirty WHERE company_id=? AND reason='scraped'", (cid,))
        index_company(cid)
        done.append(cid)
    return done


# ---------------------------------------------------------------- search
def _matrix():
    ver = store.row("SELECT count(*) n, max(id) m FROM intel_chunks")
    key = (ver["n"], ver["m"])
    if _cache["version"] != key:
        rows = store.rows("SELECT id, company_id, vec FROM intel_chunks")
        _cache.update(version=key, ids=np.array([r["id"] for r in rows]),
                      cids=np.array([r["company_id"] for r in rows]),
                      mat=np.vstack([np.frombuffer(r["vec"], dtype=np.float32) for r in rows]) if rows
                      else np.zeros((0, 384), dtype=np.float32))
    return _cache["ids"], _cache["cids"], _cache["mat"]


def search(query, k=8, company_id=None, contacted=None, per_company=2):
    """Hybrid semantic + keyword search. Returns hits grouped by company."""
    init()
    ids, cids, mat = _matrix()
    if not len(ids):
        return {"hits": [], "note": "index is empty - run a rebuild"}
    mask = np.ones(len(ids), bool)
    if company_id:
        mask &= cids == int(company_id)
    if contacted is not None:
        seen = {r["company_id"] for r in store.rows("SELECT DISTINCT company_id FROM outreach")}
        inset = np.isin(cids, list(seen))
        mask &= inset if contacted else ~inset
    sims = mat @ embed([query])[0]
    sims[~mask] = -1
    dense = [int(i) for i in np.argsort(-sims)[:200] if sims[i] > -1]
    rank = {int(ids[i]): r for r, i in enumerate(dense)}
    kw = []
    terms = [t for t in re.split(r"[\s,、，。/|]+", re.sub(r'["*()^:]', " ", query)) if len(t) >= 3]
    if terms:
        try:
            match = " OR ".join(f'"{t}"' for t in terms)          # trigram FTS needs ≥3 chars per term
            kw = [r["chunk_id"] for r in store.rows("SELECT chunk_id FROM intel_fts WHERE intel_fts MATCH ? "
                                                    "ORDER BY rank LIMIT 200", (match,))]
        except Exception:  # noqa: BLE001 - malformed FTS query → semantic only
            kw = []
    allowed = set(int(x) for x in ids[mask])
    score = {}
    for cid_, r in rank.items():
        score[cid_] = score.get(cid_, 0) + 1 / (60 + r)
    for r, chunk_id in enumerate(c for c in kw if c in allowed):
        score[chunk_id] = score.get(chunk_id, 0) + 1 / (60 + r)
    order = sorted(score, key=score.get, reverse=True)
    rows = {r["id"]: r for r in store.rows(
        f"SELECT ch.id, ch.company_id, ch.section, ch.text, c.name FROM intel_chunks ch JOIN companies c "
        f"ON c.id=ch.company_id WHERE ch.id IN ({','.join('?' * len(order[:400]))})", order[:400])} if order else {}
    hits, per, companies = [], {}, []
    for chunk_id in order:
        r = rows.get(chunk_id)
        if not r or per.get(r["company_id"], 0) >= per_company:
            continue
        if r["company_id"] not in per:
            if len(companies) >= k:
                continue
            companies.append(r["company_id"])
        per[r["company_id"]] = per.get(r["company_id"], 0) + 1
        hits.append({"company_id": r["company_id"], "company": r["name"], "section": r["section"],
                     "text": r["text"], "score": round(score[chunk_id] * 1000, 2)})
    return {"hits": hits}


def status():
    init()
    s = store.row("SELECT count(*) chunks, count(DISTINCT company_id) companies FROM intel_chunks")
    return {**s, "dirty": store.row("SELECT count(DISTINCT company_id) n FROM intel_dirty")["n"],
            "last_full": store.get_setting("intel_last_full"), "last_full_result": store.get_setting(
                "intel_last_full_result"), "running": STATUS["running"], "last_error": STATUS["last_error"],
            "model": MODEL_NAME}


# ---------------------------------------------------------------- background worker (GUI process)
def start_worker(poll=20):
    """Daemon thread: process dirty companies every `poll` s; run the daily full update when it is due."""
    def loop():
        time.sleep(5)
        while True:
            try:
                init()
                last = store.get_setting("intel_last_full")
                if not STATUS["running"] and (not last or datetime.fromisoformat(last) < datetime.now() - FULL_EVERY):
                    daily_update(progress=lambda m: STATUS.update(progress=m))
                process_dirty()
                STATUS["last_error"] = None
            except Exception as e:  # noqa: BLE001 - keep the worker alive, show it in the GUI
                STATUS["last_error"] = f"{type(e).__name__}: {e}"
            time.sleep(poll)
    threading.Thread(target=loop, daemon=True, name="intel-worker").start()


def main():
    ap = argparse.ArgumentParser(description="Company intelligence index (RAG)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rebuild", help="re-index every company (no scraping)")
    sub.add_parser("daily", help="re-scrape all websites, then rebuild (what the 24 h job does)")
    sub.add_parser("dirty", help="process companies changed since the last run")
    sub.add_parser("status")
    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("-k", type=int, default=8)
    p.add_argument("--company", type=int)
    p.add_argument("--contacted", choices=["yes", "no"])
    p = sub.add_parser("company", help="re-scrape and re-index one company")
    p.add_argument("id", type=int)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if a.cmd == "rebuild":
        print(rebuild_all(print))
    elif a.cmd == "daily":
        print(daily_update())
    elif a.cmd == "dirty":
        print(process_dirty())
    elif a.cmd == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=1))
    elif a.cmd == "company":
        scrape([a.id])
        print(index_company(a.id, force=True), "chunks")
    else:
        c = None if not a.contacted else a.contacted == "yes"
        for h in search(a.query, a.k, a.company, c)["hits"]:
            print(f"#{h['company_id']} {h['company']} [{h['section']}] {h['score']}\n   {h['text'][:200]}")


if __name__ == "__main__":
    main()
