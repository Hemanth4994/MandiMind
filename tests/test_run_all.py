"""run_all.py with ingestion skipped: it should still check the stored data and record one row per source."""
from conftest import make_weather_db, rows, run_script


def test_each_run_records_one_row_per_source_with_two_separate_statuses(tmp_path):
    path = make_weather_db(tmp_path)
    result = run_script("run_all.py", "--no-ingest", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    runs = rows(path, "select source, pipeline_status, data_status, failed_checks, run_id "
                      "from ops.pipeline_runs order by source")
    assert [(r[0], r[1], r[2], r[3]) for r in runs] == [
        ("mandi", "skipped", "not_checked", ""),
        ("weather", "skipped", "ok", ""),
    ]
    assert len({r[4] for r in runs}) == 1          # both rows belong to the same run


def test_bad_data_is_reported_even_though_nothing_failed(tmp_path):
    """The pipeline status and the data status are different columns: here nothing ran, yet the data is bad."""
    path = make_weather_db(tmp_path)
    assert run_script("inject_fault.py", "spike", cwd=tmp_path).returncode == 0
    assert run_script("run_all.py", "--no-ingest", cwd=tmp_path).returncode == 0
    weather = rows(path, "select pipeline_status, data_status, failed_checks from ops.pipeline_runs where source = 'weather'")
    assert weather == [("skipped", "bad", "valid_temperature")]


def test_history_accumulates_across_runs(tmp_path):
    path = make_weather_db(tmp_path)
    for _ in range(2):
        assert run_script("run_all.py", "--no-ingest", cwd=tmp_path).returncode == 0
    n_runs, n_ids = rows(path, "select count(*), count(distinct run_id) from ops.pipeline_runs")[0]
    assert (n_runs, n_ids) == (4, 2)
