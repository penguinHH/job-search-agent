"""The agent: one tool set, three interchangeable model back-ends, events streamed to the GUI.

Back-ends ("provider" setting):
  claude_api   Anthropic API (API key, pay per use) - manual streaming tool loop
  claude_cli   Claude Code CLI (`claude -p`, uses the user's Claude subscription); our tools are
               exposed to it through the MCP server in mcp_server.py
  openai       any OpenAI-compatible endpoint (NemoClaw-style: NVIDIA NIM, DeepSeek, OpenRouter, Ollama …)

Every chat keeps a provider-neutral display log (`events`) so the GUI can render history for all back-ends.
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import anthropic
import keyring
import requests

from . import store
from .tools import SEARCH_TOOL, SERVER_TOOLS, TOOL_SCHEMAS, run_tool

ROOT = store.ROOT
HOME = store.HOME
MODEL = "claude-opus-5-5"
KEYRING_API = ("jobsearch-anthropic", "api_key")
KEYRING_OPENAI = "jobsearch-openai"
KNOWLEDGE = HOME / "knowledge.md"          # shared with Claude Code sessions
MAX_STEPS = 40
HIDDEN_CLI_TOOLS = {"ToolSearch"}
LANG_NAME = {"zh": "Simplified Chinese", "ja": "Japanese", "en": "English"}

OPENAI_PRESETS = {
    "nvidia": {"label": "NVIDIA NIM（NemoClaw 风格）", "base_url": "https://integrate.api.nvidia.com/v1",
               "model": "nvidia/llama-3.3-nemotron-super-49b-v1"},
    "deepseek": {"label": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "openrouter": {"label": "OpenRouter", "base_url": "https://openrouter.ai/api/v1", "model": "deepseek/deepseek-chat"},
    "ollama": {"label": "Ollama（本地）", "base_url": "http://localhost:11434/v1", "model": "qwen3:14b"},
    "custom": {"label": "自定义", "base_url": "", "model": ""},
}

SYSTEM_RULES = """You are the job-search agent for {owner_name}.

# Who the user is
{owner_intro}
The profile is the ONLY source of facts about the user. Never invent experience,
numbers, dates or publications; if something is missing, ask_user and leave a visible placeholder.

# Languages
You are fluent in Chinese, Japanese and English. Talk to the user in {ui_lang}. Write company-facing text in
the company's language (Japanese by default, English for English-speaking companies), polite business style
(敬語 for Japanese), concrete facts from the profile.

# How to work
- Before applying, check the company record and its live careers page (fetch_url / web search): open roles,
  requirements, location, application channel. Prefer the official channel: ATS form > published recruiting
  e-mail > contact form. Record what you learn with score_company / save_document.
- Outward actions are gated: emails go through queue_email, and submit buttons in the browser are queued
  by browser_click. Tell the user what you queued; never claim something was sent until it is approved
  and executed. Logins, account creation, passwords and CAPTCHAs are always left to the user.
- After every application step call update_stage (drafted when prepared; sent only after the user
  approved/confirmed). When reading company replies (check_inbox / read_mail), summarise, update_stage
  replied/interview/rejected, and draft the reply with queue_email (in_reply_to).
- Keep answers short and structured: what you did, what is waiting for the user, next steps.
"""


# ---------------------------------------------------------------- settings
def settings():
    return {
        "provider": store.get_setting("provider", "claude_api"),
        "lang": store.get_setting("lang", "zh"),
        "cli_model": store.get_setting("cli_model", ""),
        "openai": store.get_setting("openai", {"preset": "deepseek", **OPENAI_PRESETS["deepseek"]}),
    }


def api_key():
    return os.environ.get("ANTHROPIC_API_KEY") or keyring.get_password(*KEYRING_API)


def set_api_key(key):
    keyring.set_password(*KEYRING_API, key.strip())


def openai_key(preset):
    return keyring.get_password(KEYRING_OPENAI, preset)


def set_openai_key(preset, key):
    keyring.set_password(KEYRING_OPENAI, preset, key.strip())


def claude_cli_path():
    p = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude.exe")
    return p if Path(p).exists() or shutil.which("claude") else None


def provider_status():
    s = settings()
    oa = s["openai"]
    return {
        "claude_api": {"ready": bool(api_key()), "detail": MODEL},
        "claude_cli": {"ready": bool(claude_cli_path()), "detail": claude_cli_path() or "未找到 claude CLI"},
        "openai": {"ready": bool(oa.get("base_url") and oa.get("model") and (openai_key(oa.get("preset", "custom"))
                                                                           or "localhost" in oa.get("base_url", ""))),
                   "detail": f"{oa.get('base_url')} · {oa.get('model')}"},
    }


def system_text():
    p = store.profile()
    s = store.stats()
    lang = LANG_NAME.get(settings()["lang"], "Simplified Chinese")
    know = KNOWLEDGE.read_text(encoding="utf-8") if KNOWLEDGE.exists() else ""
    o = store.owner()
    name = " / ".join(x for x in (o.get("name"), o.get("name_en"), o.get("nickname")) if x) or "the user"
    return (SYSTEM_RULES.replace("{ui_lang}", lang).replace("{owner_name}", name)
            .replace("{owner_intro}", o.get("agent_intro", "(see the profile below)"))
            + "\n# Shared knowledge (Claude Code sessions ⇄ agent)\n" + know
            + "\n# Candidate profile (profile.md)\n" + p["markdown"]
            + f"\n# Now\nToday is {datetime.now():%Y-%m-%d (%a) %H:%M}. Pipeline counts: "
              f"{json.dumps(s['pipeline'], ensure_ascii=False)}; follow-ups due: {len(s['followups_due'])}; "
              f"pending approvals: {s['pending_actions']}; unread job mail: {s['new_mail']}; "
              f"open questions: {s['open_questions']}.")


# ---------------------------------------------------------------- chat persistence
def new_chat(title="新对话"):
    return store.execute("INSERT INTO chats(title,messages,events,oa_messages,provider,updated_at) VALUES(?,?,?,?,?,?)",
                         (title, "[]", "[]", "[]", settings()["provider"], store.now()))


def load_chat(chat_id):
    c = store.row("SELECT * FROM chats WHERE id=?", (chat_id,))
    if not c:
        return None
    for k in ("messages", "events", "oa_messages"):
        c[k] = json.loads(c.get(k) or "[]")
    return c


def _save(chat_id, **fields):
    sets, vals = [], []
    for k, v in fields.items():
        sets.append(f"{k}=?")
        vals.append(json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v)
    store.execute(f"UPDATE chats SET {', '.join(sets)}, updated_at=? WHERE id=?", vals + [store.now(), chat_id])


class Recorder:
    """Folds streamed GUI events into a compact display log stored with the chat."""

    def __init__(self, chat_id, events):
        self.chat_id, self.events = chat_id, events

    def add(self, ev):
        t = ev["type"]
        if t == "text":
            if self.events and self.events[-1]["t"] == "text":
                self.events[-1]["text"] += ev["text"]
            else:
                self.events.append({"t": "text", "text": ev["text"]})
        elif t == "tool_use" and ev.get("id"):
            self.events.append({"t": "tool", "id": ev["id"], "name": ev["name"], "input": ev.get("input"),
                                "result": None, "err": False})
        elif t == "tool_result":
            for e in reversed(self.events):
                if e["t"] == "tool" and e.get("id") == ev["id"]:
                    e["result"], e["err"] = ev["content"][:3000], ev["is_error"]
                    break
        elif t == "error":
            self.events.append({"t": "error", "text": ev["text"]})

    def save(self):
        _save(self.chat_id, events=self.events)


def run(chat_id, user_text, stop_flag=None):
    """Generator of GUI events for one user turn, dispatched to the configured back-end."""
    chat = load_chat(chat_id)
    provider = settings()["provider"]
    rec = Recorder(chat_id, chat["events"])
    rec.events.append({"t": "user", "text": user_text, "provider": provider})
    if chat["title"] == "新对话":
        _save(chat_id, title=user_text[:24], provider=provider)
    rec.save()
    runner = {"claude_api": _run_claude_api, "claude_cli": _run_claude_cli, "openai": _run_openai}[provider]
    yield {"type": "provider", "provider": provider}
    try:
        for ev in runner(chat, user_text, stop_flag):
            rec.add(ev)
            if ev["type"] in ("turn_end", "tool_result"):
                rec.save()
            yield ev
    except Exception as e:  # noqa: BLE001
        ev = {"type": "error", "text": f"{type(e).__name__}: {e}"}
        rec.add(ev)
        yield ev
    rec.save()
    yield {"type": "done"}


def _run_tools(calls, stop_flag):
    """calls: [(id, name, input)] → yields events, returns results via list."""
    for cid, name, args in calls:
        yield {"type": "tool_use", "id": cid, "name": name, "input": args}
        out, err = run_tool(name, args) if isinstance(args, dict) else ("invalid tool input", True)
        yield {"type": "tool_result", "id": cid, "name": name, "content": out, "is_error": err}


# ---------------------------------------------------------------- 1) Anthropic API
def _run_claude_api(chat, user_text, stop_flag):
    key = api_key()
    if not key:
        raise RuntimeError("还没有设置 Anthropic API key（设置 → 模型后端）")
    cl = anthropic.Anthropic(api_key=key)
    messages = chat["messages"]
    if messages and messages[-1]["role"] == "user" and isinstance(messages[-1]["content"], str):
        user_text = messages.pop()["content"] + "\n\n" + user_text      # previous turn never answered
    messages.append({"role": "user", "content": user_text})
    _save(chat["id"], messages=messages)
    system = [{"type": "text", "text": system_text(), "cache_control": {"type": "ephemeral"}}]
    for _ in range(MAX_STEPS):
        if stop_flag and stop_flag.is_set():
            yield {"type": "error", "text": "已停止"}
            return
        with cl.messages.stream(model=MODEL, max_tokens=32000, system=system, messages=messages,
                                tools=TOOL_SCHEMAS + SERVER_TOOLS,
                                thinking={"type": "adaptive", "display": "summarized"}) as stream:
            for ev in stream:
                if stop_flag and stop_flag.is_set():
                    break
                if ev.type == "content_block_start" and ev.content_block.type == "server_tool_use":
                    yield {"type": "tool_use", "name": ev.content_block.name, "server": True}
                elif ev.type == "content_block_start" and ev.content_block.type == "thinking":
                    yield {"type": "thinking_start"}
                elif ev.type == "content_block_delta":
                    if ev.delta.type == "text_delta":
                        yield {"type": "text", "text": ev.delta.text}
                    elif ev.delta.type == "thinking_delta":
                        yield {"type": "thinking", "text": ev.delta.thinking}
            resp = stream.get_final_message()
        messages.append({"role": "assistant", "content": [b.model_dump(exclude_none=True) for b in resp.content]})
        _save(chat["id"], messages=messages)
        yield {"type": "turn_end"}
        if resp.stop_reason == "pause_turn":
            continue
        tool_uses = [b for b in resp.content if b.type == "tool_use"]
        if not tool_uses or resp.stop_reason in ("end_turn", "refusal"):
            return
        if resp.stop_reason == "max_tokens":
            raise RuntimeError("工具输入被截断")
        results = []
        for ev in _run_tools([(t.id, t.name, t.input) for t in tool_uses], stop_flag):
            yield ev
            if ev["type"] == "tool_result":
                results.append({"type": "tool_result", "tool_use_id": ev["id"], "content": ev["content"][:60000],
                                **({"is_error": True} if ev["is_error"] else {})})
        messages.append({"role": "user", "content": results})
        _save(chat["id"], messages=messages)


# ---------------------------------------------------------------- 2) Claude CLI (subscription)
def _run_claude_cli(chat, user_text, stop_flag):
    exe = claude_cli_path()
    if not exe:
        raise RuntimeError("没有找到 claude CLI（请先安装 Claude Code 并登录订阅账户）")
    sysfile = HOME / "data" / "agent_system_prompt.md"
    sysfile.write_text(system_text(), encoding="utf-8")
    cfg = HOME / "data" / "agent_mcp_config.json"
    cfg.write_text(json.dumps({"mcpServers": {"jobagent": {
        "command": sys.executable, "args": [str(Path(__file__).parent / "mcp_server.py")]}}}),
        encoding="utf-8")
    cmd = [exe, "-p", "--output-format", "stream-json", "--verbose", "--include-partial-messages",
           "--mcp-config", str(cfg), "--strict-mcp-config",
           "--allowedTools", "mcp__jobagent", "WebSearch", "WebFetch",
           "--append-system-prompt-file", str(sysfile)]
    if chat.get("session_id"):
        cmd += ["--resume", chat["session_id"]]
    if settings()["cli_model"]:
        cmd += ["--model", settings()["cli_model"]]
    env = {**os.environ}
    env.pop("ANTHROPIC_API_KEY", None)              # make sure the subscription login is used
    proc = subprocess.Popen(cmd, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8", errors="replace", env=env,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    proc.stdin.write(user_text)
    proc.stdin.close()
    names = {}
    try:
        for line in proc.stdout:
            if stop_flag and stop_flag.is_set():
                proc.kill()
                yield {"type": "error", "text": "已停止"}
                return
            line = line.strip()
            if not line.startswith("{"):
                continue
            msg = json.loads(line)
            t = msg.get("type")
            if t == "system" and msg.get("subtype") == "init":
                _save(chat["id"], session_id=msg.get("session_id"))
            elif t == "stream_event":
                ev = msg.get("event", {})
                if ev.get("type") == "content_block_delta":
                    d = ev.get("delta", {})
                    if d.get("type") == "text_delta":
                        yield {"type": "text", "text": d.get("text", "")}
                    elif d.get("type") == "thinking_delta":
                        yield {"type": "thinking", "text": d.get("thinking", "")}
                elif ev.get("type") == "content_block_start" and ev.get("content_block", {}).get("type") == "thinking":
                    yield {"type": "thinking_start"}
            elif t == "assistant":
                for b in msg.get("message", {}).get("content", []):
                    if b.get("type") == "tool_use":
                        name = b["name"].replace("mcp__jobagent__", "")
                        names[b["id"]] = name
                        if name in HIDDEN_CLI_TOOLS:       # CLI-internal plumbing, not interesting to show
                            continue
                        yield {"type": "tool_use", "id": b["id"], "name": name, "input": b.get("input")}
                yield {"type": "turn_end"}
            elif t == "user":
                content = msg.get("message", {}).get("content", [])
                for b in content if isinstance(content, list) else []:
                    if b.get("type") == "tool_result" and names.get(b.get("tool_use_id")) not in HIDDEN_CLI_TOOLS:
                        c = b.get("content")
                        if isinstance(c, list):
                            c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
                        yield {"type": "tool_result", "id": b.get("tool_use_id"),
                               "name": names.get(b.get("tool_use_id"), ""), "content": str(c or ""),
                               "is_error": bool(b.get("is_error"))}
            elif t == "result":
                if msg.get("session_id"):
                    _save(chat["id"], session_id=msg["session_id"])
                if msg.get("is_error"):
                    yield {"type": "error", "text": str(msg.get("result") or msg.get("subtype"))}
        proc.wait(timeout=30)
        if proc.returncode not in (0, None):
            err = proc.stderr.read()[-1500:]
            if err.strip():
                yield {"type": "error", "text": f"claude CLI 退出码 {proc.returncode}: {err}"}
    finally:
        if proc.poll() is None:
            proc.kill()


# ---------------------------------------------------------------- 3) OpenAI-compatible (NemoClaw-style)
def _oa_tools():
    return [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                              "parameters": t["input_schema"]}} for t in TOOL_SCHEMAS + [SEARCH_TOOL]]


def _run_openai(chat, user_text, stop_flag):
    oa = settings()["openai"]
    base, model = oa.get("base_url", "").rstrip("/"), oa.get("model")
    key = openai_key(oa.get("preset", "custom")) or ("ollama" if "localhost" in base else None)
    if not (base and model and key):
        raise RuntimeError("OpenAI 兼容后端没有配置完整（设置 → 模型后端：接口地址、模型名、API key）")
    msgs = chat["oa_messages"]
    msgs.append({"role": "user", "content": user_text})
    _save(chat["id"], oa_messages=msgs)
    for _ in range(MAX_STEPS):
        if stop_flag and stop_flag.is_set():
            yield {"type": "error", "text": "已停止"}
            return
        body = {"model": model, "stream": True, "tools": _oa_tools(), "temperature": 0.4,
                "messages": [{"role": "system", "content": system_text()}] + msgs}
        r = requests.post(f"{base}/chat/completions", json=body, stream=True, timeout=300,
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:800]}")
        text, calls, thinking_started = "", {}, False
        for raw in r.iter_lines(decode_unicode=True):
            if stop_flag and stop_flag.is_set():
                break
            if not raw or not raw.startswith("data:"):
                continue
            data = raw[5:].strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            if not chunk.get("choices"):
                continue
            delta = chunk["choices"][0].get("delta", {})
            rc = delta.get("reasoning_content") or delta.get("reasoning")
            if rc:
                if not thinking_started:
                    thinking_started = True
                    yield {"type": "thinking_start"}
                yield {"type": "thinking", "text": rc}
            if delta.get("content"):
                text += delta["content"]
                yield {"type": "text", "text": delta["content"]}
            for tc in delta.get("tool_calls") or []:
                c = calls.setdefault(tc.get("index", 0), {"id": "", "name": "", "args": ""})
                c["id"] = tc.get("id") or c["id"]
                fn = tc.get("function") or {}
                c["name"] += fn.get("name") or ""
                c["args"] += fn.get("arguments") or ""
        assistant = {"role": "assistant", "content": text or None}
        if calls:
            assistant["tool_calls"] = [{"id": c["id"] or f"call_{i}", "type": "function",
                                        "function": {"name": c["name"], "arguments": c["args"] or "{}"}}
                                       for i, c in sorted(calls.items())]
        msgs.append(assistant)
        _save(chat["id"], oa_messages=msgs)
        yield {"type": "turn_end"}
        if not calls:
            return
        parsed = []
        for tc in assistant["tool_calls"]:
            try:
                args = json.loads(tc["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = None
            parsed.append((tc["id"], tc["function"]["name"], args))
        for ev in _run_tools(parsed, stop_flag):
            yield ev
            if ev["type"] == "tool_result":
                msgs.append({"role": "tool", "tool_call_id": ev["id"], "content": ev["content"][:30000]})
        _save(chat["id"], oa_messages=msgs)
