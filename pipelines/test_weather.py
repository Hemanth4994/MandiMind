import requests

url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 12.97, "longitude": 77.59,
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
    "past_days": 7, "timezone": "Asia/Kolkata",
}
r = requests.get(url, params=params, timeout=30)
print("status:", r.status_code)
d = r.json()["daily"]
for t, hi, lo, rain in zip(d["time"], d["temperature_2m_max"], d["temperature_2m_min"], d["precipitation_sum"]):
    print(t, hi, lo, rain)