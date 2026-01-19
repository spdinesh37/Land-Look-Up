import requests
import pandas as pd
import os
from sqlalchemy import create_engine, text

# API Configuration
BASE_URL = "https://data.wcad.org/api/v3/views/an3x-cnmw/query.json"
APP_TOKEN = "o9NY7r7FdFUFpFQQC9vAgy7Jx"

# MySQL Connection Info
MYSQL_USER = "root"        # change if needed
MYSQL_PASSWORD = "your_password"  # change to your MySQL password
MYSQL_HOST = "localhost"
MYSQL_PORT = "3306"
MYSQL_DB = "land_lookup"

# Create SQLAlchemy connection
engine = create_engine(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")

def fetch_and_store_data(batch_size=5000):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "X-App-Token": APP_TOKEN
    }

    offset = 0

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
            print("✅ All data fetched and stored.")
            break

        df = pd.DataFrame(data)
        df.to_sql("parcels", con=engine, if_exists="append", index=False)
        print(f"📦 Stored {len(df)} rows (offset={offset})")

        offset += batch_size

    print("✅ Data successfully saved to MySQL database!")

if __name__ == "__main__":
    fetch_and_store_data(batch_size=5000)
