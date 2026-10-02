"""J-Startup (METI-selected startups, https://www.j-startup.go.jp/startups/).

Each company page lists: name, category, 法人番号, official URL and a short description.
"""
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import USER_AGENT  # noqa: E402
from db import connect  # noqa: E402
from scrapers.common import clean_url, upsert_company  # noqa: E402

LIST_URL = "https://www.j-startup.go.jp/startups/"
H = {"User-Agent": USER_AGENT}


def list_pages() -> list[tuple[str, str]]:
    s = BeautifulSoup(requests.get(LIST_URL, headers=H, timeout=30).content, "html.parser")
    out = {}
    for a in s.find_all("a", href=True):
        if re.match(r"^/startups/\d+[a-z]?-[\w-]+\.html$", a["href"]):
            out[urljoin(LIST_URL, a["href"])] = a["href"].split("/")[-1][:-5]
    return list(out.items())


def parse(url: str, slug: str) -> dict | None:
    s = BeautifulSoup(requests.get(url, headers=H, timeout=30).content, "html.parser")
    for t in s(["script", "style"]):
        t.decompose()
    main = s.find("main") or s.body
    text = re.sub(r"\s+", " ", main.get_text(" ")).strip()
    h = main.find(["h1", "h2"])
    name = h.get_text(" ", strip=True) if h else text.split(" ")[0]
    m = re.search(r"法人番号[｜|:：\s]*(\d{13})", text)
    site = next((a["href"] for a in main.find_all("a", href=True)
                 if a["href"].startswith("http") and "j-startup.go.jp" not in a["href"]), None)
    cat = re.search(r"(AI/制御|IoTデバイス/ICT/アプリ|サービス/プラットフォーム|製造/素材[・･]マテリアル|"
                    r"医工/バイオ|環境/エネルギー/社会|航空/宇宙|ロボティクス|モビリティ)", text)
    desc = text
    if site and site in desc:
        desc = desc.split(site, 1)[1]
    desc = re.split(r"Startups List|\d{4}\.\d{2}\.\d{2}", desc)[0].strip()[:1000]
    return {
        "name": name, "name_ja": name, "website": clean_url(site), "region": "japan",
        "corp_number": m.group(1) if m else None, "tech_field": cat.group(1) if cat else None,
        "description": desc, "status": "active",
    }


def main():
    pages = list_pages()
    print(f"J-Startup: {len(pages)} company pages")
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda p: (p, parse(*p)), pages))
    conn = connect()
    new = 0
    for (url, slug), f in results:
        if f:
            _, created = upsert_company(conn, "jstartup", slug, f)
            new += created
    conn.commit()
    print(f"saved: {new} new, {len(results) - new} merged into existing companies")


if __name__ == "__main__":
    main()
