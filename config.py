"""Shared paths and settings.

Code lives in the repository; everything personal (database, profile, documents, owner settings) lives in
the data folder HOME, which defaults to <repo>/资料 and can be moved with the JOBAGENT_HOME environment variable.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent                           # code
HOME = Path(os.environ.get("JOBAGENT_HOME") or ROOT / "资料").resolve()   # personal data folder
DATA_DIR = HOME / "data"
DB_PATH = DATA_DIR / "jobsearch.db"
MATERIALS_DIR = HOME / "profile" / "materials"   # drop CV / papers / notes here
PROFILE_MD = HOME / "profile" / "profile.md"     # hand-written profile & preferences
OUTBOX_DIR = HOME / "outbox"                      # drafted documents and mails
OWNER_FILE = HOME / "owner.json"                  # name, mail accounts, CV build recipes

MODEL = "claude-opus-5-5"
# Server-side refusal fallback: if a safety classifier declines a request, the API
# re-runs it on Anthropic's recommended fallback model instead of returning a refusal.
FALLBACK = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

for _d in (DATA_DIR, OUTBOX_DIR, MATERIALS_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def owner() -> dict:
    """Personal settings of the job seeker (see 资料.example/owner.json)."""
    return json.loads(OWNER_FILE.read_text(encoding="utf-8")) if OWNER_FILE.exists() else {}
