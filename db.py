"""SQLite storage: company database (1), profile database (2), and agent state (3)."""
import sqlite3
from config import DB_PATH

SCHEMA = """
-- (1) candidate companies ---------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source        TEXT NOT NULL,            -- e.g. 'globalbrains'
    source_id     TEXT NOT NULL,            -- id inside that source
    name          TEXT NOT NULL,
    name_ja       TEXT,
    website       TEXT,
    status        TEXT,                     -- active / ipo / ma
    sector        TEXT,
    region        TEXT,
    invested_at   TEXT,
    -- enrichment from the company's own website
    title         TEXT,
    description   TEXT,                     -- meta description
    homepage_text TEXT,                     -- visible text excerpt
    careers_url   TEXT,
    careers_text  TEXT,
    contact_emails TEXT,                    -- comma separated, only ones published on site
    enriched_at   TEXT,
    enrich_error  TEXT,
    UNIQUE(source, source_id)
);

-- (2) the candidate (me) ----------------------------------------------------
CREATE TABLE IF NOT EXISTS profile_docs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    path      TEXT UNIQUE,
    kind      TEXT,                          -- cv / paper / note / profile
    text      TEXT,
    mtime     REAL
);
CREATE TABLE IF NOT EXISTS profile_summary (
    id        INTEGER PRIMARY KEY CHECK (id = 1),
    json      TEXT,                          -- structured profile built by Claude
    updated_at TEXT
);

-- (3) agent state -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS matches (
    company_id  INTEGER PRIMARY KEY REFERENCES companies(id),
    score       INTEGER,                     -- 0-100
    fit_roles   TEXT,
    reasons     TEXT,
    concerns    TEXT,
    scored_at   TEXT
);
CREATE TABLE IF NOT EXISTS documents (                 -- application materials (CV, 履歴書, letters ...)
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id  INTEGER REFERENCES companies(id),       -- NULL = general-purpose
    kind        TEXT,      -- rirekisho / cv / form_message / cover_letter / strategy / interview_prep ...
    title       TEXT,
    path        TEXT UNIQUE,
    lang        TEXT,
    status      TEXT,      -- draft / needs_info / final / submitted
    missing     TEXT,      -- what is still missing (JSON list)
    text        TEXT,      -- extracted full text, so the DB is searchable without opening files
    generator   TEXT,      -- script that regenerates it, if any
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    updated_at  TEXT
);
CREATE TABLE IF NOT EXISTS open_items (                -- questions waiting for the user's answer
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    topic       TEXT,
    question    TEXT,
    needed_for  TEXT,      -- which documents / companies need it
    priority    TEXT,      -- high / normal
    status      TEXT DEFAULT 'open',   -- open / answered / dropped
    answer      TEXT,
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    answered_at TEXT
);
CREATE TABLE IF NOT EXISTS outreach (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id  INTEGER REFERENCES companies(id),
    stage       TEXT,      -- shortlisted / drafted / sent / replied / interview / offer / rejected / closed
    note        TEXT,
    draft_path  TEXT,
    created_at  TEXT DEFAULT (datetime('now','localtime'))
);
"""


# Columns added after the first version; created on demand so old databases keep working.
COMPANY_EXTRA_COLUMNS = {
    "sources": "TEXT",           # every source that lists this company, e.g. 'globalbrains,jstartup'
    "domain": "TEXT",            # normalised website host, used to merge the same company across sources
    "corp_number": "TEXT",       # 法人番号
    "prefecture": "TEXT",
    "address": "TEXT",
    "phone": "TEXT",
    "contact_form_url": "TEXT",  # お問い合わせ page on the company's site
    "tech_field": "TEXT",        # source-provided field, e.g. METI 技術分野 / J-Startup category
    "university": "TEXT",        # related university (METI 大学発ベンチャー)
    "founded": "TEXT",
    "listed_market": "TEXT",     # JPX market if listed
    "category": "TEXT",          # A = not IPO and not M&A, B = IPO or M&A
    "category_basis": "TEXT",    # why B (e.g. 'JPX listed: グロース', 'GB status: ma')
    "types": "TEXT",             # '1' chem/materials, '2' IT, '1,2' both, 'other'
    "type_basis": "TEXT",        # matched keywords / source field behind the type
    "tier": "TEXT",              # NULL = main list (class A only); 'backup' = 保底候选 kept regardless of class
}


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    have = {r["name"] for r in conn.execute("PRAGMA table_info(companies)")}
    for col, typ in COMPANY_EXTRA_COLUMNS.items():
        if col not in have:
            conn.execute(f"ALTER TABLE companies ADD COLUMN {col} {typ}")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain)")
    conn.commit()
    return conn
