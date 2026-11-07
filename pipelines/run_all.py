import sys
import time
import uuid
from datetime import datetime
import duckdb
from weather_pipeline import pipeline, daily_weather
from quality import run_checks, DB

run_id = uuid.uuid4().hex[:8]
started = datetime.now()
t0 = time.time()
pipeline_status, error = "success", ""

if "--no-ingest" in sys.argv:
    pipeline_status = "skipped"
else:
    try:
        pipeline.run(daily_weather())
    except Exception as e:
        pipeline_status, error = "failed", f"{type(e).__name__}: {e}"[:300]

con = duckdb.connect(DB)
con.sql("create schema if not exists ops")
con.sql("""create table if not exists ops.pipeline_runs (
    run_id varchar, started_at timestamp, duration_s double,
    pipeline_status varchar, data_status varchar, failed_checks varchar, error varchar)""")

failed = []
try:
    results = run_checks(con, run_id)
    failed = [name for name, ok, _ in results if not ok]
    data_status = "ok" if not failed else "bad"
except Exception as e:
    data_status = "unknown"
    error = (error + " | checks: " + type(e).__name__)[:300]

con.execute("insert into ops.pipeline_runs values (?, ?, ?, ?, ?, ?, ?)",
            [run_id, started, time.time() - t0, pipeline_status, data_status, ",".join(failed), error])
print(f"\nrun {run_id}: pipeline={pipeline_status} data={data_status} failed={failed}")