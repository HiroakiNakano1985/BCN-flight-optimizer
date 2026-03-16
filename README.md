# ✈️ Cheap Flight Explorer

**Cheap Flight Explorer** is a Streamlit‑based web application that combines real‑time flight search, machine‑learning price prediction, and a multi‑city itinerary recommendation chatbot.

Using the Google Flights Live API, the app retrieves up‑to‑date flight prices and compares them against a custom ML model’s predicted “fair price,” helping travelers instantly identify unusually cheap tickets and discover optimal multi‑city routes.

---

## 🚀 Features

### **1. Flexible Real‑Time Flight Search**
- Powered by the **Google Flights Live API (RapidAPI)**
- Both **origin** and **destination** can be set to **Any** for maximum flexibility
- Search supported for **11 cities** (reduced from 20 due to API limits)
- Clean, intuitive Streamlit UI
- Displays price, departure time, arrival time, and more

---

### **2. Machine‑Learning Price Prediction**
- XGBoost regression model trained on historical flight data  
  (Mar 12, 2026 – Apr 11, 2026, based on the data generated on Mar 11 2026)
- Predicts the “fair price” using features such as:
  - origin  
  - airline  
  - weekday  
  - route_weekday  
  - duration (min)  
  - dep_minutes
- Model stored as `model.pkl` and loaded at runtime

---

### **3. Cheap‑Flight Detection with Adjustable Threshold**
- Computes  
  **diff = predicted_price − actual_price**
- Users can adjust the threshold (e.g., 20 EUR) via a slider
- Only flights significantly cheaper than predicted are highlighted
- Makes it easy to spot exceptional deals at a glance

---

### **4. Multi‑City Route Recommendation Chatbot**
Tell the chatbot your:

- departure city  
- travel start date  
- travel end date  

…and it will automatically:

1. Use the ML model to evaluate all possible  
   **origin → A → B → origin** multi‑city routes  
2. Select the **top 5 cheapest predicted routes**
3. Fetch **real prices** for those routes using the Google Flights API
4. Present the results directly in the chat interface

It feels like having a personal travel analyst who finds the best multi‑city deals for you.

---

## 🧠 Tech Stack

- **Python 3.10+**
- **Streamlit** — Web UI
- **XGBoost** — Regression model
- **scikit‑learn** — Preprocessing
- **Pandas** — Data manipulation
- **Google Flights Live API (RapidAPI)** — Real‑time flight data
- **Pickle** — Model serialization
- **Gemini API** — Powers the multi‑city route recommendation chatbot


---

## 🔄 Major Updates from Previous Version

1. Renamed the application to **Cheap Flight Explorer**
2. Added **Any** option for both origin and destination to increase search flexibility
3. Reduced supported cities from **20 → 11** due to API limitations
4. Migrated from **Amadeus API** to **Google Flights Live API**, because of the limitation of free‑tier usage
5. Redesigned the UI into **three tabs**:
   - **Tab 1:** Standard flight search  
   - **Tab 2:** ML‑based price comparison with adjustable threshold  
   - **Tab 3:** Multi‑city route recommendation chatbot using Gemini
6. Implemented a new chatbot system that:
   - Uses the ML model to predict cheap multi‑city routes  
   - Selects the top 5 candidates  
   - Retrieves real prices via Google Flights API  
   - Returns the results in a conversational format


### **Project Structure**

```
project/
│
├── app.py                         # Main Streamlit application
├── model.py                       # ML training script (run once)
├── model.pkl                      # Trained ML model used for price prediction
│
├── build_route_tabels.py          # Generates route_stats.parquet, airline_stats.parquet,
│                                  # and airport_graph.parquet from flights_preprocessed.csv.
│                                  # These parquet files are used by the chatbot to fill in
│                                  # missing route attributes (airline, duration, weekday, etc.)
│
├── chatbot_prediction.py          # Generates all possible multi-city routes based on user input,
│                                  # calls the ML model to predict prices, and returns the top 5
│                                  # cheapest predicted routes to the chatbot.
│
├── checkpoint.txt                 # Recovery file used during Google Flights data collection.
│                                  # Stores completed routes/dates so the process can resume
│                                  # safely after errors or interruptions.
│
├── dataset_processing.py          # Cleans and preprocesses flights_bulk.csv into
│                                  # flights_preprocessed.csv for ML training.
│
├── google_flights_collecting_data.py
│                                  # Collects real flight data (Mar 12 – Apr 11) for 11 cities
│                                  # using the Google Flights Live API. Produces flights_bulk.csv.
│
├── flight_api.py                  # Wrapper for Google Flights Live API (RapidAPI)
├── config.py                      # API keys, city metadata, airline names, and app settings
│
├── data/                          # Datasets used across the project
│   ├── flights_bulk.csv           # Raw flight data collected from Google Flights API
│   ├── flights_preprocessed.csv   # Cleaned dataset used for ML training
│   ├── airline_stats.parquet      # Top 3 airlines per route (used by chatbot to fill missing airline info)
│   ├── airport_graph.parquet      # Graph of reachable cities per origin (used to filter invalid routes)
│   ├── route_stats.parquet        # Flight duration, departure time, weekday info per route
│                                  # (used by chatbot to fill missing ML features)
│   └── baseline_prices.csv        # Legacy file (no longer used)
│
├── .streamlit/                    # Streamlit configuration (theme, secrets template, etc.)
├── .env                           # Environment variables (API keys)
├── .gitignore                     # Git ignore rules
└── README.md                      # Project documentation
```


### **Author**
Hiroaki Nakano  
MSc Business Analytics (2026) in ESADE  
Japan Post Bank
