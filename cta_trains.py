import os
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CTA_API_KEY")

API_URL = "http://lapi.transitchicago.com/api/1.0/ttpositions.aspx"
ROUTES = "Red,Blue,Brn,G,Org,P,Pink,Y"
DB_FILE = "cta_trains.db"


def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS train_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_number TEXT,
            route TEXT,
            destination TEXT,
            next_station_id TEXT,
            next_station_name TEXT,
            is_approaching INTEGER,
            is_delayed INTEGER,
            lat REAL,
            lon REAL,
            heading INTEGER,
            predicted_arrival TEXT,
            fetched_at TEXT
        )
    """)
    conn.commit()


def fetch_positions():
    params = {
        "key": API_KEY,
        "rt": ROUTES,
        "outputType": "JSON"
    }
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    return response.json()


def load_to_db(conn, data):
    fetched_at = datetime.now().isoformat()
    trains = []

    for route in data["ctatt"]["route"]:
        route_name = route["@name"]
        for train in route.get("train", []):
            trains.append((
                train.get("rn"),
                route_name,
                train.get("destNm"),
                train.get("nextStaId"),
                train.get("nextStaNm"),
                int(train.get("isApp", 0)),
                int(train.get("isDly", 0)),
                float(train.get("lat", 0)),
                float(train.get("lon", 0)),
                int(train.get("heading", 0)),
                train.get("arrT"),
                fetched_at,
            ))

    conn.executemany("""
        INSERT INTO train_positions
            (run_number, route, destination, next_station_id, next_station_name,
             is_approaching, is_delayed, lat, lon, heading, predicted_arrival, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, trains)
    conn.commit()
    return len(trains)


def main():
    conn = sqlite3.connect(DB_FILE)
    init_db(conn)

    print("Fetching train positions...")
    data = fetch_positions()

    count = load_to_db(conn, data)
    print(f"Loaded {count} trains into {DB_FILE}")

    conn.close()


if __name__ == "__main__":
    main()
