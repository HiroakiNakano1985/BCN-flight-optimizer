from data_pipeline.data_generation import collect_route_data, save_to_csv
import os
import csv

# 21 cities incl. BCN
origins = [
    "LIS", "CMN", "TUN", "CDG", "LON", "ZRH", "BRU", "AMS",
    "BER", "PRG", "WAW", "VIE", "LJU", "FCO", "BUD", "ZAG",
    "OTP", "SOF", "ATH", "IST", "NCE", "MAD", "BCN"]

start_date = "2026-03-12"
days=30

checkpoint_file = "checkpoint.txt"
output_file = "all_routes_dataset.csv"

# loading checkpoint
def load_checkpoint():
    try:
        with open(checkpoint_file, "r") as f:
            line = f.read().strip()
            if line:
                origin, destination = line.split(",")
                return origin, destination
    except FileNotFoundError:
        pass
    return None, None

# saving checkpoint
def save_checkpoint(origin, destination):
    with open(checkpoint_file, "w") as f:
        f.write(f"{origin},{destination}")

def init_csv_if_needed():
    if not os.path.exists(output_file):
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "origin", "destination", "date", "price", "airline",
                "duration", "segments", "departure_time", "arrival_time"
            ])

def append_to_csv(rows):
    with open(output_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "origin", "destination", "date", "price", "airline",
            "duration", "segments", "departure_time", "arrival_time", "error"
        ])
        for row in rows:
            writer.writerow(row)




# main procedure
init_csv_if_needed()

last_origin, last_destination = load_checkpoint()
skip = True if last_origin else False

for origin in origins:
    for destination in origins:
        if origin == destination:
            continue
        
        if skip:
            if origin == last_origin and destination == last_destination:
                skip = False
            continue


        print(f"{origin} -> {destination}")
        route_data = collect_route_data(origin, destination, start_date, days)
        if len(route_data) == 0:
            print("⚠️ route_data is EMPTY")
        else:
            print("route_data length:", len(route_data))
            print("sample row:", route_data[0])
        append_to_csv(route_data)
        
        save_checkpoint(origin,destination)

print("saved to all_routes_dataset.csv")