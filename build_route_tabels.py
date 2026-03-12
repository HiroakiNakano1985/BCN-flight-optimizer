import pandas as pd

df = pd.read_csv("data/flights_preprocessed.csv")

df["route_weekday"] = df["origin"] + "_" + df["destination"] + "_" + df["weekday"]


route_stats = (
    df.groupby(["origin", "destination"])
      .agg(
          duration_min_median=("duration_min", "median"),
          dep_minutes_peak=("dep_minutes", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.median()),
          weekday_distribution=("weekday", lambda x: x.value_counts(normalize=True).to_dict())
      )
      .reset_index()
)

route_stats.to_parquet("data/route_stats.parquet")
print("Saved: route_stats.parquet")


airline_stats = (
    df.groupby(["origin", "destination"])["airline"]
      .apply(lambda x: x.value_counts().head(3).index.tolist())
      .reset_index(name="airlines_top3")
)

airline_stats.to_parquet("data/airline_stats.parquet")
print("Saved: airline_stats.parquet")


airport_graph = (
    df.groupby("origin")["destination"]
      .apply(lambda x: sorted(x.unique().tolist()))
      .reset_index(name="reachable_destinations")
)

airport_graph.to_parquet("data/airport_graph.parquet")
print("Saved: airport_graph.parquet")