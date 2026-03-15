import json
import pandas as pd
import joblib
from datetime import datetime, timedelta

route_stats = pd.read_parquet("data/route_stats.parquet")
airline_stats = pd.read_parquet("data/airline_stats.parquet")
airport_graph = pd.read_parquet("data/airport_graph.parquet")
model = joblib.load("model.pkl")

def build_features(origin, destination, date):
    dt = pd.to_datetime(date)
    weekday = dt.day_name()
    route_weekday = f"{origin}_{destination}_{weekday}"

    row = route_stats[
        (route_stats["origin"] == origin) &
        (route_stats["destination"] == destination)
    ].iloc[0]

    duration_min = row["duration_min_median"]
    dep_minutes = row["dep_minutes_peak"]

    row_air = airline_stats[
        (airline_stats["origin"] == origin) &
        (airline_stats["destination"] == destination)
    ].iloc[0]

    airline = row_air["airlines_top3"][0]

    return {
        "origin": origin,
        "destination": destination,
        "airline": airline,
        "weekday": weekday,
        "route_weekday": route_weekday,
        "duration_min": duration_min,
        "dep_minutes": dep_minutes
    }

def build_route_features(origin, A, B, dateA, dateB, dateReturn):
    legs = [
        (origin, A, dateA),
        (A, B, dateB),
        (B, origin, dateReturn)
    ]

    features = [build_features(o, d, dt) for (o, d, dt) in legs]
    return pd.DataFrame(features)


def generate_dates(start_date, stayA, stayB):
    date_A = start_date
    date_B = date_A + timedelta(days=stayA)
    date_return = date_B + timedelta(days=stayB)
    return date_A, date_B, date_return

def predict_route_price(df_features):
    preds = model.predict(df_features)
    return preds.sum()

#test_response = {"origin": "BCN", "start_date": "2026-03-20",
#                 "end_date": "2026-03-30","num_cities": 2}

def find_best_routes(params):


    origin = params["origin"]
    start_date = pd.to_datetime(params["start_date"])
    end_date = pd.to_datetime(params["end_date"])
    num_cities = 2

    total_days = (end_date - start_date).days

    avg_stay = int(total_days / (num_cities))
    min_stay = max(2, avg_stay - 1)
    max_stay = avg_stay + 1

    stay_range = range(min_stay, max_stay + 1)



    reachable_origin = airport_graph.loc[
        airport_graph["origin"] == origin, "reachable_destinations"].iloc[0]

    results = []


    for A in reachable_origin:

        reachable_A = airport_graph.loc[
            airport_graph["origin"] == A, "reachable_destinations"].iloc[0]

        for B in reachable_A:

            reachable_B = airport_graph.loc[
                airport_graph["origin"] == B, "reachable_destinations"].iloc[0]

            if origin not in reachable_B:
                continue

            for stayA in stay_range:
                for stayB in stay_range:

                    dateA, dateB, dateReturn = generate_dates(start_date, stayA, stayB)

                    if dateReturn > end_date:
                        continue

                    df_feat = build_route_features(origin, A, B, dateA, dateB, dateReturn)
                    score = predict_route_price(df_feat)

                    legs = [
                            {"origin": origin, "destination": A, "date": dateA.date().isoformat()},
                            {"origin": A, "destination": B, "date": dateB.date().isoformat()},
                            {"origin": B, "destination": origin, "date": dateReturn.date().isoformat()}
                            ]

                    results.append({"legs": legs,"predicted_price": float(score)})


    results_sorted = sorted(results, key=lambda x: x["predicted_price"])
    return results_sorted[:5]

if __name__ == "__main__":
    test = {"origin": "BCN", "start_date": "2026-03-20", "end_date": "2026-03-30"}
    print(find_best_routes(test))
