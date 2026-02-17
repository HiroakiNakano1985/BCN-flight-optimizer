from datetime import datetime, timedelta
from flight_api import search_flights
import time
import csv

def generate_dates(start_date, days=30):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

def collect_route_data(origin, destination, start_date, days=30):
    dates = generate_dates(start_date, days)
    all_results = []

    for date in dates:
        try:
            print(f"Fetching {origin} → {destination} on {date}")
            data = search_flights(origin, destination, date)

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
                     "departure": seg["departure"]["at"],
                     "arrival": seg["arrival"]["at"],
                     "error": None
                })


            time.sleep(1.2) 
        except Exception as e:
            print(f"Error on {origin}-{destination} {date}: {e}")

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

def collect_all_cities(origins, destination, start_date, days=30):
    all_data = []

    for origin in origins:
        route_data = collect_route_data(origin, destination, start_date, days)
        all_data.extend(route_data)

    save_to_csv(all_data, "bcn_flight_dataset.csv")
    print("Saved to bcn_flight_dataset.csv")
