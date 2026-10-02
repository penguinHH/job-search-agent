"""Score companies against my profile.

Step 1 (free): a keyword heuristic ranks every company by how close it is to
computational chemistry / materials / AI / deep-tech.
Step 2 (Claude): the top-N of that ranking get a 0-100 fit score with
reasons, suitable roles and concerns, stored in the `matches` table.

Usage:
    python match.py --top 60                   # score the 60 best heuristic hits in Japan
    python match.py --top 30 --region any      # any region
    python match.py --ids 12 57 301            # score specific companies
    python match.py --heuristic-only           # just print the keyword ranking
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")  # Windows console
import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import anthropic
from pydantic import BaseModel

from config import FALLBACK, MODEL
from db import connect

SECTOR_WEIGHT = {
    "materials": 30, "quantum-computing": 28, "semiconductor": 28,
    "electronics-and-photonics": 25, "lifescience-healthcare": 22, "climate-tech": 22,
    "energy": 22, "ai": 20, "space": 15, "robotics": 12, "agritech-foodtech": 12,
    "iot": 8, "mobility": 8, "cloud-saas": 5, "enterprise": 5,
}
KEYWORDS = {
    r"materials? informatics|マテリアルズ・インフォマティクス|MI\b": 25,
    r"comput\w* chemi|計算化学|quantum chem|量子化学|DFT|第一原理|molecular dynamics|分子動力学|simulation|シミュレーション": 20,
    r"molecul|分子|chemi|化学|polymer|高分子|organic|有機|catalys|触媒": 15,
    r"material|素材|材料|battery|電池|semiconductor|半導体|photonic": 12,
    r"drug discovery|創薬|protein|タンパク|biotech|バイオ": 12,
    r"machine learning|deep learning|機械学習|深層学習|generative|生成AI|foundation model": 10,
    r"quantum|量子|HPC|GPU|high.performance comput": 10,
    r"R&D|研究開発|research|scientist|研究者|PhD|博士": 6,
    r"deep ?tech|ディープテック|university|大学発": 6,
}
STATUS_WEIGHT = {"active": 5, "ipo": 0, "ma": -10}


def heuristic(row) -> int:
    text = " ".join(filter(None, [row["name"], row["title"], row["description"],
                                  row["homepage_text"], row["careers_text"]]))
    s = SECTOR_WEIGHT.get(row["sector"], 0) + STATUS_WEIGHT.get(row["status"], 0)
    for pat, w in KEYWORDS.items():
        if re.search(pat, text, re.I):
            s += w
    if row["careers_url"]:
        s += 3
    return s


class Match(BaseModel):
    score: int              # 0-100 overall fit
    fit_roles: list[str]    # concrete roles the candidate could fill there
    reasons: list[str]      # why it fits, citing company facts
    concerns: list[str]     # gaps, risks, missing info (visa, language, stage ...)


def company_card(row, text_limit: int = 3000) -> str:
    return (
        f"Name: {row['name']} ({row['name_ja'] or ''})\n"
        f"Website: {row['website']}\nSector: {row['sector']} | Region: {row['region']} | "
        f"Status: {row['status']} | Global Brains invested: {row['invested_at']}\n"
        f"Title: {row['title'] or ''}\nDescription: {row['description'] or ''}\n"
        f"Homepage text: {(row['homepage_text'] or '')[:text_limit]}\n"
        f"Careers page: {row['careers_url'] or 'not found'}\n"
        f"Careers text: {(row['careers_text'] or '')[:text_limit]}"
    )


def load_profile(conn) -> str:
    r = conn.execute("SELECT json FROM profile_summary WHERE id=1").fetchone()
    if not r:
        raise SystemExit("No profile yet - run `python build_profile.py` first.")
    return r["json"]


def score_company(client, profile_json: str, row) -> Match:
    resp = client.beta.messages.parse(
        model=MODEL,
        max_tokens=4000,
        **FALLBACK,
        output_config={"effort": "medium"},
        system=[
            {"type": "text", "text":
                "You evaluate how well a startup fits a job-seeking candidate. Score 0-100: "
                "90+ = obvious, role-level fit; 70-89 = strong domain overlap and plausible role; "
                "40-69 = partial overlap; <40 = little relevance. Consider the candidate's skills, "
                "target roles, sector and location preferences, the company's stage/status "
                "(acquired companies may have merged into a parent), and whether it plausibly "
                "hires in Japan. Base company facts only on the provided card. Write in English."},
            {"type": "text", "text": f"<candidate_profile>\n{profile_json}\n</candidate_profile>",
             "cache_control": {"type": "ephemeral"}},
        ],
        messages=[{"role": "user", "content": company_card(row)}],
        output_format=Match,
    )
    if resp.stop_reason == "refusal" or resp.parsed_output is None:
        raise RuntimeError(f"no score for {row['name']} (stop_reason={resp.stop_reason})")
    return resp.parsed_output


def score_ids(ids: list[int], workers: int = 6) -> list[tuple]:
    conn = connect()
    profile = load_profile(conn)
    rows = conn.execute(f"SELECT * FROM companies WHERE id IN ({','.join('?' * len(ids))})", ids).fetchall()
    client = anthropic.Anthropic()

    def work(row):
        try:
            return row, score_company(client, profile, row), None
        except Exception as e:
            return row, None, e

    results = []
    with ThreadPoolExecutor(workers) as pool:
        for row, m, err in pool.map(work, rows):
            if err:
                print(f"  ! {row['name']}: {err}")
                continue
            conn.execute(
                "INSERT OR REPLACE INTO matches VALUES (?,?,?,?,?,?)",
                (row["id"], m.score, json.dumps(m.fit_roles, ensure_ascii=False),
                 json.dumps(m.reasons, ensure_ascii=False), json.dumps(m.concerns, ensure_ascii=False),
                 datetime.now().isoformat(timespec="seconds")))
            conn.commit()
            results.append((row["id"], row["name"], m.score))
            print(f"  {m.score:3d}  {row['name']}")
    return results


def heuristic_ranking(region: str = "japan", include_ma: bool = False) -> list[tuple]:
    conn = connect()
    sql = "SELECT * FROM companies WHERE 1=1"
    params = []
    if region != "any":
        sql += " AND region = ?"; params.append(region)
    if not include_ma:
        sql += " AND status != 'ma'"
    rows = conn.execute(sql, params).fetchall()
    return sorted(((heuristic(r), r["id"], r["name"], r["sector"]) for r in rows), reverse=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--region", default="japan", help="japan / north-america / asia / europe / any")
    ap.add_argument("--include-ma", action="store_true")
    ap.add_argument("--ids", type=int, nargs="*")
    ap.add_argument("--rescore", action="store_true", help="re-score companies already scored")
    ap.add_argument("--heuristic-only", action="store_true")
    args = ap.parse_args()

    if args.ids:
        score_ids(args.ids)
    else:
        ranking = heuristic_ranking(args.region, args.include_ma)
        if args.heuristic_only:
            for s, cid, name, sector in ranking[: args.top]:
                print(f"{s:4d}  #{cid:<4d} {name}  [{sector}]")
        else:
            scored = {r[0] for r in connect().execute("SELECT company_id FROM matches")}
            ids = [cid for _, cid, _, _ in ranking[: args.top] if args.rescore or cid not in scored]
            print(f"Scoring {len(ids)} companies with Claude ...")
            score_ids(ids)
