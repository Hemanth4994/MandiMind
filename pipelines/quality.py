from datetime import date, timedelta
import duckdb

con = duckdb.connect("mandimind_weather.duckdb")
con.sql("create schema if not exists ops")
con.sql("""create table if not exists ops.quality_checks (
    checked_at timestamp, check_name varchar, passed boolean, detail varchar)""")

def record(name, passed, detail):
    con.execute("insert into ops.quality_checks values (current_timestamp, ?, ?, ?)",
                [name, passed, detail])
    print("PASS" if passed else "FAIL", name, "-", detail)

def count(where):
    return con.sql(f"select count(*) from raw_weather.daily_weather where {where}").fetchone()[0]

today = date.today()
expected = {(today - timedelta(days=i)).isoformat() for i in range(8)}
have = {r[0] for r in con.sql("select date from raw_weather.daily_weather").fetchall()}
missing = sorted(expected - have)
latest = max(have) if have else None

record("freshness", latest == today.isoformat(), f"latest day = {latest}")
record("completeness", not missing, f"missing days = {missing}")
bad_t = count("temp_max_c > 55 or temp_min_c < -10 or temp_min_c > temp_max_c")
record("valid_temperature", bad_t == 0, f"{bad_t} bad rows")
bad_r = count("rain_mm < 0 or rain_mm > 500")
record("valid_rain", bad_r == 0, f"{bad_r} bad rows")
nulls = count("temp_max_c is null or temp_min_c is null or rain_mm is null")
record("no_nulls", nulls == 0, f"{nulls} rows with nulls")