from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("AMAD_CLIENT_ID")
API_SECRET = os.getenv("AMAD_CLIENT_SECRET")