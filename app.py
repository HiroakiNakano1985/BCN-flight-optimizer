import streamlit as st
from flight_api import search_multiple_origins
import pandas as pd
from datetime import time, datetime
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

def parse_gf_datetime(text):
    # "7:00 AM on Thu, Mar 12" → "7:00 AM Thu Mar 12 2026"
    text = text.replace(" on ", " ")
    text = text + " 2026"

    return datetime.strptime(text, "%I:%M %p %a, %b %d %Y")


def normalize_airline(name: str) -> str:
    if not name:
        return None
    name = name.replace("|", ",")
    first = name.split(",")[0].strip()
    if "Operated by" in first:
        first = first.split("Operated by")[0].strip()
    return first


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
            if len(valid_origins) == 0:
                continue
            results.extend(search_multiple_origins(valid_origins, dest, str(date)))

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


            offers = r

            for offer in offers["data"]:
                rows.append({
                    "origin": origin,
                    "destination": destination,
                    "price": offer["price_as_number"],
                    "airline": offer["airline"],
                    "duration": offer["duration_seconds"],
                    "departure_time": offer["departure_description"],
                    "arrival_time": offer["arrival_description"],
                    "error": None
                })

        df = pd.DataFrame(rows)
        df["City"] = df["destination"].apply(lambda x: origin_info[x][0])
        df["Country"] = df["destination"].apply(lambda x: origin_info[x][1])
        df["airline"] = df["airline"].apply(normalize_airline)        
        df["AirlineName"] = df["airline"].apply(lambda x: airline_names.get(x, "Unknown"))
        df["departure_dt"] = df["departure_time"].apply(parse_gf_datetime)
        df["arrival_dt"] = df["arrival_time"].apply(parse_gf_datetime)

        df["dep_date"] = df["departure_dt"].dt.date.astype(str)
        df["dep_time"] = df["departure_dt"].dt.time
        df["dep_minutes"] = df["departure_dt"].dt.hour * 60 + df["departure_dt"].dt.minute

        df["arr_date"] = df["arrival_dt"].dt.date.astype(str)
        df["arr_time"] = df["arrival_dt"].dt.time
        df["arr_minutes"] = df["arrival_dt"].dt.hour * 60 + df["arrival_dt"].dt.minute

        df["weekday"] = df["departure_dt"].dt.day_name()
        df["duration_min"] = df["duration"] / 60

        df = df.drop(columns=["departure_time", "arrival_time"])
        st.session_state["df"] = df
        status.empty()
        st.success("Search completed!")

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
            "AirlineName", "price", "dep_time", "arr_time", "duration", "is_cheapest"]]
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
        st.info("Please run a search first.")
    else:
        df = st.session_state["df"].copy()
        threshold = st.slider(
            "Show flights cheaper than predicted by at least this amount (EUR)",
            min_value=0,
            max_value=200,
            value=20,
            step=5
        )



        df_pred = df.copy()
        df_pred["route_weekday"] = df["origin"] + "_" + df["destination"] + "_" + df["weekday"] 
        df_pred["pred_price"] = model.predict(df_pred[[
            "origin",
            "destination",
            "airline",
            "weekday",
            "route_weekday",
            "duration_min",
            "dep_minutes"
        ]])



        df_pred["diff"] = df_pred["pred_price"] - df_pred["price"]

        cheap = df_pred[df_pred["diff"] > threshold].copy()

        cheap["City"] = cheap["destination"].apply(lambda x: origin_info[x][0])
        cheap["Country"] = cheap["destination"].apply(lambda x: origin_info[x][1])
        cheap["AirlineName"] = cheap["airline"].apply(lambda x: airline_names.get(x, "Unknown"))

        cheap["diff"] = cheap["diff"].round(2)
        cheap["pred_price"] = cheap["pred_price"].round(2)

        cheap_display = cheap[[
            "origin", "destination","City", "Country",
            "airline","dep_time", "arr_time",
            "price", "pred_price", "diff"
            ]].sort_values("diff", ascending=False)

        st.subheader("🔥 Flight Tickets cheaper than predicted by threshold")

        if len(cheap_display) == 0:
            st.info("No significantly cheap flights found on selected date.")
        else:
            st.dataframe(cheap_display)

st.markdown("""
<style>
/* CSS for tab3 */
[data-testid="stChatInput"] > div {
    position: fixed !important;
    bottom: 0 !important;
    left: 0 !important;
    width: 100% !important;
    background: white !important;
    padding: 12px !important;
    z-index: 99999 !important;
    border-top: 1px solid #ddd !important;
}

[data-testid="stMainBlockContainer"] {
    padding-bottom: 140px !important;
}
</style>
""", unsafe_allow_html=True)

from google.genai import Client
import json
import re
import dateparser
import datetime

client = Client(api_key=st.secrets["GEMINI_API_KEY"])
# Force all dates to be in 2026
def fix_year(date_str):
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        dt = dt.replace(year=2026)
        return dt.strftime("%Y-%m-%d")
    except:
        return date_str



def parse_user_input(text):
    prompt = f"""
    You are an information extraction system.
    Extract travel information from the user message and output ONLY a JSON object:

    {{
    "origin": "IATA airport code or null",
    "start_date": "YYYY-MM-DD or null",
    "end_date": "YYYY-MM-DD or null"
    }}

    Rules:
    - Convert city names to IATA codes (Barcelona → BCN).
    - When the user mentions a city with multiple airports (e.g., London), ALWAYS return the city-level IATA code:
        - London → LON
    - Accept ANY date format, including incomplete or shorthand formats.
    - Accept inputs with punctuation, typos, or separators like ';' or ':'.
    - If the user mentions only an end date (e.g. "end date 30 Mar"), set end_date.
    - If information is missing, return null for that field.
    - ALWAYS return valid JSON. Never output explanations.

    User message: {text}
    """

    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt
    )

    raw = response.text.strip()

    # extracting json
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {"origin": None, "start_date": None, "end_date": None, "num_cities": 2}

    json_str = match.group(0)

    try:
        data = json.loads(json_str)
    except:
        json_str = re.sub(r",\s*}", "}", json_str)
        json_str = re.sub(r",\s*\]", "]", json_str)
        try:
            data = json.loads(json_str)
        except:
            return {"origin": None, "start_date": None, "end_date": None, "num_cities": 2}
    data["num_cities"] = 2
    return data

with tab3:
    st.subheader("Route Recoomendation Chatbot")

    # -----------------------------
    # 1. Initialize session states
    # -----------------------------
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "Hi! We recommend cheap multi-city flights for you.\nCould you provide the origin and travel dates?"
            }
        ]

    if "pending" not in st.session_state:
        st.session_state["pending"] = None

    if "travel_info" not in st.session_state:
        st.session_state["travel_info"] = {
            "origin": None,
            "start_date": None,
            "end_date": None
        }

    if "pending_step" not in st.session_state:
        st.session_state["pending_step"] = "parse"

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # -----------------------------
    # 2. User input
    # -----------------------------
    user_input = st.chat_input("please input your request")
    if user_input:
        st.session_state["pending"] = user_input
        st.rerun()

    # -----------------------------
    # 3. Process pending message
    # -----------------------------

    # --- STEP 1: Parse user input ---
    if st.session_state["pending"] is not None and st.session_state["pending_step"] == "parse":
        text = st.session_state["pending"]

        # Add user message
        st.session_state["messages"].append({"role": "user", "content": text})

        try:
            # ---- Parse user input ----
            parsed = parse_user_input(text)
            info = st.session_state["travel_info"]

            if parsed.get("origin"):
                info["origin"] = parsed["origin"]
            if parsed.get("start_date"):
                info["start_date"] = fix_year(parsed["start_date"])
            if parsed.get("end_date"):
                info["end_date"] = fix_year(parsed["end_date"])

            # ---- Fallback date parsing ----
            for key in ["start_date", "end_date"]:
                if info[key] is None:
                    m = re.search(r"(\d{1,2}\s*[A-Za-z]{3,9})", text)
                    if m:
                        try:
                            dt = dateparser.parse(
                                m.group(1),
                                settings={"RELATIVE_BASE": datetime.datetime(2026, 3, 15)}
                            )
                            info[key] = dt.strftime("%Y-%m-%d")
                        except:
                            pass

            # ---- Missing info check ----
            missing = [k for k, v in info.items() if v is None]
            if missing:
                st.session_state["messages"].append(
                    {"role": "assistant", "content": "I still need: " + ", ".join(missing)}
                )
                st.session_state["pending"] = None
                st.session_state["pending_step"] = "parse"
                st.rerun()

            # ---- Parsing finished → show intermediate message ----
            st.session_state["messages"].append(
                {
                    "role": "assistant",
                    "content": f"Great! Here is your info: {info}\n\nSearching for the best routes using our machine learning model..."
                }
            )

            # Move to next step
            st.session_state["pending_step"] = "search"
            st.rerun()

        except Exception as e:
            st.session_state["messages"].append(
                {"role": "assistant", "content": "Sorry, I couldn't understand your input."}
            )
            st.session_state["last_error"] = str(e)
            st.session_state["pending"] = None
            st.session_state["pending_step"] = "parse"
            st.rerun()


    # --- STEP 2: Run ML ---
    if st.session_state["pending_step"] == "search":
        try:
            info = st.session_state["travel_info"]

            from chatbot_prediction import find_best_routes
            best_routes = find_best_routes(info)

            st.session_state["temp_best_routes"] = best_routes

            st.session_state["messages"].append(
                {
                    "role": "assistant",
                    "content": "Found the top route candidates!\n\nFetching real flight prices from live APIs..."
                }
            )

            st.session_state["pending_step"] = "api_search"
            st.rerun()

        except Exception as e:
            st.session_state["messages"].append(
                {"role": "assistant", "content": "Sorry, something went wrong during ML prediction."}
            )
            st.session_state["last_error"] = str(e)
            st.session_state["pending_step"] = "parse"
            st.session_state["pending"] = None
            st.rerun()

    # --- STEP 3: API search ---
    if st.session_state["pending_step"] == "api_search":
            try:
                from flight_api import search_multiple_legs

                best_routes = st.session_state["temp_best_routes"]
                real_results = []
                for route in best_routes:
                    legs = route["legs"]
                    real_price = search_multiple_legs(legs)

                    real_results.append({
                        "legs": legs,
                        "predicted_price": route.get("predicted_price"),
                        "real_price": real_price["total_price"],
                        "details": real_price["details"]
                    })

                st.session_state["real_results"] = sorted(real_results, key=lambda x: x["real_price"])

                st.session_state["messages"].append(
                    {"role": "assistant", "content": "Search completed! Here are your best routes below."}
                )

                st.session_state["pending_step"] = "parse"
                st.session_state["pending"] = None
                st.rerun()


            except Exception as e:
                st.session_state["messages"].append(
                    {"role": "assistant", "content": "Sorry, something went wrong during route search."}
                )
                st.session_state["last_error"] = str(e)
                st.session_state["pending_step"] = "parse"
                st.rerun()

    # -----------------------------
    # 5. Route cards
    # -----------------------------


    if "real_results" in st.session_state:
        st.markdown("## ✈️ Best Route Options")

        for i, r in enumerate(st.session_state["real_results"]):
            st.markdown(f"### 🛫 Route {i+1}")

            details_list = r.get("details", [])
            first_detail = details_list[0] if details_list else {}
            flights = first_detail.get("flights", [])
            first_flight = flights[0] if flights else {}

            dep_desc = first_flight.get("departure_description", "")
            arr_desc = first_flight.get("arrival_description", "")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Real Price", f"{r['real_price']} EUR")
            with col2:
                st.metric("Predicted Price", f"{r['predicted_price']:.2f} EUR")

            st.markdown("#### Flight Legs")
            for idx, leg in enumerate(r["legs"]):

                detail = details_list[idx] if idx < len(details_list) else {}
                flights = detail.get("flights", [])
                
                flight = flights[0] if flights else {}

                dep_desc = flight.get("departure_description", "N/A")
                arr_desc = flight.get("arrival_description", "N/A")

                st.write(
                    f"- **{leg['origin']} → {leg['destination']}** "
                    f"({leg['date']} | {dep_desc} → {arr_desc})"
                )


            st.markdown("---")