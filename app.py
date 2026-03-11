import streamlit as st
from flight_api import search_multiple_origins
import pandas as pd
from datetime import time
from config import origins, origin_info, airline_names
import pickle

@st.cache_resource
def load_model():
    with open("model.pkl", "rb") as f:
        return pickle.load(f)

model = load_model()

def highlight_cheapest(row):
    if row["is_cheapest"]:
        return ["background-color: #d1ffd1"] * len(row)
    return [""] * len(row)

st.set_page_config(
    page_title="Cheap Flight Explorer",
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

    df_pred = df.copy()
    df_pred["pred_price"] = model.predict(df_pred[[
        "origin", "airline", "weekday", "route_weekday", "duration(min)", "dep_minutes"
    ]])
    df_pred["diff"] = df_pred["pred_price"] - df_pred["price"]

    cheap_display = df_pred.copy()
    cheap_display["City"] = cheap_display["origin"].apply(lambda x: origin_info[x][0])
    cheap_display["Country"] = cheap_display["origin"].apply(lambda x: origin_info[x][1])
    cheap_display["AirlineName"] = cheap_display["airline"].apply(lambda x: airline_names.get(x, "Unknown"))
    cheap_display["dep_time"] = pd.to_datetime(cheap_display["departure"]).dt.time
    cheap_display["arr_time"] = pd.to_datetime(cheap_display["arrival"]).dt.time
    cheap_display["diff"] = cheap_display["diff"].round(2)
    cheap_display["pred_price"] = cheap_display["pred_price"].round(2)


tab1, tab2, tab3 = st.tabs(["Flight Search", "Cheap Deals", "Chatbot"])

with tab1:
    st.title("Cheap Flight Explorer")
    st.subheader("Search Cheap flights in Europe")


    origin_choice = st.selectbox("Origin", ["Any"] + origins)
    destination_choice = st.selectbox("Destination", ["Any"] + origins)

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
        if origin_choice == "Any":
            origin_list = origins
        else:
            origin_list = [origin_choice]
        
        if destination_choice == "Any":
            destination_list = origins
        else:
            destination_list = [destination_choice]

        results = []

        for dest in destination_list:

            valid_origins = [o for o in origin_list if o != dest]

            if len(valid_origins) ==0:
                continue
            results.extend(search_multiple_origins(origin_list, dest, str(date)))

        rows = []

        for r in results:
            origin = r["origin"]
            destination = r["destination"]

            if "error" in r:
                rows.append({
                    "origin": origin,
                    "destination": destination,
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
                    "destination": destination,
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
        df = st.session_state["df"]

        filtered = df[
            (df["dep_time"] >= dep_start) &
            (df["dep_time"] <= dep_end) &
            (df["arr_time"] >= arr_start) &
            (df["arr_time"] <= arr_end)
        ].copy()

        filtered["is_cheapest"] = filtered.groupby("origin")["price"].transform(
            lambda x: x == x.min()
        )

        filtered = filtered[[
            "origin", "destination", "City", "Country",
            "airline", "AirlineName",
            "price", "dep_time", "arr_time", "duration",
            "is_cheapest"
        ]]
        filtered["route"] = filtered["origin"] + " -> " + filtered["destination"]

        st.subheader("Filtered Results")
        st.dataframe(filtered.style.apply(highlight_cheapest, axis=1))

        cheapest_by_route = (filtered.groupby("route")["price"]
                    .min().reset_index().sort_values("price")
                    .head(5).set_index("route"))

        st.subheader("Cheapest Price by Route (Top 5 Cheapest)")
        st.bar_chart(cheapest_by_route["price"])


        avg_price_by_route = (filtered.groupby("route")["price"]
                              .mean().reset_index().sort_values("price")
                              .head(5).set_index("route"))
        
        
        st.subheader("Average Price by Route (Top 5 Cheapest)")
        st.bar_chart(avg_price_by_route["price"])

with tab2:
    st.subheader("🔥 Flight Tickets cheaper than predicted")
    if "df" not in st.session_state:
        st.info("Please search flights first")
    else:
        threshold = st.slider(
            "How much cheaper than predicted?",
            min_value = 5,
            max_value = 100,
            value = 20,
            step = 5
        )
        cheap = df_pred[df_pred["diff"] > threshold]

        if len(cheap_display) == 0:
            st.info("No significantly cheap flights found on selected date.")
        else:
            st.dataframe(cheap_display)


with tab3:
    st.subheader("Chatbot")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    
    if "pending_user_input" not in st.session_state:
        st.session_state["pending_user_input"] = None

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    user_input = st.chat_input("please input your request")
    if user_input:
        st.session_state["pending_user_input"] = user_input
        st.rerun()

    if st.session_state["pending_user_input"] is not None:
        user_text = st.session_state["pending_user_input"]

        st.session_state["messages"].append(
            {"role": "user", "content": user_text}
        )

        bot_reply = f"You said: {user_text}"
        st.session_state["messages"].append(
            {"role": "assistant", "content": bot_reply}
        )

        st.session_state["pending_user_input"] = None
        st.rerun()
