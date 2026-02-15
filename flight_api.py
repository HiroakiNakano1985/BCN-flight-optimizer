import os
import requests
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from flight_api import search_flights


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
        "max": 20
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

def search_multiple_origins(origins, destination, date, max_workers=5):
    
    def fetch(origin):
        try:
            data = search_flights(origin, destination, date)
            return {"origin": origin, "data": data}
        except Exception as e:
            return {"origin": origin, "error": str(e)}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(fetch, origins))

    return results
