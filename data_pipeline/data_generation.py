from datetime import datetime, timedelta
from flight_api import search_flights
import time
import csv

def safe_search_flights(origin, destination, date, max_retries=7):
    retry = 0

    while True:
        try:
            return search_flights(origin, destination, date)

        except Exception as e:
            msg = str(e).lower()

            # rate limit(401)
            if "401" in msg or "unauthorized" in msg:
                wait = min(120, 2 ** retry)
                print(f"[AUTH ERROR / 401] Waiting {wait} sec before retry...")
                time.sleep(wait)
                retry += 1
                continue

            # rate limit（429）
            if "429" in msg or "rate" in msg:
                wait = min(120, 2 ** retry)  # waiting 120 sec in error 429
                print(f"[RATE LIMIT] Waiting {wait} sec...")
                time.sleep(wait)
                retry += 1
                continue

            # server error（500 or 503）
            if "500" in msg or "503" in msg:
                wait = min(60, 2 ** retry) # waiting 60 sec in error 500 or 503
                print(f"[SERVER ERROR] Waiting {wait} sec...")
                time.sleep(wait)
                retry += 1
                continue

            print(f"[UNEXPECTED ERROR] {e}")
            return None

def generate_dates(start_date, days=30):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

def collect_route_data(origin, destination, start_date, days=30):
    dates = generate_dates(start_date, days)
    all_results = []

    for date in dates:
        print(f"Fetching {origin} → {destination} on {date}")
            
        data = safe_search_flights(origin, destination, date)

        if not data:
            print(f"No data for {date}")
            continue

        offers = data.get("data", [])
        for offer in offers:
            seg = offer["itineraries"][0]["segments"][0]

            all_results.append({
                "origin": origin,
                "destination": destination,
                "date": date,
                "price": float(offer["price"]["grandTotal"]),
                "airline": offer["validatingAirlineCodes"][0],
                "duration": offer["itineraries"][0]["duration"],
                "departure_time": seg["departure"]["at"],
                "arrival_time": seg["arrival"]["at"],
                "error": None
                })


        time.sleep(1.5) 
        
    return all_results

def save_to_csv(data, filename="flight_data.csv"):
    if not data:
        print("No data to save")
        return
    keys = data[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
