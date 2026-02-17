from data_generation import collect_all_cities

# 20 cities
#origins = [
#    "LIS", "CMN", "TUN", "CDG", "LON", "ZRH", "BRU", "AMS",
#    "BER", "PRG", "WAW", "VIE", "LJU", "FCO", "BUD", "ZAG",
#    "OTP", "SOF", "ATH", "IST", "NCE", "MAD"]

origins = ["NCE", "MAD"]


# run for 30days
collect_all_cities(origins, "BCN", "2026-02-18", days=30)