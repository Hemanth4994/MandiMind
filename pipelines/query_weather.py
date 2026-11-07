import sys
import duckdb

db = sys.argv[1] if len(sys.argv) > 1 else "mandimind_weather.duckdb"
schema = sys.argv[2] if len(sys.argv) > 2 else "raw_weather"
con = duckdb.connect(db)
con.sql(f"select count(*) as n, min(date) as first_day, max(date) as last_day from {schema}.daily_weather").show()
con.sql(f"select load_id, status, inserted_at from {schema}._dlt_loads order by inserted_at").show()