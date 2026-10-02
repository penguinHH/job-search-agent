"""Writing reviewer – a sub-agent that checks application texts before they go out.

Knowledge base: reviewer_kb/*.md (Japanese grammar & keigo, English grammar & style, writing principles for
emails / 履歴書 / CVs / cover letters / form answers), plus an optional personal file HOME/reviewer_knowledge.md.

It runs on the same model back-end as the main agent (Claude API / Claude CLI / OpenAI-compatible) and returns
structured issues + a fully revised version. Mode (setting "review_mode"):
  off      – no automatic review
  suggest  – review emails / documents the agent produces; the user applies suggestions (default)
  auto     – same, but the revised text replaces the original automatically (original kept for undo)
"""
import json
import os
import re
import subprocess
import threading
from pathlib import Path

import requests

from . import store

KB_DIR = Path(__file__).parent / "reviewer_kb"
PERSONAL_KB = store.HOME / "reviewer_knowledge.md"
MODES = ("off", "suggest", "auto")
TEXT_SUFFIXES = (".md", ".txt")

REVIEW_SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    target_kind  TEXT,      -- action / document / text
    target_ref   TEXT,      -- action id or document path ('' for ad-hoc text)
    doc_kind     TEXT,      -- email / cv / rirekisho / cover_letter / form_answer / interview / other
    lang         TEXT,
    company_id   INTEGER,
    mode         TEXT,
    status       TEXT DEFAULT 'running',   -- running / done / applied / dismissed / failed
    original     TEXT,      -- JSON {field: text}
    revised      TEXT,      -- JSON {field: text}
    issues       TEXT,      -- JSON list
    summary      TEXT,
    error        TEXT,
    created_at   TEXT DEFAULT (datetime('now','localtime')),
    updated_at   TEXT
);
"""

SYSTEM = """You are the writing reviewer of a job-search assistant. You check one application text (e-mail,
履歴書, 職務経歴書 / CV, cover letter, application-form answer, interview answer …) written for the candidate below,
and you return corrections. You do not chat and you do not use tools.

Check, in this order:
1. Facts – every experience, number, date, role, publication and skill must be supported by the candidate profile.
   Unsupported or exaggerated claims are severity "high", category "fact". Never add new facts yourself.
2. Correctness – company / person names, dates, attachments mentioned, placeholders left in the text.
3. Language – grammar, 敬語 (Japanese) or articles/tense/prepositions (English), natural wording.
4. Writing principles for this document type – structure, length, specificity, tone.

Keep the candidate's voice and the overall length unless length itself is a problem. Do not rewrite sentences that
are already correct just to change style. If the text is good, return an empty issue list and the text unchanged.

Return ONLY one JSON object, no markdown fences:
{"summary": "<1-2 sentences in {ui_lang}>",
 "issues": [{"severity": "high|medium|low", "category": "fact|keigo|grammar|wording|structure|format|content|confidential",
             "field": "<which field>", "quote": "<exact substring of the original field>",
             "suggestion": "<replacement for that substring (empty string = delete)>",
             "reason": "<short explanation in {ui_lang}>"}],
 "revised": {"<field>": "<full corrected text of that field>", ...}}
"quote" must be copied exactly from the original so it can be replaced automatically; keep quotes short (a phrase or
one sentence). "revised" must contain every field of the input, with all issues fixed.

# Knowledge base
{kb}

# Candidate profile (the only source of facts)
{profile}
"""

_lock = threading.Lock()


# ---------------------------------------------------------------- settings / storage
def mode():
    m = store.get_setting("review_mode", "suggest")
    return m if m in MODES else "suggest"


def _init():
    store.db().executescript(REVIEW_SCHEMA)


def get(rid):
    _init()
    r = store.row("SELECT * FROM reviews WHERE id=?", (rid,))
    return _decode(r) if r else None


def latest(target_kind, target_ref):
    _init()
    r = store.row("SELECT * FROM reviews WHERE target_kind=? AND target_ref=? ORDER BY id DESC LIMIT 1",
                  (target_kind, str(target_ref)))
    return _decode(r) if r else None


def list_reviews(target_kind=None):
    _init()
    if target_kind:
        rs = store.rows("SELECT * FROM reviews WHERE id IN (SELECT max(id) FROM reviews WHERE target_kind=? "
                        "GROUP BY target_ref)", (target_kind,))
    else:
        rs = store.rows("SELECT * FROM reviews ORDER BY id DESC LIMIT 100")
    return [_decode(r) for r in rs]


def _decode(r):
    for k, default in (("original", {}), ("revised", {}), ("issues", [])):
        try:
            r[k] = json.loads(r[k]) if r.get(k) else default
        except ValueError:
            r[k] = default
    return r


def _update(rid, **f):
    f["updated_at"] = store.now()
    for k in ("original", "revised", "issues"):
        if k in f and not isinstance(f[k], str):
            f[k] = json.dumps(f[k], ensure_ascii=False)
    store.execute(f"UPDATE reviews SET {', '.join(k + '=?' for k in f)} WHERE id=?", (*f.values(), rid))


# ---------------------------------------------------------------- targets (where the text lives)
def _read_target(kind, ref):
    if kind == "action":
        a = next((x for x in store.actions() if x["id"] == int(ref)), None)
        if not a or a["kind"] != "email":
            raise ValueError(f"action {ref} is not an e-mail")
        return {"subject": a["payload"].get("subject", ""), "body": a["payload"].get("body", "")}
    if kind == "document":
        p = Path(ref)
        return {"content": p.read_text(encoding="utf-8")}
    raise ValueError(f"cannot read target {kind}")


def _write_target(kind, ref, fields):
    if kind == "action":
        a = next((x for x in store.actions() if x["id"] == int(ref)), None)
        if not a or a["status"] != "pending":
            raise ValueError("the e-mail is no longer pending; nothing changed")
        p = {**a["payload"], **{k: v for k, v in fields.items() if k in ("subject", "body")}}
        store.execute("UPDATE actions SET payload=?, title=? WHERE id=?",
                      (json.dumps(p, ensure_ascii=False), p.get("subject", a["title"]), a["id"]))
    elif kind == "document":
        p = Path(ref)
        p.write_text(fields["content"], encoding="utf-8")
        store.execute("UPDATE documents SET text=?, updated_at=? WHERE path=?", (fields["content"], store.now(), str(p)))
    elif kind != "text":
        raise ValueError(f"cannot write target {kind}")


# ---------------------------------------------------------------- model call
def _kb(lang):
    parts = [(KB_DIR / "writing_principles.md").read_text(encoding="utf-8")]
    if lang in ("ja", "mixed"):
        parts.append((KB_DIR / "ja_grammar.md").read_text(encoding="utf-8"))
    if lang in ("en", "mixed"):
        parts.append((KB_DIR / "en_grammar.md").read_text(encoding="utf-8"))
    if PERSONAL_KB.exists():
        parts.append("# Personal rules\n" + PERSONAL_KB.read_text(encoding="utf-8"))
    return "\n\n".join(parts)


def detect_lang(text):
    kana = len(re.findall(r"[぀-ヿ]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    if kana > 20 and latin > 400:
        return "mixed"
    return "ja" if kana > 20 else "en"


def _complete(system, user):
    """One-shot completion on the configured back-end; returns the text."""
    from . import agent           # late import: agent imports tools, tools imports us
    s = agent.settings()
    prov = s["provider"]
    if prov == "claude_api":
        import anthropic
        key = agent.api_key()
        if not key:
            raise RuntimeError("Claude API key not set")
        cl = anthropic.Anthropic(api_key=key)
        with cl.messages.stream(model=agent.MODEL, max_tokens=16000, thinking={"type": "adaptive"},
                                system=system, messages=[{"role": "user", "content": user}]) as st:
            msg = st.get_final_message()
        return "".join(b.text for b in msg.content if b.type == "text")
    if prov == "claude_cli":
        exe = agent.claude_cli_path()
        if not exe:
            raise RuntimeError("claude CLI not found")
        sysfile = store.HOME / "data" / "reviewer_system_prompt.md"
        sysfile.write_text(system, encoding="utf-8")
        cmd = [exe, "-p", "--output-format", "json", "--strict-mcp-config", "--append-system-prompt-file", str(sysfile)]
        if s["cli_model"]:
            cmd += ["--model", s["cli_model"]]
        env = {**os.environ}
        env.pop("ANTHROPIC_API_KEY", None)
        r = subprocess.run(cmd, input=user, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=env, cwd=store.HOME, timeout=600, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout)[-800:])
        return json.loads(r.stdout).get("result", "")
    oa = s["openai"]
    base, model = oa.get("base_url", "").rstrip("/"), oa.get("model")
    key = agent.openai_key(oa.get("preset", "custom")) or ("ollama" if "localhost" in base else None)
    r = requests.post(f"{base}/chat/completions", timeout=600,
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                      json={"model": model, "temperature": 0.2,
                            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")
    return r.json()["choices"][0]["message"]["content"]


def _parse(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("reviewer did not return JSON: " + text[:300])
    return json.loads(text[start:end + 1])


def check(fields, doc_kind="other", lang=None, company_id=None, purpose=""):
    """Run the reviewer once (blocking). Returns {"summary", "issues", "revised"}."""
    from . import agent
    joined = "\n".join(fields.values())
    lang = lang or detect_lang(joined)
    ui = agent.LANG_NAME.get(agent.settings()["lang"], "Simplified Chinese")
    system = (SYSTEM.replace("{ui_lang}", ui).replace("{kb}", _kb(lang))
              .replace("{profile}", store.profile()["markdown"]))
    comp = store.row("SELECT name, description FROM companies WHERE id=?", (company_id,)) if company_id else None
    user = (f"Document type: {doc_kind}\nLanguage: {lang}\n"
            + (f"Purpose: {purpose}\n" if purpose else "")
            + (f"Recipient company: {comp['name']} – {(comp['description'] or '')[:400]}\n" if comp else "")
            + "Fields to review (JSON):\n" + json.dumps(fields, ensure_ascii=False, indent=1))
    out = _parse(_complete(system, user))
    issues = [i for i in out.get("issues", []) if isinstance(i, dict)]
    revised = out.get("revised") or {}
    revised = {k: revised.get(k, v) if isinstance(revised.get(k, v), str) else v for k, v in fields.items()}
    return {"summary": out.get("summary", ""), "issues": issues, "revised": revised, "lang": lang}


# ---------------------------------------------------------------- review lifecycle
def start(target_kind, target_ref, doc_kind="other", company_id=None, purpose="", force=False, background=True):
    """Create a review for an e-mail action or a document. Respects review_mode unless force=True."""
    m = mode()
    if m == "off" and not force:
        return None
    if target_kind == "document" and Path(target_ref).suffix.lower() not in TEXT_SUFFIXES:
        return None
    _init()
    fields = _read_target(target_kind, target_ref)
    rid = store.execute("INSERT INTO reviews(target_kind,target_ref,doc_kind,company_id,mode,original,updated_at) "
                        "VALUES(?,?,?,?,?,?,?)", (target_kind, str(target_ref), doc_kind, company_id,
                                                  m if m != "off" else "suggest",
                                                  json.dumps(fields, ensure_ascii=False), store.now()))

    def work():
        try:
            r = check(fields, doc_kind, None, company_id, purpose)
            _update(rid, status="done", revised=r["revised"], issues=r["issues"], summary=r["summary"], lang=r["lang"])
            if m == "auto" and r["issues"]:
                apply(rid)
        except Exception as e:  # noqa: BLE001 - shown in the GUI
            _update(rid, status="failed", error=f"{type(e).__name__}: {e}")

    if background:
        threading.Thread(target=work, daemon=True).start()
    else:
        work()
    return rid


def apply(rid, indices=None):
    """Apply all suggestions (use the reviewer's revised text) or only the selected issue indices."""
    r = get(rid)
    if not r or r["status"] not in ("done", "applied"):
        raise ValueError("review is not finished")
    if indices is None:
        new = {**r["original"], **r["revised"]}
        applied = list(range(len(r["issues"])))
    else:
        new = dict(_read_target(r["target_kind"], r["target_ref"])) if r["target_kind"] != "text" else dict(r["original"])
        applied = []
        for i in indices:
            iss = r["issues"][i]
            keys = [iss.get("field")] if iss.get("field") in new else list(new)
            for k in keys:
                if iss.get("quote") and iss["quote"] in new[k]:
                    new[k] = new[k].replace(iss["quote"], iss.get("suggestion", ""), 1)
                    applied.append(i)
                    break
    _write_target(r["target_kind"], r["target_ref"], new)
    issues = r["issues"]
    for i in applied:
        issues[i]["applied"] = True
    _update(rid, status="applied", issues=issues)
    return {"applied": applied, "fields": new}


def revert(rid):
    r = get(rid)
    if not r or r["status"] != "applied":
        raise ValueError("nothing to undo")
    _write_target(r["target_kind"], r["target_ref"], r["original"])
    _update(rid, status="done", issues=[{**i, "applied": False} for i in r["issues"]])


def dismiss(rid):
    _update(rid, status="dismissed")


def blocking_review(target_kind, target_ref):
    """In auto mode an e-mail must not be sent while its review is still running."""
    r = latest(target_kind, target_ref)
    return bool(r and r["status"] == "running" and r["mode"] == "auto")


def summary_line(rid):
    if not rid:
        return ""
    return (f" Reviewer sub-agent is checking it (review #{rid}, mode={mode()}); the user sees its suggestions next "
            "to the draft" + (" and they are applied automatically." if mode() == "auto" else "."))
