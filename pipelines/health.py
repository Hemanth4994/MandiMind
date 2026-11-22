import os
from pathlib import Path

import duckdb

DB = os.getenv(
    "MANDIMIND_DB",
    str(Path(__file__).resolve().parent.parent / "data" / "mandimind_weather.duckdb"),
)


def _query(sql, params=None):
    con = duckdb.connect(DB, read_only=True)
    try:
        cur = con.execute(sql, params or [])
        cols = [c[0] for c in cur.description]
        return [
            {c: (v if isinstance(v, (int, float, bool, type(None))) else str(v))
             for c, v in zip(cols, row)}
            for row in cur.fetchall()
        ]
    finally:
        con.close()


def recent_runs(limit: int = 10):
    return _query(
        "select run_id, source, started_at, pipeline_status, data_status, "
        "failed_checks, substr(error, 1, 200) as error "
        "from ops.pipeline_runs order by started_at desc limit ?", [limit])


def failed_checks(limit: int = 20):
    return _query(
        "select run_id, checked_at, check_name, detail "
        "from ops.quality_checks where not passed order by checked_at desc limit ?", [limit])


def weather(days: int = 8):
    return _query(
        "select date, temp_max_c, temp_min_c, rain_mm "
        "from raw_weather.daily_weather order by date desc limit ?", [days])


def classify(error, failed):
    e = (error or "").lower()
    if "timed out" in e or "502" in e or "connection" in e:
        return "upstream_unavailable"
    if failed:
        return "data_quality"
    if e:
        return "pipeline_error"
    return "healthy"


def diagnose(run_id: str):
    runs = _query(
        "select source, pipeline_status, data_status, failed_checks, error "
        "from ops.pipeline_runs where run_id = ?", [run_id])
    for r in runs:
        r["classification"] = classify(r["error"], r["failed_checks"])
    checks = _query(
        "select check_name, passed, detail from ops.quality_checks where run_id = ?", [run_id])
    return {"run_id": run_id, "runs": runs, "checks": checks}