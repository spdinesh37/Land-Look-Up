# extract_data.py
import requests
import pandas as pd
from sqlalchemy import create_engine, text

# MySQL connection
username = 'root'
password = 'mysql1'
host = 'localhost'
port = 3306
database = 'land_lookup'

# WCAD API
BASE_URL = "https://data.wcad.org/api/v3/views/an3x-cnmw/query.json"
APP_TOKEN = "o9NY7r7FdFUFpFQQC9vAgy7Jx"
BATCH_SIZE = 5000  # fetch 5000 rows for now

try:
    engine = create_engine(f'mysql+pymysql://{username}:{password}@{host}:{port}/{database}')
    connection = engine.connect()
    print("✅ Connected to MySQL database!")

    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "X-App-Token": APP_TOKEN}
    params = {"$limit": BATCH_SIZE, "$offset": 0}

    print("Fetching data from WCAD API...")
    response = requests.get(BASE_URL, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    print(f"Fetched {len(data)} rows.")

    if not data:
        print("No data returned from API.")
    else:
        # Only extract required fields from JSON to avoid duplicates
        cleaned_data = []
        for row in data:
            cleaned_row = {
                "propertyid": row.get(":id"),            # use API row ID as primary key
                "quickrefid": row.get("parcelid"),       # example mapping
                "description": row.get("usedscrp"),
                "area": row.get("assessedacres"),
                "class": row.get("usecd"),
                "actyrbuilt": row.get("resyrblt"),
                "effyrbuilt": None,
                "bedrooms": None,
                "fireplace": None
            }
            # Skip rows without propertyid
            if cleaned_row["propertyid"] is not None:
                cleaned_data.append(cleaned_row)

        print(f"Rows after cleaning: {len(cleaned_data)}")

        # Insert into MySQL
        with engine.begin() as conn:
            for row in cleaned_data:
                # Convert NaN or empty strings to None
                for k, v in row.items():
                    if pd.isna(v) or v == "":
                        row[k] = None
                try:
                    conn.execute(
                        text("""INSERT IGNORE INTO parcels
                                (propertyid, quickrefid, description, area, class, actyrbuilt, effyrbuilt, bedrooms, fireplace)
                                VALUES (:propertyid, :quickrefid, :description, :area, :class, :actyrbuilt, :effyrbuilt, :bedrooms, :fireplace)"""),
                        row
                    )
                except Exception as e:
                    print("Error inserting row:", e)

        print("✅ Data inserted into parcels table!")

    connection.close()
    print("Connection closed.")

except Exception as e:
    print("Error:", e)
