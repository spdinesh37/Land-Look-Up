import requests
import pandas as pd

BASE_URL = "https://data.wcad.org/resource/4kxj-e8c3.json"


def fetch_property_data(limit=1000, offset=0):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    params = {
        "$limit": limit,
        "$offset": offset,
        "$select": "propertyid,quickrefid,description,area,class,actyrbuilt,effyrbuilt,bedrooms,fireplace"
    }

    response = requests.get(BASE_URL, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)
    return df


if __name__ == "__main__":
    df = fetch_property_data(limit=1000)
    print(df.head())
    df.to_csv(r"C:\Users\dsripath\PycharmProjects\land_lookup\data\land_records_sample.csv", index=False)
    print("✅ Data saved to data/land_records_sample.csv")
