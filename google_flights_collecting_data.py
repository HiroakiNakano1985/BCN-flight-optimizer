import requests
import json
import csv
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from config import origins as CONFIG_ORIGINS
import streamlit as st

load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY") or st.secrets["RAPIDAPI_KEY"]

DAYS = 30

SINGLE_ROUTE = False

ORIGIN_OVERRIDE = "BCN"
DEST_OVERRIDE = "FRA"

OUTPUT_CSV = "flights_bulk.csv"
CHECKPOINT_FILE = "checkpoint.txt"

def normalize_airline(name: str) -> str:
    if not name:
        return None
    name = name.replace("|", ",")
    first = name.split(",")[0].strip()
    if "Operated by" in first:
        first = first.split("Operated by")[0].strip()
    return first

def load_checkpoint():
    if not os.path.exists(CHECKPOINT_FILE):
        return None
    with open(CHECKPOINT_FILE, "r") as f:
        return f.read().strip()

def save_checkpoint(origin, destination, date):
    with open(CHECKPOINT_FILE, "w") as f:
        f.write(f"{origin},{destination},{date}")


def init_csv():
    if not os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "origin", "destination", "date", "price", "airline",
                "duration", "segments", "departure_time", "arrival_time"
            ])


def append_csv(row):
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def fetch_flights(origin, destination, date):
    url = "https://google-flights-live-api.p.rapidapi.com/api/google_flights/oneway/v1"

    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "google-flights-live-api.p.rapidapi.com"
    }

    payload = {
        "departure_date": date,
        "from_airport": origin,
        "to_airport": destination
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            print(f"API error {response.status_code} for {origin}->{destination} {date}")
            return None
        return response.json()
    except Exception as e:
        print(f"Exception for {origin}->{destination} {date}: {e}")
        return None


def main():
    init_csv()

    if SINGLE_ROUTE:
        origins = [ORIGIN_OVERRIDE]
        destinations = [DEST_OVERRIDE]
    else:
        origins = CONFIG_ORIGINS
        destinations = CONFIG_ORIGINS

    start_date = datetime(2026,3,12)
    checkpoint = load_checkpoint()
    skip = True if checkpoint else False

    if checkpoint:
        cp_origin, cp_dest, cp_date = checkpoint.split(",")
        print(f"Resuming from checkpoint: {checkpoint}")

    for origin in origins:
        for destination in destinations:
            if origin == destination:
                continue

            for i in range(DAYS):
                date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                
                if skip:
                    if (origin == cp_origin and
                        destination == cp_dest and
                        date == cp_date):
                        skip = False
                    else:
                        continue
                print(f"Fetching {origin} → {destination} on {date}")

                flights = fetch_flights(origin, destination, date)
                if flights is None:
                    print("Error fetching data, saving checkpoint…")
                    save_checkpoint(origin, destination, date)
                    continue

                for f in flights:
                    row = [
                        origin,
                        destination,
                        date,
                        f.get("price_as_number"),
                        normalize_airline(f.get("airline")),
                        f.get("duration_seconds"),
                        f.get("stops"),
                        f.get("departure_description"),
                        f.get("arrival_description")
                    ]
                    append_csv(row)
                save_checkpoint(origin, destination, date)

    print("All data collected.")


if __name__ == "__main__":
    main()