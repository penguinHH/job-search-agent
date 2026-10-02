"""METI 大学発ベンチャーデータベース (data version, Excel).

https://www.meti.go.jp/policy/innovation_corp/univ-startupsdb.html
The sheet carries 法人番号, address, phone, e-mail, homepage, tech field, listing info, university.
"""
import sys
from pathlib import Path

import openpyxl
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DATA_DIR  # noqa: E402
from db import connect  # noqa: E402
from scrapers.common import clean_url, upsert_company  # noqa: E402

URL = "https://www.meti.go.jp/policy/innovation_corp/excel/Univ-venture_db_data.xlsx"
FILE = DATA_DIR / "sources" / "meti_univ_venture.xlsx"
# METI's server returns an HTML error page to short user agents
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def download():
    FILE.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(URL, headers={"User-Agent": UA}, timeout=60)
    r.raise_for_status()
    if not r.content.startswith(b"PK"):
        raise RuntimeError("METI returned a non-Excel response")
    FILE.write_bytes(r.content)


def val(row, ix, col):
    v = row[ix[col]] if col in ix else None
    if v is None:
        return None
    v = str(v).strip()
    return None if v in ("", "-", "None", "無", "なし", "無し") else v


def listing(row, ix) -> str | None:
    when, market = val(row, ix, "株式公開 公開時期"), val(row, ix, "株式公開 上場市場名")
    if market and market not in ("非上場", "未定", "その他"):
        return market
    if when and (when == "有" or when[:4].isdigit() and int(when[:4]) <= 2026):
        return f"公開 {when}"
    return None


def main(refresh: bool = False):
    if refresh or not FILE.exists():
        download()
    ws = openpyxl.load_workbook(FILE, read_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    ix = {h: i for i, h in enumerate(rows[0]) if h}
    conn = connect()
    new = 0
    for row in rows[1:]:
        name = val(row, ix, "企業名")
        if not name:
            continue
        listed = listing(row, ix)
        overview = " ".join(filter(None, [val(row, ix, "主力製品サービス名_日本語"), val(row, ix, "製品概要　日本語"),
                                          val(row, ix, "主力製品サービス関連技術分野_その他具体")]))
        f = {
            "name": val(row, ix, "企業名（英語）") or name, "name_ja": name,
            "website": clean_url(val(row, ix, "ホームページ")), "region": "japan",
            "corp_number": val(row, ix, "法人番号"), "prefecture": val(row, ix, "都道府県名"),
            "address": val(row, ix, "所在地"), "phone": val(row, ix, "連絡先_電話番号"),
            "contact_emails": val(row, ix, "メール"), "tech_field": val(row, ix, "主力製品サービス関連技術分野"),
            "university": val(row, ix, "関連大学") or val(row, ix, "1 関連大学"),
            "founded": val(row, ix, "設立年月"), "description": overview[:1000] or None,
            "status": "ipo" if listed else "active", "listed_market": listed,
        }
        _, created = upsert_company(conn, "meti_univ", f["corp_number"] or name, f)
        new += created
    conn.commit()
    print(f"METI univ ventures: {len(rows) - 1} rows, {new} new companies")


if __name__ == "__main__":
    main("--refresh" in sys.argv)
