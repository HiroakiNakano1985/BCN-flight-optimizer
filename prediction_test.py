import pandas as pd
import numpy as np
from datetime import datetime

# === 1. Parquet 読み込み ===
route_stats = pd.read_parquet("data/route_stats.parquet")
airline_stats = pd.read_parquet("data/airline_stats.parquet")
airport_graph = pd.read_parquet("data/airport_graph.parquet")

# === 2. ルート特徴量を生成する関数 ===
def build_features(origin, destination, date):
    
    dt = pd.to_datetime(date)
    weekday = dt.day_name()
    route_weekday = f"{origin}_{destination}_{weekday}"


    row = route_stats[
        (route_stats["origin"] == origin) &
        (route_stats["destination"] == destination)
    ]

    if len(row) == 0:
        raise ValueError(f"No route_stats found for {origin} → {destination}")

    duration_min = row["duration_min_median"].iloc[0]
    dep_minutes_peak = row["dep_minutes_peak"].iloc[0]

    # === airline を airline_stats から取得（top1 を使う） ===
    row_air = airline_stats[
        (airline_stats["origin"] == origin) &
        (airline_stats["destination"] == destination)
    ]

    if len(row_air) == 0:
        raise ValueError(f"No airline_stats found for {origin} → {destination}")

    airline = row_air["airlines_top3"].iloc[0][0] 

    
    X = pd.DataFrame([{
        "origin": origin,
        "destination": destination,
        "airline": airline,
        "weekday": weekday,
        "route_weekday": route_weekday,
        "duration_min": duration_min,
        "dep_minutes": dep_minutes_peak
    }])

    return X



import joblib
model = joblib.load("model.pkl")


origin = "BCN"
destination = "CDG"
date = "2026-03-20"

X_test = build_features(origin, destination, date)
pred_price = model.predict(X_test)[0]

print("=== Prediction Test ===")
print(X_test)
print(f"Predicted price: {pred_price:.2f} EUR")