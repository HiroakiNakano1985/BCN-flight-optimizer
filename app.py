import streamlit as st
from flight_api import search_multiple_origins
import pandas as pd
from datetime import time
from config import origins, origin_info, airline_names

def format_duration(iso_duration):
    hours = 0
    minutes = 0

    if "H" in iso_duration:
        hours = int(iso_duration.split("T")[1].split("H")[0])
    if "M" in iso_duration:
        minutes = int(iso_duration.split("H")[-1].replace("M", ""))

    return f"{hours}:{minutes:02d}"

def highlight_cheapest(row):
    if row["is_cheapest"]:
        return ["background-color: #d1ffd1"] * len(row)
    return [""] * len(row)


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
    gif_placeholder.markdown(
        """
        <div style='text-align:center;'>
            <img src='data/YVPG.gif' width='120'>
            <p>Searching flights...</p>
        </div>
        """,
        unsafe_allow_html=True)

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
    st.success("Search completed!")


if "df" in st.session_state:
    df = st.session_state["df"].copy()

    df["City"] = df["origin"].apply(lambda x: origin_info[x][0])
    df["Country"] = df["origin"].apply(lambda x: origin_info[x][1])
    df["AirlineName"] = df["airline"].apply(lambda x: airline_names.get(x, "Unknown"))
    df["Duration"] = df["duration"].apply(format_duration)

    

    
    df["dep_time"] = pd.to_datetime(df["departure"]).dt.time
    df["arr_time"] = pd.to_datetime(df["arrival"]).dt.time

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
        "price","dep_time", "arr_time", "Duration",
        "is_cheapest"]]



    st.subheader("Filtered Results")
    st.dataframe(filtered.style.apply(highlight_cheapest, axis=1))

    cheapest = filtered[filtered["price"].notnull()]
    if len(cheapest) > 0:
        best = cheapest.sort_values("price").iloc[0]
        st.success(
            f"Cheapest flight is from **{best['origin']}** → BCN at **€{best['price']}**"
        )