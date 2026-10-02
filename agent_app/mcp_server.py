"""MCP server (stdio) exposing the agent's tools, so the Claude CLI (subscription) can drive them.

    claude -p "..." --mcp-config data/agent_mcp_config.json --allowedTools mcp__jobagent

Tool calls are forwarded to the running GUI process (POST /api/tool/<name>) so the browser window and
its form state persist across turns; if the GUI is not running they execute in this process.
"""
import asyncio
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mcp.types as types  # noqa: E402
from mcp.server.lowlevel import Server  # noqa: E402
from mcp.server.stdio import stdio_server  # noqa: E402

from agent_app.tools import TOOL_SCHEMAS, run_tool  # noqa: E402

GUI_URL = "http://127.0.0.1:8765/api/tool/"


def _call(name, arguments):
    try:
        req = urllib.request.Request(GUI_URL + name, data=json.dumps(arguments).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            d = json.loads(r.read())
            return d["content"], d["is_error"]
    except OSError:
        return run_tool(name, arguments)


async def list_tools(ctx, params) -> types.ListToolsResult:
    return types.ListToolsResult(tools=[types.Tool(name=t["name"], description=t["description"],
                                                   input_schema=t["input_schema"]) for t in TOOL_SCHEMAS])


async def call_tool(ctx, params: types.CallToolRequestParams) -> types.CallToolResult:
    # tools are synchronous (sqlite, requests, playwright) → run off the event loop
    out, is_err = await asyncio.to_thread(_call, params.name, params.arguments or {})
    return types.CallToolResult(content=[types.TextContent(type="text", text=out)], is_error=is_err)


server = Server("jobagent", on_list_tools=list_tools, on_call_tool=call_tool)


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
