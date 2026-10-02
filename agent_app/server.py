"""FastAPI backend for the GUI."""
import json
import threading
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import agent, mailer, store, tools
from .browser import browser

STATIC = Path(__file__).parent / "static"
app = FastAPI(title="求职 Agent")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
STOP = {}


@app.get("/")
def index():
    # cache-bust the static assets so a restart always serves the current frontend
    v = int(max((STATIC / f).stat().st_mtime for f in ("app.js", "style.css")))
    html = (STATIC / "index.html").read_text(encoding="utf-8").replace(".css\"", f".css?v={v}\"").replace(
        ".js\"", f".js?v={v}\"")
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


# ---------------------------------------------------------------- overview
@app.get("/api/stats")
def stats():
    s = store.stats()
    s["recent_mail"] = store.rows("""SELECT i.id,i.subject,i.from_name,i.from_addr,i.date,i.status,c.name company,
        i.company_id FROM inbox i LEFT JOIN companies c ON c.id=i.company_id ORDER BY i.date DESC LIMIT 8""")
    s["pending"] = store.actions("pending")[:10]
    s["questions"] = store.questions("open")[:8]
    s["stage_labels"] = store.STAGE_LABEL
    return s


# ---------------------------------------------------------------- companies & pipeline
@app.get("/api/companies")
def companies(q: str = "", type: str = "", category: str = "A", applied: str = "", min_score: int | None = None,
              prefecture: str = "", stage: str = "", limit: int = 50, offset: int = 0, order: str = "score"):
    ap = {"yes": True, "no": False}.get(applied)
    return store.search_companies(q, type or None, category or None, stage or None, ap, min_score,
                                  prefecture or None, limit, offset, order)


@app.get("/api/companies/{cid}")
def company(cid: int):
    c = store.company(cid)
    if not c:
        raise HTTPException(404)
    return c


@app.post("/api/companies/{cid}/stage")
def set_stage(cid: int, body: dict = Body(...)):
    store.set_stage(cid, body["stage"], body.get("note", ""))
    return {"ok": True}


@app.post("/api/companies/{cid}/score")
def set_score(cid: int, body: dict = Body(...)):
    store.set_score(cid, int(body["score"]), body.get("roles"), body.get("reasons"), body.get("concerns"))
    return {"ok": True}


@app.post("/api/companies/{cid}/enrich")
def enrich(cid: int):
    return json.loads(tools.enrich_company(cid))


@app.get("/api/pipeline")
def pipeline():
    return {"items": store.pipeline(), "stages": store.STAGES, "labels": store.STAGE_LABEL}


# ---------------------------------------------------------------- profile & questions
@app.get("/api/profile")
def profile():
    return store.profile()


@app.put("/api/profile")
def save_profile(body: dict = Body(...)):
    store.save_profile_md(body["markdown"])
    return {"ok": True}


@app.get("/api/questions")
def questions(status: str = "open"):
    return store.questions(status)


@app.post("/api/questions")
def add_question(body: dict = Body(...)):
    return {"id": store.ask(body["question"], body.get("topic", ""), body.get("needed_for", ""),
                            body.get("priority", "normal"))}


@app.post("/api/questions/{qid}/answer")
def answer(qid: int, body: dict = Body(...)):
    store.answer(qid, body.get("answer", ""), bool(body.get("drop")))
    return {"ok": True}


# ---------------------------------------------------------------- documents & files
@app.get("/api/documents")
def documents():
    finals = sorted(p.relative_to(store.HOME).as_posix() for p in tools.FINAL.glob("*.pdf")) if tools.FINAL.exists() else []
    return {"documents": store.documents(), "finals": finals}


@app.post("/api/documents/build")
def build(body: dict = Body(default={})):
    return json.loads(tools.build_resume(body.get("variant", "all")))


@app.get("/api/file")
def file(path: str, download: bool = False):
    p = (store.HOME / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if not p.is_relative_to(store.HOME) or not p.exists():
        raise HTTPException(404)
    if p.suffix.lower() in (".md", ".txt", ".json") and not download:
        return {"path": path, "text": p.read_text(encoding="utf-8", errors="replace")}
    return FileResponse(p, filename=p.name if download else None)


@app.put("/api/file")
def save_file(body: dict = Body(...)):
    p = (store.HOME / body["path"]).resolve()
    if not p.is_relative_to(store.HOME / "outbox") or p.suffix.lower() not in (".md", ".txt"):
        raise HTTPException(400, "only outbox/*.md|txt can be edited here")
    p.write_text(body["text"], encoding="utf-8")
    return {"ok": True}


# ---------------------------------------------------------------- approval queue
@app.get("/api/actions")
def actions(status: str = ""):
    return store.actions(status or None)


@app.put("/api/actions/{aid}")
def edit_action(aid: int, body: dict = Body(...)):
    a = store.row("SELECT * FROM actions WHERE id=?", (aid,))
    if not a or a["status"] != "pending":
        raise HTTPException(400, "only pending actions can be edited")
    store.execute("UPDATE actions SET payload=? WHERE id=?", (json.dumps(body["payload"], ensure_ascii=False), aid))
    return {"ok": True, "problems": mailer.check_email(body["payload"]) if a["kind"] == "email" else []}


@app.post("/api/actions/{aid}/approve")
def approve(aid: int):
    a = store.actions()
    a = next((x for x in a if x["id"] == aid), None)
    if not a or a["status"] != "pending":
        raise HTTPException(400, "not pending")
    p = a["payload"]
    try:
        if a["kind"] == "email":
            mid = mailer.send(p)
            store.update_action(aid, "done", f"sent {mid}")
            if a["company_id"]:
                store.set_stage(a["company_id"], "sent" if not p.get("in_reply_to") else "replied",
                                f"email sent ({p.get('account')}): {p['subject']} → {', '.join(p['to'])}")
            return {"ok": True, "result": f"已发送 {mid}"}
        if a["kind"] == "form_submit":
            snap = browser.snapshot()
            if snap["url"].split("#")[0] != p["url"].split("#")[0]:
                raise RuntimeError(f"浏览器当前页面已变化（{snap['url']}），请让 agent 重新准备")
            after = browser.click(p["field_id"])
            store.update_action(aid, "done", f"clicked → {after.get('url')} | {after.get('title')}")
            return {"ok": True, "result": after.get("title"), "url": after.get("url")}
        raise RuntimeError(f"unknown action kind {a['kind']}")
    except Exception as e:  # noqa: BLE001
        store.update_action(aid, "failed", str(e))
        raise HTTPException(500, str(e))


@app.post("/api/actions/{aid}/reject")
def reject(aid: int, body: dict = Body(default={})):
    store.update_action(aid, "rejected", body.get("reason", ""))
    return {"ok": True}


@app.post("/api/actions/{aid}/mark_done")
def mark_done(aid: int):
    """User submitted the form themselves (e.g. after solving a CAPTCHA)."""
    a = store.row("SELECT * FROM actions WHERE id=?", (aid,))
    store.update_action(aid, "done", "submitted manually by the user")
    if a and a["company_id"]:
        store.set_stage(a["company_id"], "sent", f"web form submitted: {a['title']}")
    return {"ok": True}


# ---------------------------------------------------------------- inbox
@app.get("/api/inbox")
def inbox(status: str = ""):
    sql = """SELECT i.id,i.account,i.from_addr,i.from_name,i.subject,i.date,i.status,i.company_id,c.name company,
             substr(i.body,1,200) preview FROM inbox i LEFT JOIN companies c ON c.id=i.company_id"""
    if status:
        return store.rows(sql + " WHERE i.status=? ORDER BY i.date DESC LIMIT 300", (status,))
    return store.rows(sql + " ORDER BY i.date DESC LIMIT 300")


@app.post("/api/inbox/fetch")
def fetch(body: dict = Body(default={})):
    try:
        return {"new": mailer.fetch(body.get("account"), int(body.get("days", 14)))}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, str(e))


@app.get("/api/inbox/{mid}")
def mail(mid: int):
    m = store.row("SELECT i.*, c.name company FROM inbox i LEFT JOIN companies c ON c.id=i.company_id WHERE i.id=?",
                  (mid,))
    if m and m["status"] == "new":
        store.execute("UPDATE inbox SET status='read' WHERE id=?", (mid,))
    return m


@app.post("/api/inbox/{mid}")
def update_mail(mid: int, body: dict = Body(...)):
    if "company_id" in body:
        store.execute("UPDATE inbox SET company_id=? WHERE id=?", (body["company_id"], mid))
    if "status" in body:
        store.execute("UPDATE inbox SET status=? WHERE id=?", (body["status"], mid))
    return {"ok": True}


# ---------------------------------------------------------------- agent chat
@app.get("/api/chats")
def chats():
    return store.rows("SELECT id,title,created_at,updated_at FROM chats ORDER BY updated_at DESC LIMIT 100")


@app.post("/api/chats")
def create_chat():
    return {"id": agent.new_chat()}


@app.get("/api/chats/{cid}")
def get_chat(cid: int):
    c = agent.load_chat(cid)
    if not c:
        raise HTTPException(404)
    return c


@app.delete("/api/chats/{cid}")
def delete_chat(cid: int):
    store.execute("DELETE FROM chats WHERE id=?", (cid,))
    return {"ok": True}


@app.post("/api/chats/{cid}/send")
def send(cid: int, body: dict = Body(...)):
    flag = threading.Event()
    STOP[cid] = flag

    def stream():
        for ev in agent.run(cid, body["text"], flag):
            yield f"data: {json.dumps(ev, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/chats/{cid}/stop")
def stop(cid: int):
    if cid in STOP:
        STOP[cid].set()
    return {"ok": True}


# ---------------------------------------------------------------- settings
@app.get("/api/settings")
def settings():
    s = agent.settings()
    return {"api_key_set": bool(agent.api_key()), "model": agent.MODEL, "accounts": mailer.accounts(),
            "default_account": mailer.default_account(), "provider": s["provider"], "lang": s["lang"],
            "cli_model": s["cli_model"], "openai": s["openai"], "presets": agent.OPENAI_PRESETS,
            "providers": agent.provider_status(),
            "openai_keys": {p: bool(agent.openai_key(p)) for p in agent.OPENAI_PRESETS},
            "owner": {k: store.owner().get(k) for k in ("name", "name_en", "short_name", "nickname", "avatar", "subtitle")}}


@app.post("/api/settings/agent")
def agent_settings(body: dict = Body(...)):
    for k in ("provider", "lang", "cli_model", "openai"):
        if k in body:
            store.set_setting(k, body[k])
    if body.get("openai_key"):
        agent.set_openai_key((body.get("openai") or agent.settings()["openai"]).get("preset", "custom"),
                             body["openai_key"])
    return {"ok": True, "providers": agent.provider_status()}


@app.post("/api/tool/{name}")
def call_tool(name: str, body: dict = Body(default={})):
    """Used by mcp_server.py so Claude CLI tool calls run inside this process (shared browser window)."""
    out, err = tools.run_tool(name, body)
    return {"content": out, "is_error": err}


@app.get("/api/knowledge")
def knowledge():
    return {"text": agent.KNOWLEDGE.read_text(encoding="utf-8") if agent.KNOWLEDGE.exists() else ""}


@app.put("/api/knowledge")
def save_knowledge(body: dict = Body(...)):
    agent.KNOWLEDGE.write_text(body["text"], encoding="utf-8")
    return {"ok": True}


@app.post("/api/sync")
def sync():
    """Refresh everything the agent and Claude Code sessions share: mail, follow-ups, documents."""
    out = {"mail": None, "errors": []}
    try:
        out["mail"] = mailer.fetch(None, 14)
    except Exception as e:  # noqa: BLE001
        out["errors"].append(f"mail: {e}")
    # register any PDFs/markdown files created outside the agent (e.g. by Claude Code) as documents
    known = {r["path"] for r in store.rows("SELECT path FROM documents")}
    added = 0
    for p in list((store.HOME / "outbox").rglob("*.md")) + list(tools.FINAL.glob("*.pdf")):
        if str(p) not in known and "sent" not in p.parts and "mail" not in p.parts:
            store.archive_document(p, "pdf" if p.suffix == ".pdf" else "note", None, p.stem, "ja", "draft", [],
                                   "" if p.suffix == ".pdf" else p.read_text(encoding="utf-8", errors="replace")[:20000])
            added += 1
    out["documents_added"] = added
    out["stats"] = store.stats()
    return out


@app.post("/api/settings/apikey")
def apikey(body: dict = Body(...)):
    agent.set_api_key(body["key"])
    return {"ok": True}


@app.post("/api/settings/mail/{acc}/password")
def mail_password(acc: str, body: dict = Body(...)):
    try:
        mailer.set_password(acc, body["password"])
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"登录失败：{e}")
    return {"ok": True}


@app.post("/api/settings/default_account")
def default_account(body: dict = Body(...)):
    store.set_setting("default_account", body["account"])
    return {"ok": True}


@app.post("/api/browser/open")
def browser_open(body: dict = Body(...)):
    snap = browser.open(body["url"])
    return {"title": snap["title"], "url": snap["url"]}
