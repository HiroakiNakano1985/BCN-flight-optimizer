# ✈️ Barcelona Flight Optimizer

**Barcelona Flight Optimizer** is a Streamlit web application that retrieves real‑time flight offers to Barcelona (BCN) from multiple global cities and compares them against a **machine‑learning–predicted “fair price.”**

The app highlights flights that are **significantly cheaper than expected (20EURs)**, helping users quickly spot unusually good deals.

---

## 🚀 Features

### **Real‑time flight search**
- Fetches live flight offers using the Amadeus API  
- Supports multiple origin cities (from 20 cities in Europe)  
- Filters by departure and arrival time  
- Displays clean, user‑friendly tables with highlights for the cheapest options

### **Machine Learning price prediction**
- XGBoost regression model trained on historical flight data
  (used ticket prices from 18Feb2026 to 19Mar2026)  
- Predicts the “fair price” for each flight based on:
  - origin  
  - airline  
  - weekday  
  - route_weekday  
  - duration(min)  
  - dep_minutes  
- Model is saved as `model.pkl` and loaded by the app at runtime

### **Deal detection**
- Computes  
  diff = pred_price - price
- Flights with over 20EURs positive diff are shown as tickets cheaper than predicted.

### **Tech Stack**
- Python 3.10+
- Streamlit — Web UI
- XGBoost — Regression model
- scikit‑learn — Preprocessing & Pipeline
- Pandas — Data manipulation
- Amadeus API — Real‑time flight data
- Pickle — Model serialization

### **Project Structure**
project/
│
├── app.py                         # Streamlit web application
├── model.py                       # ML training script (run once)
├── model.pkl                      # Trained ML model used by app.py
│
├── data_pipeline/                 # Data collection & preprocessing
│   ├── data_generation.py         # Tool to collect raw flight data
│   ├── collecting_data.py         # API collection script (split due to API errors)
│   ├── dataset_creation.py        # Merge collected data into full dataset
│   ├── dataset_processing.py      # Clean & preprocess dataset for ML
│
├── flight_api.py                  # Amadeus API wrapper
├── config.py                      # API keys, city metadata, airline names
│
├── data/                          # Datasets
│   ├── bcn_flight_dataset_full.csv          # Raw merged dataset
│   ├── bcn_flight_dataset_preprocessed.csv  # Final ML training dataset
│   ├── bcn_flight_dataset_remaining.csv
│   ├── bcn_flight_dataset_till_IST.csv
│   ├── bcn_flight_dataset_till_PRG.csv
│   └── baseline_prices.csv        # (Legacy file, no longer used)
│
└── README.md

### **Future Improvements**
- Adjustable threshold for “cheap flight” detection
- Visual comparison of predicted vs. actual prices
- Time‑series trend analysis per origin city
- AI recommendation model for round-trip

### **Author**
Hiroaki Nakano
Barcelona-based developer, Japan Post Bank
