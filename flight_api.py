import os
import requests
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import time

load_dotenv()

API_KEY = os.getenv("AMAD_CLIENT_ID")
API_SECRET = os.getenv("AMAD_CLIENT_SECRET")

TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

ACCESS_TOKEN =None

def get_access_token():
    global ACCESS_TOKEN
    if ACCESS_TOKEN is not None:
        return ACCESS_TOKEN
    data = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": API_SECRET
    }
    response = requests.post(TOKEN_URL, data=data)
    response.raise_for_status()
    ACCESS_TOKEN = response.json()["access_token"]
    return ACCESS_TOKEN


def search_flights(origin, destination, date):
    
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": date,
        "adults": 1,
        "max": 15
    }

    response = requests.get(SEARCH_URL, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    direct_offers = []
    for offer in data["data"]:
        segments = offer["itineraries"][0]["segments"]
        if all(seg["numberOfStops"] == 0 for seg in segments):
            direct_offers.append(offer)
    data["data"] = direct_offers
    return data

    return response.json()

def search_multiple_origins(origins, destination, date, max_workers=1):

    def fetch(origin):
        for attempt in range(3):  # max try 3 times
            try:
                time.sleep(1.2)  # to avoid "too many requests"
                data = search_flights(origin, destination, date)
                return {"origin": origin, "data": data}
            except Exception as e:
                if "429" in str(e):
                    # in case of 429, take longer to avoid error
                    time.sleep(2)
                    continue
                return {"origin": origin, "error": str(e)}
        return {"origin": origin, "error": "Failed after retries"}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(fetch, origins))

    return results
