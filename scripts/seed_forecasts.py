import requests
from datetime import datetime, timedelta

BASE = "http://localhost:8000/api/v1/forecasts"
PLANTS = ["TR_001", "BG_001", "ES_001"]
start = datetime(2025, 11, 14, 0, 0)

payloads = []
for hour in range(24):
    ts = (start + timedelta(hours=hour)).isoformat() + "Z"
    payloads.extend([
        {"plant_id": "TR_001", "forecast_timestamp": ts, "estimated_production_mwh": 50 + hour * 0.5},
        {"plant_id": "BG_001", "forecast_timestamp": ts, "estimated_production_mwh": 30 + hour * 0.3},
        {"plant_id": "ES_001", "forecast_timestamp": ts, "estimated_production_mwh": 20 + hour * 0.2},
    ])

print(f"Posting {len(payloads)} forecasts to {BASE} ...")

for p in payloads:
    r = requests.put(BASE + "/", json=p)
    status = "OK" if r.status_code in (200, 201) else f"Failed: {r.status_code}"
    print(status, p["plant_id"], p["forecast_timestamp"], "->", r.json().get("id") if r.ok else r.text)

print("Done. Test data loaded.")