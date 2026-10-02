"""Open-model back-end (DeepSeek / OpenRouter / NVIDIA NIM / Ollama …) on the OpenAI Agents SDK.

The SDK runs the agent loop (multi-turn tool calls, streaming, retries via the OpenAI client); this module only
- exposes the agent's own tools (tools.TOOL_SCHEMAS + search_web) as SDK FunctionTools, executed in-process so
  the browser / approval queue are shared with the GUI,
- trims the history before every model call so long chats do not overflow the context window,
- bridges the SDK's async event stream to the GUI's synchronous event generator.
"""
import asyncio
import json
import queue
import threading

from agents import (Agent, FunctionTool, ModelSettings, OpenAIChatCompletionsModel, RunConfig, Runner,
                    set_tracing_disabled)
from agents.run_config import ModelInputData
from openai import AsyncOpenAI

from .tools import SEARCH_TOOL, TOOL_SCHEMAS, run_tool

set_tracing_disabled(True)          # never send traces anywhere

MAX_TURNS = 40
HISTORY_BUDGET = 120_000            # characters of history sent per model call (≈ 30–60k tokens)
OLD_TOOL_OUTPUT_CHARS = 1_500       # older tool outputs are shortened to this before whole turns are dropped
TOOL_OUTPUT_CHARS = 30_000


# ---------------------------------------------------------------- tools
def _make_tools(errors):
    def make(schema):
        async def invoke(ctx, args_json):
            try:
                args = json.loads(args_json or "{}")
            except json.JSONDecodeError:
                errors[ctx.tool_call_id] = True
                return "invalid JSON arguments - call the tool again with valid JSON"
            out, err = await asyncio.to_thread(run_tool, schema["name"], args)
            errors[ctx.tool_call_id] = err
            return out[:TOOL_OUTPUT_CHARS]
        return FunctionTool(name=schema["name"], description=schema["description"],
                            params_json_schema=schema["input_schema"], on_invoke_tool=invoke,
                            strict_json_schema=False)
    return [make(s) for s in TOOL_SCHEMAS + [SEARCH_TOOL]]


# ---------------------------------------------------------------- history
def _size(item):
    return len(json.dumps(item, ensure_ascii=False, default=str))


def _is_user(item):
    return isinstance(item, dict) and item.get("role") == "user"


def trim_history(items, budget=HISTORY_BUDGET):
    """Keep the request under `budget` characters: shorten old tool outputs, then drop the oldest whole turns
    (a turn starts at a user message, so a tool call is never separated from its output)."""
    items = list(items)
    if sum(map(_size, items)) <= budget:
        return items
    starts = [i for i, it in enumerate(items) if _is_user(it)] or [0]
    last = starts[-1]
    for i, it in enumerate(items[:last]):
        if isinstance(it, dict) and it.get("type") == "function_call_output":
            out = str(it.get("output", ""))
            if len(out) > OLD_TOOL_OUTPUT_CHARS:
                items[i] = {**it, "output": out[:OLD_TOOL_OUTPUT_CHARS] + " …[truncated]"}
    for s in starts:
        if sum(map(_size, items[s:])) <= budget or s == last:
            if s:
                note = {"role": "user", "content": "[Earlier conversation omitted to fit the context window.]"}
                return [note] + items[s:]
            return items[s:]
    return items[last:]


def migrate(messages):
    """Chats saved by the old hand-written loop used chat-completions messages; keep their text turns."""
    out = []
    for m in messages or []:
        if not isinstance(m, dict):
            continue
        if "type" in m or (m.get("role") in ("user", "assistant") and "tool_calls" not in m):
            if m.get("role") == "assistant" and not m.get("content") and "type" not in m:
                continue
            out.append(m)
    return out


def _filter(data):
    return ModelInputData(input=trim_history(data.model_data.input), instructions=data.model_data.instructions)


# ---------------------------------------------------------------- run
def run(history, user_text, system, cfg, key, stop_flag=None, on_history=None):
    """Synchronous generator of GUI events. `history` is the stored SDK input list; `on_history(items)` is
    called with the new list after the run (also after errors / stop)."""
    q = queue.Queue()
    END = object()
    errors = {}

    async def main():
        client = AsyncOpenAI(base_url=cfg["base_url"], api_key=key, max_retries=4, timeout=300)
        model = OpenAIChatCompletionsModel(model=cfg["model"], openai_client=client)
        agent = Agent(name="job-agent", instructions=system, model=model, tools=_make_tools(errors),
                      model_settings=ModelSettings(temperature=0.4))
        items = migrate(history) + [{"role": "user", "content": user_text}]
        result = Runner.run_streamed(agent, items, max_turns=MAX_TURNS,
                                     run_config=RunConfig(tracing_disabled=True, call_model_input_filter=_filter))
        thinking = False
        try:
            async for ev in result.stream_events():
                if stop_flag is not None and stop_flag.is_set():
                    result.cancel()
                    q.put({"type": "error", "text": "已停止"})
                    break
                if ev.type == "raw_response_event":
                    t = getattr(ev.data, "type", "")
                    if t == "response.output_text.delta":
                        q.put({"type": "text", "text": ev.data.delta})
                    elif t in ("response.reasoning_text.delta", "response.reasoning_summary_text.delta"):
                        if not thinking:
                            thinking = True
                            q.put({"type": "thinking_start"})
                        q.put({"type": "thinking", "text": ev.data.delta})
                elif ev.type == "run_item_stream_event":
                    raw = ev.item.raw_item
                    if ev.name == "tool_called":
                        try:
                            args = json.loads(getattr(raw, "arguments", "") or "{}")
                        except json.JSONDecodeError:
                            args = getattr(raw, "arguments", "")
                        q.put({"type": "tool_use", "id": raw.call_id, "name": raw.name, "input": args})
                    elif ev.name == "tool_output":
                        cid = raw["call_id"] if isinstance(raw, dict) else raw.call_id
                        q.put({"type": "tool_result", "id": cid, "name": "", "content": str(ev.item.output),
                               "is_error": bool(errors.get(cid))})
                    elif ev.name == "message_output_created":
                        q.put({"type": "turn_end"})
        finally:
            if on_history:
                try:
                    on_history(result.to_input_list())
                except Exception:  # noqa: BLE001 - keep the old history if the run broke early
                    pass

    def worker():
        try:
            asyncio.run(main())
        except Exception as e:  # noqa: BLE001 - surfaced in the GUI
            q.put({"type": "error", "text": f"{type(e).__name__}: {e}"})
        finally:
            q.put(END)

    threading.Thread(target=worker, daemon=True).start()
    while True:
        ev = q.get()
        if ev is END:
            return
        yield ev
