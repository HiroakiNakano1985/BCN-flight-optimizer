import streamlit as st
from flight_api import search_multiple_origins
import pandas as pd
from datetime import time

st.title("Barcelona Flight Optimizer")

st.subheader("UC1: Search flights arriving in Barcelona")

date = st.date_input("Arrival date")

# departure time
dep_start, dep_end = st.slider(
    "Departure time range",
    min_value=time(0, 0),
    max_value=time(23, 59),
    value=(time(0, 0), time(23, 59))
)

# arrival time
arr_start, arr_end = st.slider(
    "Arrival time range",
    min_value=time(0, 0),
    max_value=time(23, 59),
    value=(time(0, 0), time(23, 59))
)

if st.button("Search"):
    st.write("Searching flights for:", date)

    origins = [
        "LIS", "CMN", "TUN", "CDG", "LON", "ZRH", "BRU", "AMS",
        "BER", "PRG", "WAW", "VIE", "LJU", "FCO", "BUD", "ZAG",
        "OTP", "SOF", "ATH", "IST", "NCE", "MAD"
    ]

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

        #time filter
        filtered = []
        for offer in offers:
            seg = offer["itineraries"][0]["segments"][0]
            dep_time = pd.to_datetime(seg["departure"]["at"]).time()
            arr_time = pd.to_datetime(seg["arrival"]["at"]).time()

            if dep_start <= dep_time <= dep_end and arr_start <= arr_time <= arr_end:
                filtered.append(offer)

        if len(filtered) == 0:
            rows.append({
                "origin": origin,
                "price": None,
                "airline": None,
                "duration": None,
                "departure": None,
                "arrival": None,
                "error": "No flights in selected time range"
            })
            continue

        
        cheapest = min(filtered, key=lambda x: float(x["price"]["grandTotal"]))

        rows.append({
            "origin": origin,
            "price": float(cheapest["price"]["grandTotal"]),
            "airline": cheapest["validatingAirlineCodes"][0],
            "duration": cheapest["itineraries"][0]["duration"],
            "departure": cheapest["itineraries"][0]["segments"][0]["departure"]["at"],
            "arrival": cheapest["itineraries"][0]["segments"][0]["arrival"]["at"],
            "error": None
        })

    df = pd.DataFrame(rows)

    st.subheader("Results")
    st.dataframe(df)

    cheapest_rows = df[df["price"].notnull()]
    if len(cheapest_rows) > 0:
        best = cheapest_rows.sort_values("price").iloc[0]
        st.success(
            f"Cheapest flight is from **{best['origin']}** → BCN at **€{best['price']}**"
        )