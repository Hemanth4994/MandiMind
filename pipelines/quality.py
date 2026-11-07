from datetime import date, timedelta
import duckdb

DB = "mandimind_weather.duckdb"

def run_checks(con, run_id=None):
    con.sql("create schema if not exists ops")
    con.sql("""create table if not exists ops.quality_checks (
        checked_at timestamp, check_name varchar, passed boolean, detail varchar)""")
    con.sql("alter table ops.quality_checks add column if not exists run_id varchar")
    results = []

    def record(name, passed, detail):
        con.execute(
            "insert into ops.quality_checks (checked_at, check_name, passed, detail, run_id) "
            "values (current_timestamp, ?, ?, ?, ?)", [name, passed, detail, run_id])
        results.append((name, passed, detail))
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
    return results

if __name__ == "__main__":
    run_checks(duckdb.connect(DB))