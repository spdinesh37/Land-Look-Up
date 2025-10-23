import requests
import pandas as pd
import os

BASE_URL = "https://data.wcad.org/api/v3/views/an3x-cnmw/query.json"
APP_TOKEN = "o9NY7r7FdFUFpFQQC9vAgy7Jx"
CSV_FILE = r"E:\UAB\Land-Look-Up\land_lookup\data\land_records_sample.csv"

def fetch_data_incrementally(batch_size=5000):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "X-App-Token": APP_TOKEN
    }

    offset = 0
    first_batch = True

    while True:
        params = {
            "$limit": batch_size,
            "$offset": offset,
            "$select": "propertyid,quickrefid,description,area,class,actyrbuilt,effyrbuilt,bedrooms,fireplace"
        }

        response = requests.get(BASE_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:
            print("✅ All data fetched.")
            break

        df = pd.DataFrame(data)
        # If first batch, write header; otherwise append without header
        if first_batch:
            df.to_csv(CSV_FILE, index=False, mode='w')
            first_batch = False
        else:
            df.to_csv(CSV_FILE, index=False, mode='a', header=False)

        print(f"Fetched {len(data)} rows (offset={offset})")
        offset += batch_size

    print(f"✅ Data saved to {CSV_FILE}")

if __name__ == "__main__":
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    fetch_data_incrementally(batch_size=5000)
