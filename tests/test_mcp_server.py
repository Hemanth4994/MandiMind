"""Start the MCP server as a separate process and talk to it the way an MCP client does (over stdio)."""
import asyncio
import json
import os
import sys

import pytest

pytest.importorskip("mcp")
from mcp import ClientSession, StdioServerParameters          # noqa: E402
from mcp.client.stdio import stdio_client                       # noqa: E402

from conftest import PIPELINES, make_weather_db, run_script     # noqa: E402


def payload(result):
    """Each returned dict arrives as one JSON text item."""
    return [json.loads(item.text) for item in result.content]


async def talk(db_path):
    params = StdioServerParameters(command=sys.executable, args=[str(PIPELINES / "mcp_server.py")],
                                   env={**os.environ, "MANDIMIND_DB": str(db_path)})
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {t.name for t in (await session.list_tools()).tools}
            runs = await session.call_tool("get_recent_runs", {"limit": 5})
            failed = await session.call_tool("get_failed_checks", {})
            run_id = payload(runs)[0]["run_id"]
            diagnosis = await session.call_tool("diagnose_run", {"run_id": run_id})
            return tools, runs, payload(failed), diagnosis


def test_server_lists_four_tools_and_answers_from_the_database(tmp_path):
    path = make_weather_db(tmp_path)
    run_script("inject_fault.py", "spike", cwd=tmp_path)
    run_script("run_all.py", "--no-ingest", cwd=tmp_path)

    tools, runs, failed, diagnosis = asyncio.run(asyncio.wait_for(talk(path), timeout=90))

    assert tools == {"get_recent_runs", "get_failed_checks", "get_weather", "diagnose_run"}
    assert not runs.is_error and not diagnosis.is_error
    assert [f["check_name"] for f in failed] == ["valid_temperature"]
    by_source = {r["source"]: r["classification"] for r in payload(diagnosis)[0]["runs"]}
    assert by_source["weather"] == "data_quality"
