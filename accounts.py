"""Accounts: one personal data folder per job seeker.

Each account is a complete data folder (database, profile, documents, owner.json, browser login) - nothing is
shared between accounts except the public company list, which a new account copies once at creation.
The original folder <repo>/资料 is the account "default"; new accounts live in <repo>/accounts/<slug>
(or JOBAGENT_ACCOUNTS). The server picks one at start-up by setting JOBAGENT_HOME, so the rest of the code
keeps reading config.HOME as before.

This module must not import config (config creates folders under HOME at import time).
"""
import json
import os
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT / "资料"
TEMPLATE = ROOT / "资料.example"
ACCOUNTS_DIR = Path(os.environ.get("JOBAGENT_ACCOUNTS") or ROOT / "accounts").resolve()
LAST_FILE = ACCOUNTS_DIR / ".last"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")


def _json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _info(slug: str, home: Path) -> dict:
    owner, meta = _json(home / "owner.json"), _json(home / "account.json")
    name = owner.get("name") or meta.get("name") or slug
    return {"slug": slug, "name": name, "name_en": owner.get("name_en", ""), "nickname": owner.get("nickname", ""),
            "avatar": owner.get("avatar") or name[:1], "subtitle": owner.get("subtitle") or {},
            "created": meta.get("created", ""), "onboarded": meta.get("onboarded", True), "home": str(home)}


def list_accounts() -> list[dict]:
    out = [_info("default", LEGACY)] if (LEGACY / "data").exists() else []
    if ACCOUNTS_DIR.exists():
        out += [_info(d.name, d) for d in sorted(ACCOUNTS_DIR.iterdir())
                if d.is_dir() and (d / "account.json").exists()]
    return out


def home_of(slug: str) -> Path:
    if slug == "default":
        return LEGACY
    if not SLUG_RE.match(slug or "") or not (ACCOUNTS_DIR / slug / "account.json").exists():
        raise KeyError(slug)
    return ACCOUNTS_DIR / slug


def slug_of(home: Path) -> str:
    home = Path(home).resolve()
    return "default" if home == LEGACY.resolve() else home.name


def last() -> str | None:
    try:
        s = LAST_FILE.read_text(encoding="utf-8").strip()
        home_of(s)
        return s
    except (OSError, KeyError):
        return None


def set_last(slug: str):
    ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
    LAST_FILE.write_text(slug, encoding="utf-8")


def _new_slug(name_en: str, name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (name_en or "").lower()).strip("-")[:24] or "user"
    slug, i = base, 2
    while slug == "default" or (ACCOUNTS_DIR / slug).exists():
        slug, i = f"{base}-{i}", i + 1
    return slug


def _lines(text: str) -> str:
    rows = [r.strip(" -・\t") for r in (text or "").splitlines() if r.strip(" -・\t")]
    return "\n".join(f"- {r}" for r in rows) if rows else "- "


def profile_md(d: dict) -> str:
    """profile.md from the onboarding answers (the agent treats this file as the only source of facts)."""
    g = lambda k: (d.get(k) or "").strip()  # noqa: E731
    return f"""# 我的求职档案 / My job-search profile

> The agent treats this file as the only source of facts about you. Edit it any time; write everything it may use.

## 基本信息 / Basics
- Name: {g("name")}{f" ({g('name_en')})" if g("name_en") else ""}
- Nationality / visa: {" / ".join(x for x in (g("nationality"), g("visa")) if x)}
- Location: {g("location")}
- Phone / e-mail: {" / ".join(x for x in (g("phone"), g("email")) if x)}

## 学历 / Education
{_lines(d.get("education"))}

## 职历 / Work experience
{_lines(d.get("experience"))}

## 研究与技术 / Research & skills
{_lines(d.get("skills"))}

## 论文与发表 / Publications
{_lines(d.get("publications"))}

## 语言 / Languages
{_lines(d.get("languages"))}

## 求职偏好 / Preferences
- Roles (in order of preference): {g("roles")}
- Industries: {g("industries")}
- Location / remote: {g("work_location")}
- Working language: {g("work_language")}
- Start date: {g("start")}
- Not considering: {g("exclude")}
"""


def owner_json(d: dict) -> dict:
    g = lambda k: (d.get(k) or "").strip()  # noqa: E731
    name = g("name")
    intro = " ".join(x for x in (
        f"{name} ({g('name_en')})." if g("name_en") else f"{name}.",
        f"Education: {d['education'].splitlines()[0].strip()}." if g("education") else "",
        f"Experience: {d['experience'].splitlines()[0].strip()}." if g("experience") else "",
        f"Looking for: {g('roles')}." if g("roles") else "",
        f"Start: {g('start')}." if g("start") else "",
        f"Visa: {g('visa')}." if g("visa") else "") if x)
    mail = []
    if "@" in g("email"):
        gmail = g("email").lower().endswith("@gmail.com")
        mail.append({"id": "main", "label": "Gmail" if gmail else "Mail", "address": g("email"),
                     "display_name": name + (f"（{g('name_en')}）" if g("name_en") else ""),
                     **({"smtp_host": "smtp.gmail.com", "smtp_port": 587, "imap_host": "imap.gmail.com"} if gmail else {})})
    tagline = g("tagline")
    return {"name": name, "name_en": g("name_en"), "short_name": g("short_name") or name,
            "nickname": g("nickname"), "avatar": g("avatar") or name[:1],
            "subtitle": {"zh": tagline, "ja": tagline, "en": tagline}, "agent_intro": intro,
            "focus": g("industries") or g("roles"),          # used in the dashboard quick prompts
            "mail_accounts": mail, "resume_builds": {}}


def _copy_companies(home: Path):
    """Give a new account the public company list (scraped sources only) so it doesn't have to re-scrape."""
    src = LEGACY / "data" / "jobsearch.db"
    if not src.exists():
        return 0
    dst = home / "data" / "jobsearch.db"
    con = sqlite3.connect(dst)
    try:
        sql = sqlite3.connect(src).execute("SELECT sql FROM sqlite_master WHERE name='companies'").fetchone()[0]
        con.execute(sql)
        con.execute("ATTACH DATABASE ? AS src", (str(src),))
        # 'manual' rows and 'backup' tiers were added by hand for one person's applications - not public data
        con.execute("""INSERT INTO companies SELECT * FROM src.companies
                       WHERE source != 'manual' AND COALESCE(tier, '') != 'backup'""")
        con.commit()
        n = con.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        con.execute("DETACH DATABASE src")
        return n
    finally:
        con.close()


def create(d: dict) -> dict:
    name = (d.get("name") or "").strip()
    if not name:
        raise ValueError("name is required")
    slug = _new_slug(d.get("name_en", ""), name)
    home = ACCOUNTS_DIR / slug
    shutil.copytree(TEMPLATE, home)
    for sub in ("data", "outbox", "profile/materials"):
        (home / sub).mkdir(parents=True, exist_ok=True)
    (home / "profile" / "profile.md").write_text(profile_md(d), encoding="utf-8")
    (home / "owner.json").write_text(json.dumps(owner_json(d), ensure_ascii=False, indent=2), encoding="utf-8")
    if (d.get("cv_text") or "").strip():
        (home / "profile" / "materials" / "cv_pasted.md").write_text(d["cv_text"].strip() + "\n", encoding="utf-8")
    n = _copy_companies(home)
    con = sqlite3.connect(home / "data" / "jobsearch.db")     # UI language chosen in the guide
    con.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    con.execute("INSERT OR REPLACE INTO settings VALUES ('lang', ?)", (json.dumps(d.get("lang") or "zh"),))
    src = LEGACY / "data" / "jobsearch.db"
    if src.exists():                                            # same back-end (e.g. Claude CLI) as the default account
        row = sqlite3.connect(src).execute("SELECT value FROM settings WHERE key='provider'").fetchone()
        if row:
            con.execute("INSERT OR REPLACE INTO settings VALUES ('provider', ?)", row)
    con.commit()
    con.close()
    meta = {"name": name, "created": datetime.now().isoformat(timespec="seconds"), "onboarded": True,
            "lang": d.get("lang") or "zh", "companies_copied": n}
    (home / "account.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return _info(slug, home)
