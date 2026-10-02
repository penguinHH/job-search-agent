"""Build the candidate (me) database from profile/profile.md + profile/materials/*.

1. Extracts text from every file in profile/materials (pdf, docx, md, txt)
   and from profile/profile.md into the profile_docs table.
2. Asks Claude to distil everything into a structured profile (skills,
   research, target roles, preferences ...) stored in profile_summary.

Usage:  python build_profile.py            (re-run whenever you add materials)
        python build_profile.py --no-llm   (only extract text)
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")  # Windows console
import argparse
import json
from datetime import datetime
from pathlib import Path

import anthropic
from pydantic import BaseModel

from config import FALLBACK, MATERIALS_DIR, MODEL, PROFILE_MD
from db import connect

MAX_DOC_CHARS = 60000   # per document sent to Claude; long theses are clipped with a note


class Publication(BaseModel):
    title: str
    venue_year: str


class Profile(BaseModel):
    name: str
    headline: str                       # one-line pitch in English
    education: list[str]
    research_summary: str               # 3-5 sentences
    computational_skills: list[str]     # methods, codes, programming, ML, HPC
    chemistry_materials_skills: list[str]
    software_engineering_skills: list[str]
    publications: list[Publication]
    languages: list[str]
    target_roles: list[str]
    target_sectors: list[str]
    preferences: list[str]              # location, salary, stage, visa, start date ...
    dealbreakers: list[str]
    unique_selling_points: list[str]    # what makes this candidate stand out for startups
    open_questions: list[str]           # info missing that would help the job search


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    if suffix == ".docx":
        import docx
        from docx.table import Table
        from docx.text.paragraph import Paragraph
        doc = docx.Document(path)
        lines = []
        # walk the body in document order so tables (education, skills ...) aren't lost
        for el in doc.element.body.iterchildren():
            if el.tag.endswith("}p"):
                lines.append(Paragraph(el, doc).text)
            elif el.tag.endswith("}tbl"):
                for row in Table(el, doc).rows:
                    cells = []
                    for c in row.cells:          # merged cells repeat - keep each once
                        t = c.text.strip()
                        if t and t not in cells:
                            cells.append(t)
                    lines.append(" | ".join(cells))
        return "\n".join(l for l in lines if l.strip())
    if suffix in {".md", ".txt", ".tex", ".bib", ".csv", ".json", ".yaml", ".yml"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    return ""


def guess_kind(path: Path) -> str:
    n = path.name.lower()
    if path == PROFILE_MD:
        return "profile"
    if any(k in n for k in ("cv", "resume", "履歴", "職務", "简历")):
        return "cv"
    if path.suffix.lower() in {".pdf", ".tex"}:
        return "paper"
    return "note"


def ingest(conn) -> list:
    files = [PROFILE_MD] + sorted(p for p in MATERIALS_DIR.rglob("*") if p.is_file())
    for p in files:
        mtime = p.stat().st_mtime
        row = conn.execute("SELECT mtime FROM profile_docs WHERE path=?", (str(p),)).fetchone()
        if row and row["mtime"] == mtime:
            continue
        text = extract_text(p)
        if not text.strip():
            print(f"  skip (no text extracted): {p.name}")
            continue
        conn.execute(
            """INSERT INTO profile_docs(path, kind, text, mtime) VALUES (?,?,?,?)
               ON CONFLICT(path) DO UPDATE SET kind=excluded.kind, text=excluded.text, mtime=excluded.mtime""",
            (str(p), guess_kind(p), text, mtime))
        print(f"  ingested {p.name} ({len(text)} chars)")
    # drop docs whose files were removed
    for r in conn.execute("SELECT path FROM profile_docs").fetchall():
        if not Path(r["path"]).exists():
            conn.execute("DELETE FROM profile_docs WHERE path=?", (r["path"],))
    conn.commit()
    return conn.execute("SELECT * FROM profile_docs ORDER BY kind").fetchall()


def summarise(conn, docs) -> Profile:
    parts = []
    for d in docs:
        text = d["text"]
        if len(text) > MAX_DOC_CHARS:
            text = text[:MAX_DOC_CHARS] + "\n[... document clipped ...]"
        parts.append(f'<document kind="{d["kind"]}" file="{Path(d["path"]).name}">\n{text}\n</document>')
    client = anthropic.Anthropic()
    resp = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        **FALLBACK,
        output_config={"effort": "high"},
        system=(
            "You build a job-search profile for a candidate from their own materials. "
            "The document of kind 'profile' is written by the candidate and overrides anything "
            "inferred elsewhere. Only state facts supported by the documents; leave a list empty "
            "rather than inventing. Put anything important but missing into open_questions. "
            "Write all fields in English."
        ),
        messages=[{"role": "user", "content": "\n\n".join(parts)}],
        output_format=Profile,
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("Model declined to build the profile")
    profile = resp.parsed_output
    conn.execute(
        "INSERT OR REPLACE INTO profile_summary(id, json, updated_at) VALUES (1, ?, ?)",
        (profile.model_dump_json(indent=2), datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    return profile


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true")
    args = ap.parse_args()
    conn = connect()
    docs = ingest(conn)
    print(f"{len(docs)} profile documents in database")
    if not args.no_llm:
        p = summarise(conn, docs)
        print(json.dumps(p.model_dump(), ensure_ascii=False, indent=2))
