"""Account picker: the small server that runs before an account is chosen.

It lists the accounts, runs the new-account guide, and on "open" exits with code 3 so the supervisor in
__main__ restarts the real server for the chosen account (each account runs in its own process, so no state
can leak from one account into another).
"""
import os
import sys
import threading
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import accounts  # noqa: E402

STATIC = Path(__file__).parent / "static"
app = FastAPI(title="求职 Agent · accounts")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
OPEN_ACCOUNT = 3


@app.get("/")
def index():
    v = int(max((STATIC / f).stat().st_mtime for f in ("accounts.js", "style.css")))
    html = (STATIC / "accounts.html").read_text(encoding="utf-8").replace(".css\"", f".css?v={v}\"").replace(
        ".js\"", f".js?v={v}\"")
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


@app.get("/api/accounts")
def list_accounts():
    return {"accounts": [{k: v for k, v in a.items() if k != "home"} for a in accounts.list_accounts()],
            "last": accounts.last()}


@app.post("/api/accounts")
def create(body: dict = Body(...)):
    try:
        return accounts.create(body)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/accounts/{slug}/open")
def open_account(slug: str):
    try:
        accounts.home_of(slug)
    except KeyError:
        raise HTTPException(404, "no such account")
    accounts.set_last(slug)
    threading.Timer(0.4, lambda: os._exit(OPEN_ACCOUNT)).start()
    return {"ok": True}
