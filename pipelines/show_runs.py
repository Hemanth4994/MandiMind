import duckdb
con = duckdb.connect("mandimind_weather.duckdb", read_only=True)
con.sql("""select run_id, pipeline_status, data_status, failed_checks, round(duration_s, 1) as secs
           from ops.pipeline_runs order by started_at""").show()