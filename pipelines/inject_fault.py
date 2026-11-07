import sys
from datetime import date, timedelta
import duckdb

mode = sys.argv[1] if len(sys.argv) > 1 else ""
con = duckdb.connect("mandimind_weather.duckdb")
today = date.today().isoformat()
yesterday = (date.today() - timedelta(days=1)).isoformat()

if mode == "gap":
    con.execute("delete from raw_weather.daily_weather where date = ?", [yesterday])
elif mode == "spike":
    con.execute("update raw_weather.daily_weather set temp_max_c = 99 where date = ?", [today])
elif mode == "nulls":
    con.execute("update raw_weather.daily_weather set rain_mm = null where date = ?", [today])
else:
    sys.exit("usage: python pipelines/inject_fault.py gap|spike|nulls")
print("fault injected:", mode)