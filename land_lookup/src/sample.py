import requests
import time
import json

# --- CONFIGURATION ---
URL = "https://data.wcad.org/resource/an3x-cnmw.json"
APP_TOKEN = "o9NY7r7FdFUFpFQQC9vAgy7Jx"  # <--- Paste your token inside these quotes
OUTPUT_FILE = "wcad_data.json"
LIMIT = 1000  # Max rows per request (usually 1000-2000 is safe)
# ---------------------

headers = {
    "X-App-Token": APP_TOKEN,
    "Accept": "application/json"
}

all_data = []
offset = 0
page_num = 1

print(f"Starting crawl with token... saving to {OUTPUT_FILE}")

while True:
    params = {
        "$select": "parcelid, ownernme1, cntassdval, pstlcity, siteaddress",  # Add/remove columns here
        "$limit": LIMIT,
        "$offset": offset,
        "$order": "parcelid"  # Keeps pagination stable
    }

    try:
        response = requests.get(URL, params=params, headers=headers)

        if response.status_code != 200:
            print(f"Error on page {page_num}: {response.text}")
            break

        data = response.json()

        if not data:
            print("✓ Finished! No more data found.")
            break

        all_data.extend(data)
        print(all_data)
        print(f"Page {page_num}: Got {len(data)} rows. (Total: {len(all_data)})")

        offset += LIMIT
        page_num += 1

        # Even with a token, a tiny sleep prevents connection resets
        time.sleep(0.2)

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        break

# --- SAVE TO FILE ---
print(f"Saving {len(all_data)} records to file...")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=4)

print("Done.")