import streamlit as st
from flight_api import search_multiple_origins
import pandas as pd
from datetime import time
from config import origins, origin_info, airline_names

st.title("Barcelona Flight Optimizer")

st.subheader("UC1: Search flights arriving in Barcelona")

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
    gif_placeholder = st.empty()
    gif_placeholder.image("data/YVPG.gif", width=120)
    st.write("Searching flights...")
    results = search_multiple_origins(origins, "BCN", str(date))
    gif_placeholder.empty()

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
            seg = offer["itineraries"][0]["segments"][0]
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
    st.success("Search completed!")


if "df" in st.session_state:
    df = st.session_state["df"].copy()

    
    df["dep_time"] = pd.to_datetime(df["departure"]).dt.time
    df["arr_time"] = pd.to_datetime(df["arrival"]).dt.time

    filtered = df[
        (df["dep_time"] >= dep_start) &
        (df["dep_time"] <= dep_end) &
        (df["arr_time"] >= arr_start) &
        (df["arr_time"] <= arr_end)
    ]

    st.subheader("Filtered Results")
    st.dataframe(filtered)

    
    cheapest = filtered[filtered["price"].notnull()]
    if len(cheapest) > 0:
        best = cheapest.sort_values("price").iloc[0]
        st.success(
            f"Cheapest flight is from **{best['origin']}** → BCN at **€{best['price']}**"
        )