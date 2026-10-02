"""Classify Japanese startups and prune the company table.

Category (IPO / M&A):
    A = neither IPO nor M&A          B = IPO or M&A (either one)
    Evidence: source status (Global Brains ipo/ma, METI 株式公開), the JPX listed-company file
    (name match), and acquisition wording on the company's own site ("〜の子会社となりました",
    "acquired by", ...).
Type (field):
    1 = chemistry / materials        2 = IT (software, AI, IoT, data, platforms ...)
    '1,2' when both apply, 'other' when neither. Source category fields decide first; otherwise
    at least two distinct keyword hits in the company's own description/site text are required.
Contact: a company counts as contactable if it has a published e-mail, phone or contact-form page.

    python classify.py            # classify + report
    python classify.py --prune    # also delete companies outside Japan, without contact, or in class B
                                  #   (rows referenced by the pipeline or documents are kept)
"""
import argparse
import re
import sys
import unicodedata

import openpyxl
import requests

sys.stdout.reconfigure(encoding="utf-8")

from config import DATA_DIR
from db import connect
from scrapers.common import norm_name

JPX_URL = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xlsx"
JPX_FILE = DATA_DIR / "sources" / "jpx_listed.xlsx"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

TYPE1_FIELDS = {"素材", "materials", "semiconductor", "electronics-and-photonics", "製造/素材・マテリアル",
                "製造/素材･マテリアル"}
TYPE2_FIELDS = {"ソフトウェア・アプリ", "AI・IoT", "AI/制御", "IoTデバイス/ICT/アプリ", "サービス/プラットフォーム",
                "ai", "cloud-saas", "enterprise", "fintech", "commerce", "media", "hr-tech", "iot",
                "cybersecurity", "xr-metaverse", "game", "ad", "education", "travel-tech", "realestate-tech",
                "blockchain", "quantum-computing", "entertainment-tech"}

TYPE1_KW = [
    r"化学", r"化合物", r"材料", r"素材", r"マテリアル", r"高分子", r"ポリマー", r"樹脂", r"触媒", r"電池", r"電解",
    r"半導体", r"ナノ", r"薄膜", r"結晶", r"有機合成|合成技術|化学合成", r"セラミック", r"合金", r"金属", r"繊維",
    r"カーボン|炭素", r"グラフェン", r"ペロブスカイト", r"塗料|コーティング", r"インク", r"接着", r"分離膜|膜技術",
    r"マテリアルズ・?インフォマティクス", r"計算化学|量子化学|第一原理",
    r"chemi", r"\bmaterials?\b", r"polymer", r"catalys", r"batter(y|ies)", r"semiconductor", r"nano",
    r"crystal", r"compound", r"synthes", r"graphene", r"perovskite", r"ceramic", r"alloy", r"coating",
]
TYPE2_STRONG = [
    r"AI|人工知能", r"機械学習|深層学習|ディープラーニング", r"ソフトウェア|software", r"SaaS", r"クラウド|cloud",
    r"アプリ(開発|ケーション)?|app", r"IoT", r"DX", r"システム開発", r"ブロックチェーン|blockchain",
    r"量子コンピュータ|quantum comput", r"LLM|生成AI|generative AI", r"machine learning|deep learning",
    r"API", r"Web(サービス|アプリ|サイト制作)|ウェブ",
]
# generic words that only count together with a strong hit ("platform" and "data" also appear in biotech)
TYPE2_WEAK = [r"プラットフォーム|platform", r"データ|data", r"アルゴリズム|algorithm", r"エッジ|edge", r"デジタル|digital"]
MA_PATTERNS = [
    r"の(完全)?子会社(となりました|になりました|となり|化され)", r"グループ(入り|に参画|に加わ|の一員となりました)",
    r"(was|has been|have been) acquired by", r"\bis now (a )?part of\b", r"\ba (wholly[- ]owned )?subsidiary of\b",
    r"(株式|全株式)を(取得|譲渡)(され|いたしました)",
]


def load_jpx() -> dict[str, str]:
    if not JPX_FILE.exists():
        r = requests.get(JPX_URL, headers={"User-Agent": UA}, timeout=60)
        r.raise_for_status()
        JPX_FILE.parent.mkdir(parents=True, exist_ok=True)
        JPX_FILE.write_bytes(r.content)
    ws = openpyxl.load_workbook(JPX_FILE, read_only=True).worksheets[0]
    listed = {}
    for row in list(ws.iter_rows(values_only=True))[1:]:
        name, market = row[2], str(row[3] or "")
        if name and "株式" in market:              # skip ETFs, REITs, etc.
            key = norm_name(str(name))
            if len(key) >= 2:
                listed[key] = market
    return listed


def hits(patterns, text) -> list[str]:
    return [p for p in patterns if re.search(p, text, re.I)]


def classify_row(r, jpx) -> dict:
    own_text = " ".join(filter(None, [r["name"], r["name_ja"], r["title"], r["description"],
                                      (r["homepage_text"] or "")[:3000]]))
    own_text = unicodedata.normalize("NFKC", own_text)

    # --- category ---
    basis = []
    if r["status"] in ("ipo", "ma"):
        basis.append(f"source status: {r['status']}" + (f" ({r['listed_market']})" if r["listed_market"] else ""))
    for key in {norm_name(r["name_ja"]), norm_name(r["name"])} - {""}:
        if key in jpx:
            basis.append(f"JPX listed: {jpx[key]}")
            break
    ma = hits(MA_PATTERNS, (r["homepage_text"] or ""))
    if ma:
        basis.append(f"site text suggests M&A: /{ma[0]}/")
    category = "B" if basis else "A"

    # --- type ---
    field = (r["tech_field"] or r["sector"] or "").strip()
    t1 = hits(TYPE1_KW, own_text)
    t2s, t2w = hits(TYPE2_STRONG, own_text), hits(TYPE2_WEAK, own_text)
    is1 = field in TYPE1_FIELDS or len(t1) >= 2
    is2 = field in TYPE2_FIELDS or len(t2s) >= 2 or (len(t2s) == 1 and len(t2w) >= 2)
    types = ",".join(t for t, ok in (("1", is1), ("2", is2)) if ok) or "other"
    tb = f"field={field or '-'}; t1={len(t1)} t2={len(t2s)}+{len(t2w)}w"
    return {"category": category, "category_basis": "; ".join(basis) or None, "types": types, "type_basis": tb}


def contactable(r) -> bool:
    return bool(r["contact_emails"] or r["phone"] or r["contact_form_url"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prune", action="store_true")
    args = ap.parse_args()
    conn = connect()
    jpx = load_jpx()

    rows = conn.execute("SELECT * FROM companies WHERE region='japan' AND tier IS NULL").fetchall()
    for r in rows:
        c = classify_row(r, jpx)
        if (r["type_basis"] or "").startswith("manual"):      # hand-verified type: keep it
            c["types"], c["type_basis"] = r["types"], r["type_basis"]
        if (r["category_basis"] or "").startswith("manual"):
            c["category"], c["category_basis"] = r["category"], r["category_basis"]
        conn.execute("UPDATE companies SET category=?, category_basis=?, types=?, type_basis=? WHERE id=?",
                     (c["category"], c["category_basis"], c["types"], c["type_basis"], r["id"]))
    conn.commit()

    # prune after classifying, so freshly imported class-B companies are removed too
    if args.prune:
        keep = "SELECT company_id FROM outreach UNION SELECT company_id FROM documents WHERE company_id IS NOT NULL"
        cands = conn.execute(f"SELECT * FROM companies WHERE id NOT IN ({keep})").fetchall()
        drop = [r["id"] for r in cands if r["tier"] != "backup"
                and (r["region"] != "japan" or not contactable(r) or r["category"] == "B")]
        conn.executemany("DELETE FROM matches WHERE company_id=?", [(i,) for i in drop])
        conn.executemany("DELETE FROM companies WHERE id=?", [(i,) for i in drop])
        conn.commit()
        print(f"pruned {len(drop)} companies (outside Japan, no published contact, or class B)")
        rows = conn.execute("SELECT * FROM companies WHERE region='japan' AND tier IS NULL").fetchall()

    print(f"\nJapan companies: {len(rows)}   contactable: {sum(contactable(r) for r in rows)}")
    print("\n          type1  type2  1+2  other  total")
    for cat in ("A", "B"):
        q = lambda t: conn.execute("SELECT COUNT(*) FROM companies WHERE region='japan' AND tier IS NULL AND category=? AND types=?",
                                   (cat, t)).fetchone()[0]
        n1, n2, n12, no = q("1"), q("2"), q("1,2"), q("other")
        print(f"  {cat}      {n1:5d}  {n2:5d}  {n12:4d}  {no:5d}  {n1 + n2 + n12 + no:5d}")


if __name__ == "__main__":
    main()
