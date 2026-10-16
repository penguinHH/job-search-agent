"""python -m agent_app [--port 8765] [--no-browser] [--account <slug>]

Without JOBAGENT_HOME the app starts with the account picker. A small supervisor keeps running and starts
one server process at a time: the picker, or the agent for the chosen account (with JOBAGENT_HOME set to
that account's data folder). Opening an account or switching back to the picker ends the current process
with an exit code and the supervisor starts the next one on the same port.
With JOBAGENT_HOME set, the agent runs directly on that folder (no picker), as before.
"""
import argparse
import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn

OPEN_ACCOUNT, TO_PICKER = 3, 4


def serve(target: str, port: int):
    if target == "picker":
        uvicorn.run("agent_app.picker:app", host="127.0.0.1", port=port, log_level="warning")
    else:
        uvicorn.run("agent_app.server:app", host="127.0.0.1", port=port, log_level="warning")


def supervise(first: str, port: int):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import accounts
    target, fails = first, 0
    models = accounts.LEGACY / "data" / "models"           # embedding model files are not personal: share them
    while True:
        env = dict(os.environ, JOBAGENT_SUPERVISED="1")
        if target != "picker":
            env["JOBAGENT_HOME"] = str(accounts.home_of(target))
            env["JOBAGENT_ACCOUNT"] = target
            if models.exists():
                env.setdefault("JOBAGENT_MODELS", str(models))
        started = time.time()
        rc = subprocess.call([sys.executable, "-m", "agent_app", "--child", target, "--port", str(port)], env=env)
        if rc == OPEN_ACCOUNT:
            target, fails = accounts.last() or "picker", 0
        elif rc == TO_PICKER:
            target, fails = "picker", 0
        elif time.time() - started < 5 and fails < 5:      # port not released yet by the previous process
            fails += 1
            time.sleep(1)
        else:
            sys.exit(rc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--account", help="open this account directly instead of the picker")
    ap.add_argument("--child", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.child:
        return serve(a.child, a.port)
    url = f"http://127.0.0.1:{a.port}"
    if not a.no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    print(f"求职 Agent → {url}")
    if os.environ.get("JOBAGENT_HOME"):
        return serve("agent", a.port)
    supervise(a.account or "picker", a.port)


if __name__ == "__main__":
    main()
