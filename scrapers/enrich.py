"""Visit each company's own website and store what it says about itself.

Collects: page title, meta description, a visible-text excerpt, a careers/
recruit page (if linked from the homepage) with its text, and any contact
e-mail addresses published on those pages.

Usage:
    python scrapers/enrich.py                 # only companies not yet enriched
    python scrapers/enrich.py --all           # re-enrich everything
    python scrapers/enrich.py --region japan --status active
"""
import argparse
import re
import sys
sys.stdout.reconfigure(encoding="utf-8")  # Windows console
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import USER_AGENT  # noqa: E402
from db import connect  # noqa: E402

CAREER_HINTS = re.compile(
    r"career|recruit|job|join|hiring|work-with-us|採用|求人|キャリア|募集", re.I
)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}")
IGNORED_EMAIL = re.compile(r"\.(png|jpg|jpeg|gif|svg|webp)$|example\.|sentry|wixpress", re.I)
CONTACT_HINTS = re.compile(r"contact|inquiry|enquiry|お問い?合わ?せ|問合せ|コンタクト", re.I)
# Japanese phone numbers shown next to a TEL / 電話 label (FAX numbers are skipped)
PHONE_RE = re.compile(r"(?:TEL|Tel|tel|電話(?:番号)?|☎|℡)\s*[：:.]?\s*((?:\+81[\s-]?)?(?:\(0?\d{1,4}\)\s?|0?\d{1,4}[\s\-‐－ー−])\d{1,4}[\s\-‐－ー−]\d{3,4})")
TEXT_LIMIT = 6000

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en,ja;q=0.8"})


def get(url: str) -> tuple[str, str]:
    r = session.get(url, timeout=20, allow_redirects=True)
    r.raise_for_status()
    r.encoding = r.apparent_encoding if r.encoding in (None, "ISO-8859-1") else r.encoding
    return r.url, r.text


def visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
    return text[:TEXT_LIMIT]


def emails_in(html: str) -> set[str]:
    # strip JSON-escaped prefixes such as ">" that glue onto addresses in inline scripts
    found = {re.sub(r"^(u00[0-9a-f]{2})+", "", e).rstrip(".") for e in EMAIL_RE.findall(html)}
    return {e for e in found if "@" in e and not IGNORED_EMAIL.search(e)}


def phones_in(text: str) -> list[str]:
    return list(dict.fromkeys(re.sub(r"[‐－ー−]", "-", m.group(1)).strip() for m in PHONE_RE.finditer(text)))


def find_contact_link(soup: BeautifulSoup, base: str) -> str | None:
    host = urlparse(base).netloc
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("mailto:"):
            continue
        if CONTACT_HINTS.search(f"{a.get_text(' ', strip=True)} {a['href']}"):
            href = urljoin(base, a["href"])
            if href.startswith("http") and (urlparse(href).netloc == host
                                            or re.search(r"forms\.gle|docs\.google\.com/forms|hubspot|formrun|tayori", href)):
                return href
    return None


def find_careers_link(soup: BeautifulSoup, base: str) -> str | None:
    host = urlparse(base).netloc
    best = None
    for a in soup.find_all("a", href=True):
        label = f"{a.get_text(' ', strip=True)} {a['href']}"
        if CAREER_HINTS.search(label):
            href = urljoin(base, a["href"])
            if not href.startswith("http"):
                continue
            # prefer on-site pages; accept known ATS hosts too
            if urlparse(href).netloc == host:
                return href
            if best is None and re.search(r"greenhouse|lever|herp|wantedly|talentio|hrmos|workable|ashby|notion", href):
                best = href
    return best


def enrich_one(row) -> dict:
    out = {"id": row["id"], "enriched_at": datetime.now().isoformat(timespec="seconds")}
    if not row["website"]:
        out["enrich_error"] = "no website"
        return out
    try:
        final_url, html = get(row["website"])
        soup = BeautifulSoup(html, "html.parser")
        meta = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", attrs={"property": "og:description"})
        out["title"] = soup.title.get_text(strip=True)[:300] if soup.title else None
        out["description"] = meta.get("content", "").strip()[:1000] if meta else None
        careers = find_careers_link(soup, final_url)
        contact = find_contact_link(soup, final_url)
        emails = emails_in(html)
        emails |= {a["href"][7:].split("?")[0] for a in soup.find_all("a", href=True) if a["href"].startswith("mailto:")}
        out["homepage_text"] = visible_text(soup)
        phones = phones_in(out["homepage_text"])
        if contact:
            out["contact_form_url"] = contact
            if not emails or not phones:
                try:
                    _, cthtml = get(contact)
                    emails |= emails_in(cthtml)
                    phones += phones_in(visible_text(BeautifulSoup(cthtml, "html.parser")))
                except Exception:
                    pass
        out["phone"] = phones[0] if phones else None
        if careers:
            out["careers_url"] = careers
            try:
                _, chtml = get(careers)
                out["careers_text"] = visible_text(BeautifulSoup(chtml, "html.parser"))
                emails |= emails_in(chtml)
            except Exception as e:  # careers page failing is not fatal
                out["careers_text"] = f"[fetch failed: {e.__class__.__name__}]"
        out["contact_emails"] = ",".join(sorted(emails)[:10]) or None
        out["enrich_error"] = None
    except Exception as e:
        out["enrich_error"] = f"{e.__class__.__name__}: {str(e)[:200]}"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--region")
    ap.add_argument("--status")
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()

    conn = connect()
    sql, params = "SELECT id, name, website, description, contact_emails, phone FROM companies WHERE 1=1", []
    if not args.all:
        sql += " AND enriched_at IS NULL"
    if args.region:
        sql += " AND region = ?"; params.append(args.region)
    if args.status:
        sql += " AND status = ?"; params.append(args.status)
    rows = conn.execute(sql, params).fetchall()
    print(f"Enriching {len(rows)} companies ...")

    cols = ["title", "description", "homepage_text", "careers_url", "careers_text",
            "contact_emails", "contact_form_url", "phone", "enriched_at", "enrich_error"]
    existing = {r["id"]: r for r in rows}
    done = 0
    with ThreadPoolExecutor(args.workers) as pool:
        futures = [pool.submit(enrich_one, r) for r in rows]
        for f in as_completed(futures):
            res = f.result()
            old = existing[res["id"]]
            # keep source-provided data (METI phone/e-mail, J-Startup description); add what the site shows
            if old["description"]:
                res.pop("description", None)
            if old["phone"]:
                res.pop("phone", None)
            if old["contact_emails"] or res.get("contact_emails"):
                merged = set(filter(None, (old["contact_emails"] or "").split(","))) |                          set(filter(None, (res.get("contact_emails") or "").split(",")))
                res["contact_emails"] = ",".join(sorted(merged)[:10]) or None
            sets = ", ".join(f"{c} = ?" for c in cols if c in res)
            conn.execute(f"UPDATE companies SET {sets} WHERE id = ?",
                         [res[c] for c in cols if c in res] + [res["id"]])
            conn.commit()
            done += 1
            if done % 25 == 0:
                print(f"  {done}/{len(rows)}")
    ok = conn.execute("SELECT COUNT(*) FROM companies WHERE enrich_error IS NULL AND enriched_at IS NOT NULL").fetchone()[0]
    car = conn.execute("SELECT COUNT(*) FROM companies WHERE careers_url IS NOT NULL").fetchone()[0]
    print(f"Done. {ok} sites fetched OK, {car} with a careers page found.")


if __name__ == "__main__":
    main()
