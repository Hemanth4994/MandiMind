import os
import dlt
import requests
from dotenv import load_dotenv

load_dotenv()


@dlt.resource(name="mandi_prices", write_disposition="append")
def mandi_prices(limit=500):
    rid = os.getenv("MANDI_RESOURCE_ID")
    r = requests.get(
        f"https://api.data.gov.in/resource/{rid}",
        params={"api-key": os.getenv("DATA_GOV_API_KEY"), "format": "json", "limit": limit},
        timeout=(10, 25),
    )
    if r.status_code != 200:
        raise RuntimeError(f"mandi API returned HTTP {r.status_code}")
    for record in r.json().get("records", []):
        yield record


mandi_pipeline = dlt.pipeline(
    pipeline_name="mandimind_mandi",
    destination=dlt.destinations.duckdb("mandimind_weather.duckdb"),
    dataset_name="raw_mandi",
)