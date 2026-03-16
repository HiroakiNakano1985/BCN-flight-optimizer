import pandas as pd
import re
from datetime import datetime

df = pd.read_csv("data/flights_bulk.csv")

# Convert duration (sec) to munites
df["duration_min"] = df["duration"] / 60


def parse_gf_datetime(text):
    # "7:00 AM on Thu, Mar 12" → "7:00 AM Thu Mar 12 2026"
    text = text.replace(" on ", " ")
    text = text + " 2026"

    return datetime.strptime(text, "%I:%M %p %a, %b %d %Y")

df["departure_dt"] = df["departure_time"].apply(parse_gf_datetime)
df["arrival_dt"] = df["arrival_time"].apply(parse_gf_datetime)


df["dep_date"] = df["departure_dt"].dt.date
df["dep_time"] = df["departure_dt"].dt.time
df["dep_minutes"] = df["departure_dt"].dt.hour * 60 + df["departure_dt"].dt.minute

df["arr_date"] = df["arrival_dt"].dt.date
df["arr_time"] = df["arrival_dt"].dt.time
df["arr_minutes"] = df["arrival_dt"].dt.hour * 60 + df["arrival_dt"].dt.minute


df["weekday"] = df["departure_dt"].dt.day_name()


df = df.drop(columns=["departure_time", "arrival_time"])


df.to_csv("flights_preprocessed.csv", index=False)