"""Shared helpers: a tiny weather database shaped like the one dlt writes, and a way to run the real scripts in a scratch folder."""
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import duckdb

PIPELINES = Path(__file__).resolve().parent.parent / "pipelines"
DB_NAME = "mandimind_weather.duckdb"


def good_rows(days=8):
    """Today and the 7 days before it: warm, dry-ish, nothing missing."""
    today = date.today()
    return [((today - timedelta(days=i)).isoformat(), 30.0, 20.0, 1.0, "bengaluru") for i in range(days)]


def make_weather_db(folder, rows=None):
    """Create <folder>/mandimind_weather.duckdb with raw_weather.daily_weather (dlt stores the date as text)."""
    path = Path(folder) / DB_NAME
    con = duckdb.connect(str(path))
    con.sql("create schema raw_weather")
    con.sql("create table raw_weather.daily_weather "
            "(date varchar, temp_max_c double, temp_min_c double, rain_mm double, location varchar)")
    for row in (good_rows() if rows is None else rows):
        con.execute("insert into raw_weather.daily_weather values (?, ?, ?, ?, ?)", list(row))
    con.close()
    return path


def run_script(name, *args, cwd):
    """Run pipelines/<name> with `cwd` as the working folder (the scripts read and write the database in the current folder)."""
    env = {k: v for k, v in os.environ.items() if k not in ("DATA_GOV_API_KEY", "MANDI_RESOURCE_ID", "FAULT_MODE")}
    env["DLT_DATA_DIR"] = str(Path(cwd) / ".dlt_data")
    return subprocess.run([sys.executable, str(PIPELINES / name), *args], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=120)


def rows(path, sql):
    con = duckdb.connect(str(path), read_only=True)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()
