"""Helpers shared by all company sources: normalisation and merge-on-insert."""
import re
import unicodedata
from urllib.parse import urlparse

# hosts that are not a company's own site (social, blogs, generic platforms)
NON_COMPANY_HOSTS = re.compile(
    r"(facebook|twitter|x\.com|linkedin|instagram|youtube|note\.com|wix|jimdo|google|prtimes|wantedly)", re.I)

LEGAL_FORMS = re.compile(
    r"株式会社|（株）|\(株\)|㈱|合同会社|有限会社|一般社団法人|一般財団法人|合資会社|"
    r"\b(inc|incorporated|co|corp|corporation|ltd|limited|llc|k\.?k|g\.?k)\b\.?", re.I)


def norm_name(name: str | None) -> str:
    if not name:
        return ""
    s = unicodedata.normalize("NFKC", name).lower()
    s = LEGAL_FORMS.sub("", s)
    return re.sub(r"[\s　,.・･\-_'’&()（）]", "", s)


def norm_domain(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip().replace("，", ",").split(",")[0]
    if not re.match(r"https?://", url, re.I):
        url = "http://" + url
    try:
        host = urlparse(unicodedata.normalize("NFKC", url)).netloc.lower().split(":")[0]
    except ValueError:        # malformed (e.g. full-width garbage) URL in source data
        return None
    host = re.sub(r"^www\d?\.", "", host)
    if not host or "." not in host or NON_COMPANY_HOSTS.search(host):
        return None
    return host


def clean_url(url: str | None) -> str | None:
    if not url:
        return None
    url = str(url).strip().split()[0].replace("，", ",").split(",")[0]
    if not url or url in {"-", "なし", "無"}:
        return None
    return url if re.match(r"https?://", url, re.I) else "https://" + url


def find_existing(conn, fields: dict):
    if fields.get("corp_number"):
        r = conn.execute("SELECT * FROM companies WHERE corp_number=?", (fields["corp_number"],)).fetchone()
        if r:
            return r
    if fields.get("domain"):
        r = conn.execute("SELECT * FROM companies WHERE domain=?", (fields["domain"],)).fetchone()
        if r:
            return r
    key = norm_name(fields.get("name_ja")) or norm_name(fields.get("name"))
    if key:
        for r in conn.execute("SELECT * FROM companies WHERE region='japan' OR region IS NULL"):
            if key in (norm_name(r["name_ja"]), norm_name(r["name"])):
                return r
    return None


def upsert_company(conn, source: str, source_id: str, fields: dict) -> tuple[int, bool]:
    """Insert, or merge into an existing row describing the same company.
    Existing non-empty values win, except status 'ipo'/'ma' which always overrides 'active'.
    Returns (company_id, created)."""
    fields = {k: v for k, v in fields.items() if v not in (None, "")}
    fields.setdefault("domain", norm_domain(fields.get("website")))
    existing = find_existing(conn, fields)
    if existing:
        sets, vals = [], []
        for k, v in fields.items():
            cur = existing[k]
            if cur in (None, "") or (k == "status" and v in ("ipo", "ma") and cur == "active"):
                sets.append(f"{k}=?"); vals.append(v)
        srcs = set(filter(None, (existing["sources"] or existing["source"] or "").split(",")))
        if source not in srcs:
            srcs.add(source)
            sets.append("sources=?"); vals.append(",".join(sorted(srcs)))
        if sets:
            conn.execute(f"UPDATE companies SET {', '.join(sets)} WHERE id=?", vals + [existing["id"]])
        return existing["id"], False
    fields.update(source=source, source_id=source_id, sources=source)
    cols = ", ".join(fields)
    cur = conn.execute(f"INSERT INTO companies ({cols}) VALUES ({', '.join('?' * len(fields))})",
                       list(fields.values()))
    return cur.lastrowid, True
