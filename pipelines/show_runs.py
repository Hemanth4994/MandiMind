import duckdb

con = duckdb.connect("mandimind_weather.duckdb", read_only=True)
con.sql("""select run_id, source, pipeline_status, data_status, failed_checks,
           substr(error, 1, 70) as error
           from ops.pipeline_runs order by started_at desc limit 10""").show(max_width=200)