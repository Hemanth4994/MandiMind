"""health.py: the failure classes and the read-only queries the MCP tools call."""
import pytest

import health
from conftest import make_weather_db, rows, run_script


@pytest.mark.parametrize("error, failed, expected", [
    ("ReadTimeout: HTTPSConnectionPool: Read timed out. (read timeout=25)", "", "upstream_unavailable"),
    ("RuntimeError: mandi API returned HTTP 502", "", "upstream_unavailable"),
    ("ConnectionError: Connection reset", "no_nulls", "upstream_unavailable"),   # an unreachable source wins over old failed checks
    ("", "valid_temperature", "data_quality"),
    ("KeyError: 'daily'", "", "pipeline_error"),
    ("", "", "healthy"),
    (None, None, "healthy"),
])
def test_classify(error, failed, expected):
    assert health.classify(error, failed) == expected


@pytest.fixture
def db_with_a_bad_run(tmp_path, monkeypatch):
    path = make_weather_db(tmp_path)
    run_script("inject_fault.py", "nulls", cwd=tmp_path)
    run_script("run_all.py", "--no-ingest", cwd=tmp_path)
    monkeypatch.setattr(health, "DB", str(path))
    return path


def test_recent_runs_lists_both_sources_newest_first(db_with_a_bad_run):
    runs = health.recent_runs(10)
    assert {r["source"] for r in runs} == {"weather", "mandi"}
    assert all(set(r) >= {"run_id", "pipeline_status", "data_status", "failed_checks", "error"} for r in runs)


def test_failed_checks_names_the_failed_check(db_with_a_bad_run):
    failed = health.failed_checks()
    assert [f["check_name"] for f in failed] == ["no_nulls"]


def test_diagnose_run_gives_a_class_per_source(db_with_a_bad_run):
    run_id = health.recent_runs(1)[0]["run_id"]
    out = health.diagnose(run_id)
    by_source = {r["source"]: r["classification"] for r in out["runs"]}
    assert by_source == {"weather": "data_quality", "mandi": "healthy"}
    assert len(out["checks"]) == 5


def test_weather_returns_newest_days_first(db_with_a_bad_run):
    days = [w["date"] for w in health.weather(3)]
    assert days == sorted(days, reverse=True) and len(days) == 3


def test_queries_cannot_write(db_with_a_bad_run):
    """health opens the database read-only, so even a wrong query cannot change it."""
    import duckdb
    with pytest.raises(duckdb.Error):
        health._query("delete from ops.pipeline_runs")
    assert rows(db_with_a_bad_run, "select count(*) from ops.pipeline_runs")[0][0] == 2
