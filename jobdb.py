"""Command-line access to the job-search database (no LLM calls).

Claude Code (via the japan-job-search skill) uses this to read companies and the
profile, record its own fit evaluations, save outreach drafts and track the pipeline.

    python jobdb.py profile                         # structured profile + source docs
    python jobdb.py ingest                          # re-read profile.md + profile/materials/*
    python jobdb.py set-profile profile.json        # store an updated structured profile
    python jobdb.py prerank [--region japan] [--limit 60] [--unscored]
    python jobdb.py search "materials informatics" [--region japan] [--sector ai] [--limit 20]
    python jobdb.py show 269 [--full]               # one company, with score & pipeline
    python jobdb.py cards 269 404 253 [--chars 1500] # compact cards for batch evaluation
    python jobdb.py set-score 269 --score 92 --roles "..." --reasons "..." --concerns "..."
    python jobdb.py set-scores scores.json           # bulk: [{id, score, roles[], reasons[], concerns[]}]
    python jobdb.py ranking [--min 60] [--limit 30]
    python jobdb.py save-draft 269 --kind cold_email --lang ja --subject "..." --body-file draft.md [--to addr]
    python jobdb.py stage 269 sent --note "..."
    python jobdb.py pipeline
    python jobdb.py export                           # data/ranking.csv
    python jobdb.py export-companies                 # data/startups_japan.csv (all, with A/B and type 1/2)
    python jobdb.py search "" --category A --type 1  # unlisted chem/materials startups
    python jobdb.py archive <path> --kind cv [--company 269] [--status needs_info] [--missing "a|b"] [--title ..] [--lang ja] [--generator ..]
    python jobdb.py docs [--company 269] [--status needs_info]
    python jobdb.py doc <doc_id>                     # full record incl. extracted text
    python jobdb.py ask "<question>" --topic ... [--for ...] [--priority high]
    python jobdb.py todo [--all]                     # open questions for the user
    python jobdb.py answer <item_id> "<answer>"      # record an answer (or: --drop)
"""
import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # Windows console

from config import DATA_DIR, OUTBOX_DIR
from db import connect
from match import heuristic_ranking

STAGES = ["shortlisted", "drafted", "sent", "replied", "interview", "offer", "rejected", "closed"]
conn = connect()


def dump(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def split_list(s):
    return [x.strip() for x in re.split(r"\s*\|\s*", s) if x.strip()] if s else []


def card(r, chars):
    home = (r["homepage_text"] or "")[:chars]
    careers = (r["careers_text"] or "")[:chars]
    return (f"### #{r['id']} {r['name']} ({r['name_ja'] or ''})\n"
            f"{r['sector']} | {r['region']} | {r['status']} | GB invested {r['invested_at']}\n"
            f"web: {r['website']} | careers: {r['careers_url'] or '-'} | emails: {r['contact_emails'] or '-'}\n"
            f"title: {r['title'] or ''}\ndesc: {r['description'] or ''}\n"
            f"home: {home}\ncareers_text: {careers}\n")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("profile")
    p = sub.add_parser("set-profile"); p.add_argument("file", help="JSON file with the structured profile")
    sub.add_parser("ingest", help="re-extract text from profile.md and profile/materials/*")
    p = sub.add_parser("prerank"); p.add_argument("--region", default="japan"); p.add_argument("--limit", type=int, default=60)
    p.add_argument("--unscored", action="store_true"); p.add_argument("--include-ma", action="store_true")
    p = sub.add_parser("search"); p.add_argument("query", nargs="?", default="")
    p.add_argument("--region"); p.add_argument("--sector"); p.add_argument("--status"); p.add_argument("--limit", type=int, default=20)
    p.add_argument("--category", choices=["A", "B"]); p.add_argument("--type", dest="ctype", help="1, 2, '1,2' or other; '1' also matches '1,2'")
    p = sub.add_parser("show"); p.add_argument("id", type=int); p.add_argument("--full", action="store_true")
    p = sub.add_parser("cards"); p.add_argument("ids", type=int, nargs="+"); p.add_argument("--chars", type=int, default=1500)
    p = sub.add_parser("set-score"); p.add_argument("id", type=int); p.add_argument("--score", type=int, required=True)
    p.add_argument("--roles", default=""); p.add_argument("--reasons", default=""); p.add_argument("--concerns", default="")
    p = sub.add_parser("set-scores"); p.add_argument("file")
    p = sub.add_parser("ranking"); p.add_argument("--min", type=int, default=0); p.add_argument("--limit", type=int, default=30)
    p = sub.add_parser("save-draft"); p.add_argument("id", type=int)
    p.add_argument("--kind", required=True, choices=["cold_email", "cover_letter", "reply", "follow_up",
                                                    "application_answers", "interview_prep", "company_research"])
    p.add_argument("--lang", required=True, choices=["en", "ja", "zh"]); p.add_argument("--subject", required=True)
    p.add_argument("--body-file", required=True); p.add_argument("--to", default="")
    p = sub.add_parser("stage"); p.add_argument("id", type=int); p.add_argument("stage", choices=STAGES); p.add_argument("--note", default="")
    sub.add_parser("pipeline")
    sub.add_parser("export")
    sub.add_parser("export-companies", help="data/startups_japan.csv with category/type/contacts")
    p = sub.add_parser("archive"); p.add_argument("path"); p.add_argument("--kind", required=True)
    p.add_argument("--company", type=int); p.add_argument("--status", default="draft"); p.add_argument("--missing", default="")
    p.add_argument("--title", default=""); p.add_argument("--lang", default=""); p.add_argument("--generator", default="")
    p = sub.add_parser("docs"); p.add_argument("--company", type=int); p.add_argument("--status")
    p = sub.add_parser("doc"); p.add_argument("id", type=int)
    p = sub.add_parser("ask"); p.add_argument("question"); p.add_argument("--topic", default="")
    p.add_argument("--for", dest="needed_for", default=""); p.add_argument("--priority", default="normal")
    p = sub.add_parser("todo"); p.add_argument("--all", action="store_true")
    p = sub.add_parser("answer"); p.add_argument("id", type=int); p.add_argument("text", nargs="?", default="")
    p.add_argument("--drop", action="store_true")
    a = ap.parse_args()

    if a.cmd == "profile":
        r = conn.execute("SELECT json, updated_at FROM profile_summary WHERE id=1").fetchone()
        docs = [dict(d) for d in conn.execute("SELECT path, kind, length(text) AS chars FROM profile_docs")]
        dump({"profile": json.loads(r["json"]) if r else None, "updated_at": r["updated_at"] if r else None,
              "documents": docs})

    elif a.cmd == "set-profile":
        data = json.loads(Path(a.file).read_text(encoding="utf-8"))
        conn.execute("INSERT OR REPLACE INTO profile_summary(id, json, updated_at) VALUES (1, ?, ?)",
                     (json.dumps(data, ensure_ascii=False, indent=2), datetime.now().isoformat(timespec="seconds")))
        conn.commit()
        print("profile saved")

    elif a.cmd == "ingest":
        from build_profile import ingest
        for d in ingest(conn):
            print(f"{d['kind']:8s} {len(d['text']):6d} chars  {d['path']}")

    elif a.cmd == "prerank":
        scored = {r[0] for r in conn.execute("SELECT company_id FROM matches")}
        n = 0
        for s, cid, name, sector in heuristic_ranking(a.region, a.include_ma):
            if a.unscored and cid in scored:
                continue
            print(f"{s:4d}  #{cid:<4d} {name}  [{sector}]{'  (scored)' if cid in scored else ''}")
            n += 1
            if n >= a.limit:
                break

    elif a.cmd == "search":
        sql = """SELECT c.id, c.name, c.name_ja, c.category, c.types, c.sector, c.tech_field, c.status, c.careers_url,
                        substr(coalesce(c.description,''),1,160) AS description, m.score
                 FROM companies c LEFT JOIN matches m ON m.company_id=c.id WHERE 1=1"""
        prm = []
        for t in a.query.split():
            sql += " AND (c.name LIKE ? OR c.name_ja LIKE ? OR c.title LIKE ? OR c.description LIKE ? OR c.homepage_text LIKE ? OR c.careers_text LIKE ?)"
            prm += [f"%{t}%"] * 6
        for col in ("region", "sector", "status", "category"):
            if getattr(a, col):
                sql += f" AND c.{col}=?"; prm.append(getattr(a, col))
        if a.ctype:
            if a.ctype in ("1", "2"):
                sql += " AND (c.types=? OR c.types='1,2')"
            else:
                sql += " AND c.types=?"
            prm.append(a.ctype)
        sql += " ORDER BY m.score DESC NULLS LAST, c.name LIMIT ?"; prm.append(a.limit)
        dump([dict(r) for r in conn.execute(sql, prm)])

    elif a.cmd == "show":
        c = conn.execute("SELECT * FROM companies WHERE id=?", (a.id,)).fetchone()
        if not c:
            sys.exit("no such company")
        c = dict(c)
        if not a.full:
            for k in ("homepage_text", "careers_text"):
                c[k] = (c[k] or "")[:2500]
        m = conn.execute("SELECT * FROM matches WHERE company_id=?", (a.id,)).fetchone()
        hist = [dict(h) for h in conn.execute("SELECT stage, note, draft_path, created_at FROM outreach WHERE company_id=? ORDER BY id", (a.id,))]
        dump({"company": c, "match": dict(m) if m else None, "pipeline": hist})

    elif a.cmd == "cards":
        rows = conn.execute(f"SELECT * FROM companies WHERE id IN ({','.join('?' * len(a.ids))})", a.ids).fetchall()
        for r in rows:
            print(card(r, a.chars))

    elif a.cmd in ("set-score", "set-scores"):
        if a.cmd == "set-score":
            items = [{"id": a.id, "score": a.score, "roles": split_list(a.roles),
                      "reasons": split_list(a.reasons), "concerns": split_list(a.concerns)}]
        else:
            items = json.loads(Path(a.file).read_text(encoding="utf-8"))
        now = datetime.now().isoformat(timespec="seconds")
        for it in items:
            conn.execute("INSERT OR REPLACE INTO matches VALUES (?,?,?,?,?,?)",
                         (it["id"], int(it["score"]), json.dumps(it.get("roles", []), ensure_ascii=False),
                          json.dumps(it.get("reasons", []), ensure_ascii=False),
                          json.dumps(it.get("concerns", []), ensure_ascii=False), now))
        conn.commit()
        print(f"saved {len(items)} score(s)")

    elif a.cmd == "ranking":
        rows = conn.execute("""SELECT c.id, c.name, c.sector, c.status, m.score, m.fit_roles, c.careers_url
                               FROM matches m JOIN companies c ON c.id=m.company_id
                               WHERE m.score >= ? ORDER BY m.score DESC LIMIT ?""", (a.min, a.limit)).fetchall()
        for r in rows:
            roles = ", ".join(json.loads(r["fit_roles"] or "[]"))[:90]
            print(f"{r['score']:3d}  #{r['id']:<4d} {r['name']:<28} [{r['sector']}]  {roles}")

    elif a.cmd == "save-draft":
        c = conn.execute("SELECT name FROM companies WHERE id=?", (a.id,)).fetchone()
        name = c["name"].strip() if c else f"company{a.id}"
        slug = re.sub(r"[^\w-]+", "_", name)[:40]
        body = Path(a.body_file).read_text(encoding="utf-8")
        path = OUTBOX_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{slug}_{a.kind}.md"
        path.write_text(f"---\ncompany: {name}\ncompany_id: {a.id}\nkind: {a.kind}\nlanguage: {a.lang}\n"
                        f"to: {a.to}\nsubject: {a.subject}\n---\n\n{body}\n", encoding="utf-8")
        conn.execute("INSERT INTO outreach(company_id, stage, note, draft_path) VALUES (?,?,?,?)",
                     (a.id, "drafted", f"{a.kind}: {a.subject}", str(path)))
        conn.commit()
        print(path)

    elif a.cmd == "stage":
        conn.execute("INSERT INTO outreach(company_id, stage, note) VALUES (?,?,?)", (a.id, a.stage, a.note))
        conn.commit()
        print("ok")

    elif a.cmd == "pipeline":
        rows = conn.execute("""SELECT c.id, c.name, o.stage, o.note, o.draft_path, o.created_at, m.score
                               FROM outreach o JOIN companies c ON c.id=o.company_id
                               LEFT JOIN matches m ON m.company_id=c.id
                               WHERE o.id IN (SELECT MAX(id) FROM outreach GROUP BY company_id)
                               ORDER BY o.created_at DESC""").fetchall()
        dump([dict(r) for r in rows])

    elif a.cmd == "archive":
        from build_profile import extract_text
        path = Path(a.path).resolve()
        text = extract_text(path) if path.suffix.lower() in {".docx", ".pdf", ".md", ".txt"} else ""
        missing = json.dumps(split_list(a.missing), ensure_ascii=False)
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute("""INSERT INTO documents(company_id, kind, title, path, lang, status, missing, text, generator, updated_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?)
                        ON CONFLICT(path) DO UPDATE SET company_id=excluded.company_id, kind=excluded.kind,
                          title=excluded.title, lang=excluded.lang, status=excluded.status, missing=excluded.missing,
                          text=excluded.text, generator=excluded.generator, updated_at=excluded.updated_at""",
                     (a.company, a.kind, a.title or path.name, str(path), a.lang, a.status, missing, text,
                      a.generator, now))
        conn.commit()
        print(f"archived {path.name} ({len(text)} chars, status={a.status})")

    elif a.cmd == "docs":
        sql = """SELECT d.id, c.name AS company, d.kind, d.title, d.status, d.missing, d.path, d.updated_at
                 FROM documents d LEFT JOIN companies c ON c.id=d.company_id WHERE 1=1"""
        prm = []
        if a.company:
            sql += " AND d.company_id=?"; prm.append(a.company)
        if a.status:
            sql += " AND d.status=?"; prm.append(a.status)
        dump([dict(r) for r in conn.execute(sql + " ORDER BY d.company_id, d.kind", prm)])

    elif a.cmd == "doc":
        r = conn.execute("SELECT * FROM documents WHERE id=?", (a.id,)).fetchone()
        dump(dict(r) if r else "no such document")

    elif a.cmd == "ask":
        conn.execute("INSERT INTO open_items(topic, question, needed_for, priority) VALUES (?,?,?,?)",
                     (a.topic, a.question, a.needed_for, a.priority))
        conn.commit()
        print("ok")

    elif a.cmd == "todo":
        sql = "SELECT * FROM open_items" + ("" if a.all else " WHERE status='open'")
        for r in conn.execute(sql + " ORDER BY priority='high' DESC, id"):
            flag = "!" if r["priority"] == "high" else " "
            ans = f"  -> {r['answer']}" if r["answer"] else ""
            print(f"{flag}#{r['id']:<3} [{r['status']}] {r['topic']}: {r['question']}  (for: {r['needed_for']}){ans}")

    elif a.cmd == "answer":
        conn.execute("UPDATE open_items SET status=?, answer=?, answered_at=datetime('now','localtime') WHERE id=?",
                     ("dropped" if a.drop else "answered", a.text, a.id))
        conn.commit()
        print("ok")

    elif a.cmd == "export-companies":
        out = DATA_DIR / "startups_japan.csv"
        rows = conn.execute("""SELECT id, category, types, name_ja, name, tech_field, sector, prefecture, website,
                                      contact_emails, phone, contact_form_url, careers_url, listed_market,
                                      category_basis, sources, university, description
                               FROM companies WHERE region='japan'
                               ORDER BY category, types, name_ja""").fetchall()
        with open(out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(rows[0].keys())
            w.writerows([tuple(r) for r in rows])
        print(f"{out} ({len(rows)} rows)")

    elif a.cmd == "export":
        out = DATA_DIR / "ranking.csv"
        rows = conn.execute("""SELECT m.score, c.id, c.name, c.name_ja, c.sector, c.status, c.website, c.careers_url,
                                      c.contact_emails, m.fit_roles, m.reasons, m.concerns
                               FROM matches m JOIN companies c ON c.id=m.company_id ORDER BY m.score DESC""").fetchall()
        with open(out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(rows[0].keys() if rows else [])
            for r in rows:
                w.writerow([("; ".join(json.loads(v)) if k in ("fit_roles", "reasons", "concerns") and v else v)
                            for k, v in dict(r).items()])
        print(out)


if __name__ == "__main__":
    main()
