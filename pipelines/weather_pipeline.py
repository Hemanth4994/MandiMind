import dlt
import requests

@dlt.resource(name="daily_weather", write_disposition="merge", primary_key="date")
def daily_weather(latitude=12.97, longitude=77.59, past_days=7):
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude, "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "past_days": past_days, "forecast_days": 1,
            "timezone": "Asia/Kolkata",
        },
        timeout=30,
    )
    r.raise_for_status()
    d = r.json()["daily"]
    for i, day in enumerate(d["time"]):
        yield {
            "date": day,
            "temp_max_c": d["temperature_2m_max"][i],
            "temp_min_c": d["temperature_2m_min"][i],
            "rain_mm": d["precipitation_sum"][i],
            "location": "bengaluru",
        }

pipeline = dlt.pipeline(
    pipeline_name="mandimind_weather",
    destination="duckdb",
    dataset_name="raw_weather",
)

if __name__ == "__main__":
    print(pipeline.run(daily_weather()))