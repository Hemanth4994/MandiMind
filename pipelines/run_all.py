import os
import sys
import time
import uuid
from datetime import datetime
import duckdb
from weather_pipeline import pipeline as weather_pipeline, daily_weather
from mandi_pipeline import mandi_pipeline, mandi_prices
from quality import run_checks, DB

run_id = uuid.uuid4().hex[:8]
skip_ingest = "--no-ingest" in sys.argv
secret = os.getenv("DATA_GOV_API_KEY") or "<none>"


def clean(text):
    return str(text).replace(secret, "***")[:300]


def ingest(pipeline, resource):
    if skip_ingest:
        return "skipped", ""
    try:
        pipeline.run(resource)
        return "success", ""
    except Exception as e:
        root = getattr(e, "exception", None) or e
        return "failed", clean(f"{type(root).__name__}: {root}")


runs = []
for source, pipe, res in [
    ("weather", weather_pipeline, daily_weather()),
    ("mandi", mandi_pipeline, mandi_prices()),
]:
    started, t0 = datetime.now(), time.time()
    status, error = ingest(pipe, res)
    runs.append((source, started, time.time() - t0, status, error))

con = duckdb.connect(DB)
con.sql("create schema if not exists ops")
con.sql("""create table if not exists ops.pipeline_runs (
    run_id varchar, started_at timestamp, duration_s double,
    pipeline_status varchar, data_status varchar, failed_checks varchar, error varchar)""")
con.sql("alter table ops.pipeline_runs add column if not exists source varchar")

failed, data_status = [], "unknown"
try:
    results = run_checks(con, run_id)
    failed = [name for name, ok, _ in results if not ok]
    data_status = "ok" if not failed else "bad"
except Exception as e:
    print("checks crashed:", type(e).__name__)

for source, started, secs, status, error in runs:
    ds, fc = (data_status, failed) if source == "weather" else ("not_checked", [])
    con.execute(
        "insert into ops.pipeline_runs (run_id, started_at, duration_s, pipeline_status, "
        "data_status, failed_checks, error, source) values (?, ?, ?, ?, ?, ?, ?, ?)",
        [run_id, started, secs, status, ds, ",".join(fc), error, source])
    print(f"{source}: pipeline={status} data={ds} failed={fc} {error}")