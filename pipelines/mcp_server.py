from mcp.server.fastmcp import FastMCP

import health

mcp = FastMCP("MandiMind Health")


@mcp.tool()
def get_recent_runs(limit: int = 10) -> list[dict]:
    """Recent pipeline runs, newest first, with pipeline status and data status."""
    return health.recent_runs(limit)


@mcp.tool()
def get_failed_checks(limit: int = 20) -> list[dict]:
    """Recent data quality checks that failed."""
    return health.failed_checks(limit)


@mcp.tool()
def get_weather(days: int = 8) -> list[dict]:
    """Stored daily weather rows, newest first."""
    return health.weather(days)


@mcp.tool()
def diagnose_run(run_id: str) -> dict:
    """Explain one run: statuses, error text, failed checks and a failure class."""
    return health.diagnose(run_id)


if __name__ == "__main__":
    mcp.run()