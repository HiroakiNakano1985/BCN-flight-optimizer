import streamlit as st
from flight_api import search_multiple_origins
import pandas as pd
from datetime import time
from config import origins, origin_info, airline_names
import pickle

with open("model.pkl", "rb") as f:
    model = pickle.load(f)

def highlight_cheapest(row):
    if row["is_cheapest"]:
        return ["background-color: #d1ffd1"] * len(row)
    return [""] * len(row)

st.set_page_config(
    page_title="Barcelona Flight Optimizer",
    page_icon="✈️",
    layout="wide"
)

st.markdown("""
<style>

html, body, [data-testid="stAppViewContainer"] {
    background-color: #f5f7fa !important;
}

/* title */
h1 {
    color: #1a3c8b !important;
    font-weight: 700 !important;
}

/* subtitle */
h2, h3 {
    color: #2b4c9a !important;
}

/* button */
.stButton>button {
    background-color: #1a73e8 !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.2rem !important;
    font-size: 1.1rem !important;
}

</style>
""", unsafe_allow_html=True)

st.title("Barcelona Flight Optimizer")
st.subheader("Search flights arriving in Barcelona")

# date
date = st.date_input("Arrival date")

dep_start, dep_end = st.slider(
    "Departure time range",
    min_value=time(0, 0),
    max_value=time(23, 59),
    value=(time(0, 0), time(23, 59))
)

arr_start, arr_end = st.slider(
    "Arrival time range",
    min_value=time(0, 0),
    max_value=time(23, 59),
    value=(time(0, 0), time(23, 59))
)


if st.button("Search"):
    status = st.info("Searching flights...")
    results = search_multiple_origins(origins, "BCN", str(date))

    rows = []
    for r in results:
        origin = r["origin"]

        if "error" in r:
            rows.append({
                "origin": origin,
                "price": None,
                "airline": None,
                "duration": None,
                "departure": None,
                "arrival": None,
                "error": r["error"]
            })
            continue

        offers = r["data"]["data"]

        for offer in offers:
            segments = offer["itineraries"][0]["segments"]
            if len(segments) !=1:
                continue
            seg = segments[0]
            rows.append({
                "origin": origin,
                "price": float(offer["price"]["grandTotal"]),
                "airline": offer["validatingAirlineCodes"][0],
                "duration": offer["itineraries"][0]["duration"],
                "departure": seg["departure"]["at"],
                "arrival": seg["arrival"]["at"],
                "error": None
            })

    
    st.session_state["df"] = pd.DataFrame(rows)
    status.empty()
    st.success("Search completed!")


if "df" in st.session_state:
    df = st.session_state["df"].copy()

    df["City"] = df["origin"].apply(lambda x: origin_info[x][0])
    df["Country"] = df["origin"].apply(lambda x: origin_info[x][1])
    df["AirlineName"] = df["airline"].apply(lambda x: airline_names.get(x, "Unknown"))
    df["dep_time"] = pd.to_datetime(df["departure"]).dt.time
    df["arr_time"] = pd.to_datetime(df["arrival"]).dt.time
    df["hours"] = df["duration"].str.extract(r"(\d+)H").fillna(0).astype(int)
    df["minutes"] = df["duration"].str.extract(r"(\d+)M").fillna(0).astype(int)
    df["duration(min)"] = df["hours"] * 60 + df["minutes"]
    df["duration"] = df["hours"].astype(str) + ":" + df["minutes"].astype(str).str.zfill(2)

    df = df.drop(columns=["hours", "minutes"])
    df["departure_dt"] = pd.to_datetime(df["departure"])
    df["dep_minutes"] = df["departure_dt"].dt.hour * 60 + df["departure_dt"].dt.minute
    df["weekday"] = df["departure_dt"].dt.day_name()
    df["route_weekday"] = df["origin"] + "_" + df["weekday"]


    filtered = df[
        (df["dep_time"] >= dep_start) &
        (df["dep_time"] <= dep_end) &
        (df["arr_time"] >= arr_start) &
        (df["arr_time"] <= arr_end)
    ].copy()

    filtered["is_cheapest"] = filtered.groupby("origin")["price"].transform(
    lambda x: x == x.min())
    
    filtered = filtered[[
        "origin", "City", "Country",
        "airline", "AirlineName",
        "price","dep_time", "arr_time", "duration",
        "is_cheapest"]]



    st.subheader("Filtered Results")
    st.dataframe(filtered.style.apply(highlight_cheapest, axis=1))

    cheapest = filtered[filtered["price"].notnull()]
    if len(cheapest) > 0:
        best = cheapest.sort_values("price").iloc[0]
        st.success(f"Cheapest flight is from **{best['origin']}** → BCN at **€{best['price']}**")
    
    cheapest_by_city = (filtered.groupby(["origin", "City", "Country"])["price"]
                .min().reset_index().sort_values("price")
                .head(10).set_index("City"))

    st.subheader("Cheapest Price by City (Top 10 Cheapest)")
    st.bar_chart(cheapest_by_city["price"])


    avg_price = (filtered.groupby(["origin", "City", "Country"])["price"]
                 .mean().reset_index()
                 .sort_values("price").head(10)
                 .set_index("City"))
    
    
    st.subheader("Average Price by City (Top 10 Cheapest)")
    st.bar_chart(avg_price["price"])

    df_pred = df.copy()
    df_pred["pred_price"] = model.predict(df_pred[["origin",
                                                   "airline",
                                                   "weekday",
                                                   "route_weekday",
                                                   "duration(min)",
                                                   "dep_minutes"]])
    
    df_pred["diff"] = df_pred["pred_price"] - df_pred["price"]

    
    cheap = df_pred[df_pred["diff"] > 20].copy()
    cheap["City"] = cheap["origin"].apply(lambda x: origin_info[x][0])
    cheap["Country"] = cheap["origin"].apply(lambda x: origin_info[x][1])
    cheap["AirlineName"] = cheap["airline"].apply(lambda x: airline_names.get(x, "Unknown"))
    cheap["dep_time"] = pd.to_datetime(cheap["departure"]).dt.time
    cheap["arr_time"] = pd.to_datetime(cheap["arrival"]).dt.time
    cheap["diff"] = cheap["diff"].round(2)
    cheap["pred_price"] = cheap["pred_price"].round(2)


# filtered と同じ列順に並べる
    cheap_display = cheap[["origin", "City", "Country",
                           "airline", "AirlineName",
                           "price", "pred_price", "diff",
                           "dep_time", "arr_time", "duration"
                           ]].sort_values("diff", ascending=False)



    st.subheader("🔥 Flight Tickets cheaper than predicted by 20 EURs")

    if len(cheap_display) == 0:
        st.info("No significantly cheap flights found on selected date.")
    else:
        st.dataframe(cheap_display)