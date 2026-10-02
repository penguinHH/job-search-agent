"""Scrape the Global Brains portfolio (https://globalbrains.com/en/portfolio).

The page is server-rendered by Nuxt; the full company list is embedded as a
JSON payload in <script id="__NUXT_DATA__">. That payload is a flat array where
objects reference other entries by index, so we resolve those references.
"""
import json
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import USER_AGENT  # noqa: E402
from db import connect  # noqa: E402

URL = "https://globalbrains.com/en/portfolio"


def fetch_companies() -> list[dict]:
    html = requests.get(URL, headers={"User-Agent": USER_AGENT}, timeout=30).text
    m = re.search(r'id="__NUXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise RuntimeError("Nuxt payload not found - page layout may have changed")
    payload = json.loads(m.group(1))

    def resolve(v):
        return payload[v] if isinstance(v, int) else v

    companies = []
    for obj in payload:
        if isinstance(obj, dict) and "nameEn" in obj and "websiteEn" in obj:
            c = {k: resolve(v) for k, v in obj.items()}
            companies.append({
                "source_id": str(c["id"]),
                "name": c["nameEn"],
                "name_ja": c.get("nameJa"),
                "website": c.get("websiteEn") or c.get("websiteJa"),
                "status": c.get("status"),
                "sector": c.get("sector"),
                "region": c.get("region"),
                "invested_at": (c.get("investedAt") or "")[:10] or None,
            })
    return companies


def save(companies: list[dict]) -> int:
    conn = connect()
    with conn:
        for c in companies:
            conn.execute(
                """INSERT INTO companies (source, source_id, name, name_ja, website,
                                          status, sector, region, invested_at)
                   VALUES ('globalbrains', :source_id, :name, :name_ja, :website,
                           :status, :sector, :region, :invested_at)
                   ON CONFLICT(source, source_id) DO UPDATE SET
                       name=excluded.name, name_ja=excluded.name_ja,
                       website=excluded.website, status=excluded.status,
                       sector=excluded.sector, region=excluded.region,
                       invested_at=excluded.invested_at""",
                c,
            )
    return len(companies)


if __name__ == "__main__":
    n = save(fetch_companies())
    print(f"Saved {n} Global Brains portfolio companies")
