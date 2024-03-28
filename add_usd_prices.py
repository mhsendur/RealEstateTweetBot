import json
import requests

# Your API key for Open Exchange Rates
api_key = "846a121a69904bf9b95dc1323ddcde3a"

# Function to get the exchange rate from Open Exchange Rates
def get_exchange_rate(api_key):
    url = f"https://openexchangerates.org/api/latest.json?app_id={api_key}&symbols=TRY"
    response = requests.get(url)
    data = response.json()
    # Check the API response
    print("API Response:", data)
    # Calculate the inverse of USD to TRY to get TRY to USD
    try_to_usd_rate = 1 / data['rates']['TRY']
    return try_to_usd_rate

# Function to convert prices in the listings
def convert_prices(listings, exchange_rate):
    for listing in listings:
        price_in_try = listing['priceDetail']['price']
        listing['priceDetail']['price_in_usd'] = round(price_in_try * exchange_rate, 2)
    return listings

# Open and read the JSON file
with open('istanbul_emlakjet_all_records_cleann.json', 'r') as file:
    listings = json.load(file)

# Fetch the exchange rate
exchange_rate = get_exchange_rate(api_key)

# Convert the prices
converted_listings = convert_prices(listings, exchange_rate)

# Save the updated listings back to a JSON file
with open('istanbul_emlakjet_all_records_usd_info_.json', 'w') as file:
    json.dump(converted_listings, file, ensure_ascii=False, indent=4)
