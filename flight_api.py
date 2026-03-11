import os
import json
import requests
from dotenv import load_dotenv
import time

load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

URL = "https://google-flights-live-api.p.rapidapi.com/api/google_flights/oneway/v1"

HEADERS = {
    "Content-Type": "application/json",
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "google-flights-live-api.p.rapidapi.com"
}

def fetch_flights(origin, destination, date):
    payload = {
        "departure_date": date,
        "from_airport": origin,
        "to_airport": destination
    }
    response = requests.post(URL, headers=HEADERS, data=json.dumps(payload))
    response.raise_for_status()
    raw = response.json()
    return raw


def search_multiple_origins(origins, destination, date):
    results = []
    for origin in origins:
        flights = fetch_flights(origin, destination, date)
        results.append({
            "origin": origin,
            "destination": destination,
            "data": flights
        })
        time.sleep(1.2)
    return results