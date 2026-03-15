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

def search_multiple_legs(legs):
    total_price = 0
    detailed_results = []

    for leg in legs:
        origin = leg["origin"]
        destination = leg["destination"]
        date = leg["date"]

        flights = fetch_flights(origin, destination, date)

        # getting cheapest flight
        best_price = flights["price_min"]
        total_price += best_price

        detailed_results.append({
            "origin": origin,
            "destination": destination,
            "date": date,
            "best_price": best_price,
            "flights": flights
        })

        time.sleep(1.2)

    return {
        "total_price": total_price,
        "details": detailed_results
    }