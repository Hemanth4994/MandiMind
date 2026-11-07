import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("DATA_GOV_API_KEY")
rid = os.getenv("MANDI_RESOURCE_ID")
url = f"https://api.data.gov.in/resource/{rid}"
params = {"api-key": key, "format": "json", "limit": 5, "filters[state.keyword]": "Karnataka"}

for attempt in range(1, 5):
    start = time.time()
    try:
        r = requests.get(url, params=params, timeout=(10, 90))
        print(f"attempt {attempt}: status {r.status_code} in {time.time() - start:.1f}s")
        if r.status_code == 200:
            data = r.json()
            print("total:", data.get("total"), "| count:", data.get("count"))
            print(data.get("records", [])[:1])
            break
    except requests.exceptions.RequestException as e:
        print(f"attempt {attempt}: {type(e).__name__} after {time.time() - start:.1f}s")
    time.sleep(2 ** attempt)
else:
    print("gave up after 4 attempts")