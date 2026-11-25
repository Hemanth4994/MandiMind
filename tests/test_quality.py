"""The five weather checks, and whether each injected fault is caught by exactly the check meant to catch it."""
from datetime import date, timedelta

import duckdb
import pytest

from conftest import good_rows, make_weather_db, run_script
from quality import run_checks


def failed_names(path, run_id="t1"):
    con = duckdb.connect(str(path))
    try:
        return {name for name, ok, _ in run_checks(con, run_id) if not ok}
    finally:
        con.close()


def test_clean_data_passes_every_check(tmp_path):
    path = make_weather_db(tmp_path)
    assert failed_names(path) == set()


def test_results_are_recorded_with_the_run_id(tmp_path):
    path = make_weather_db(tmp_path)
    con = duckdb.connect(str(path))
    run_checks(con, "abc123")
    n, ids = con.sql("select count(*), count(distinct run_id) from ops.quality_checks").fetchone()
    con.close()
    assert (n, ids) == (5, 1)


# Each fault script changes one thing; exactly one check should notice.
@pytest.mark.parametrize("mode, expected", [
    ("gap", {"completeness"}),            # yesterday deleted
    ("spike", {"valid_temperature"}),     # today's temp_max_c = 99
    ("nulls", {"no_nulls"}),              # today's rain_mm is null
])
def test_injected_fault_is_caught_by_the_right_check(tmp_path, mode, expected):
    path = make_weather_db(tmp_path)
    result = run_script("inject_fault.py", mode, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert failed_names(path) == expected


def test_unknown_fault_mode_exits_with_usage(tmp_path):
    make_weather_db(tmp_path)
    result = run_script("inject_fault.py", "banana", cwd=tmp_path)
    assert result.returncode != 0
    assert "usage" in result.stderr


def test_stale_data_fails_freshness_and_completeness(tmp_path):
    today = date.today()
    old = [((today - timedelta(days=i)).isoformat(), 30.0, 20.0, 1.0, "bengaluru") for i in range(1, 9)]
    path = make_weather_db(tmp_path, old)
    assert failed_names(path) == {"freshness", "completeness"}


def test_minimum_above_maximum_is_invalid(tmp_path):
    rows = good_rows()
    rows[0] = (rows[0][0], 20.0, 25.0, 1.0, "bengaluru")
    path = make_weather_db(tmp_path, rows)
    assert failed_names(path) == {"valid_temperature"}


def test_negative_rain_is_invalid(tmp_path):
    rows = good_rows()
    rows[3] = (rows[3][0], 30.0, 20.0, -5.0, "bengaluru")
    path = make_weather_db(tmp_path, rows)
    assert failed_names(path) == {"valid_rain"}
