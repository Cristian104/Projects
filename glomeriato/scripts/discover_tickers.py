import requests
import base64
import json
import os
from app.core.config import settings

def discover():
    # Auth Setup
    credentials = f"{settings.T212_API_KEY}:{settings.T212_SECRET_KEY}"
    encoded = base64.b64encode(credentials.encode()).decode()
    headers = {"Authorization": f"Basic {encoded}"}

    print(f"🔍 Connecting to {settings.T212_BASE_URL}...")
    res = requests.get(f"{settings.T212_BASE_URL}/equity/metadata/instruments", headers=headers)
    
    if res.status_code != 200:
        print(f"❌ Failed to fetch metadata: {res.status_code}")
        return

    instruments = res.json()
    
    # Load your 180+ targets
    with open("app/data/targets.json", "r") as f:
        targets = json.load(f)

    ticker_map = {}
    print(f"🛰️ Scanning {len(instruments)} T212 instruments for {len(targets)} targets...")

    for target in targets:
        # Clean the Yahoo suffix for matching (e.g., SAP.DE -> SAP)
        base_ticker = target.split('.')[0]
        
        for inst in instruments:
            # Match base ticker (e.g., SAP) and ensure it's an Equity (_EQ)
            if inst['ticker'].startswith(base_ticker) and "_EQ" in inst['ticker']:
                ticker_map[target] = inst['ticker']
                break 

    # Save the map
    with open("app/data/ticker_map.json", "w") as f:
        json.dump(ticker_map, f, indent=2)
    
    print(f"✅ Success! Created app/data/ticker_map.json with {len(ticker_map)} valid mappings.")

if __name__ == "__main__":
    discover()
