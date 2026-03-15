# test_api.py

from flight_api import search_multiple_legs

# テスト用の legs（あなたの ML モデルが返す形式に合わせる）
legs = [
    {
        "origin": "BCN",
        "destination": "CDG",
        "date": "2026-03-25"
    }
]

print("=== Running search_multiple_legs ===")
result = search_multiple_legs(legs)

print("\n=== API Raw Result ===")
print(result)

print("\n=== Details ===")
details = result.get("details", {})
print(details)

print("\n=== Flights ===")
flights = details.get("flights", [])
for i, f in enumerate(flights):
    print(f"Flight {i+1}: {f}")