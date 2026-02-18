import pandas as pd

df = pd.read_csv("data/bcn_flight_dataset_full.csv")


# Change Duration format
df["duration"] = df["duration"].str.replace("PT", "", regex=False)

df["hours"] = df["duration"].str.extract(r"(\d+)H").fillna(0).astype(int)
df["minutes"] = df["duration"].str.extract(r"(\d+)M").fillna(0).astype(int)
df["duration(min)"] = df["hours"] * 60 + df["minutes"]
df["duration"] = df["hours"].astype(str) + ":" + df["minutes"].astype(str).str.zfill(2)

df = df.drop(columns=["hours", "minutes"])


# Change departure and arrival format
df["departure_dt"] = pd.to_datetime(df["departure"])
df["dep_date"] = df["departure_dt"].dt.date.astype(str)
df["dep_time"] = df["departure_dt"].dt.strftime("%H:%M")
df["dep_minutes"] = df["departure_dt"].dt.hour * 60 + df["departure_dt"].dt.minute

df["arrival_dt"] = pd.to_datetime(df["arrival"])
df["arr_date"] = df["arrival_dt"].dt.date.astype(str)
df["arr_time"] = df["arrival_dt"].dt.strftime("%H:%M")
df["arr_minutes"] = df["arrival_dt"].dt.hour * 60 + df["arrival_dt"].dt.minute

# Adding weekday
df["weekday"] = df["departure_dt"].dt.day_name()

df.to_csv("data/bcn_flight_dataset_preprocessed.csv", index=False)
