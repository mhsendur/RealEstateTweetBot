import asyncio
import json
import backoff
import ssl
import aiohttp
import os
from datetime import datetime, timedelta

provinces = [
    "Adalar", "Arnavutköy", "Ataşehir", "Avcılar", "Bağcılar", "Bahçelievler", "Bakırköy", "Başakşehir", 
    "Bayrampaşa", "Beşiktaş", "Beykoz", "Beylikdüzü", "Beyoğlu", "Büyükçekmece", "Çatalca", "Çekmeköy", 
    "Esenler", "Esenyurt", "Eyüpsultan", "Fatih", "Gaziosmanpaşa", "Güngören", "Kadıköy", "Kağıthane", 
    "Kartal", "Küçükçekmece", "Maltepe", "Pendik", "Sancaktepe", "Sarıyer", "Şile", "Silivri", "Şişli", 
    "Sultanbeyli", "Sultangazi", "Tuzla", "Ümraniye", "Üsküdar", "Zeytinburnu"
]

turkish_to_english_map = {
    "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
    "Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U"
}

def turkish_to_english(text):
    return ''.join(turkish_to_english_map.get(char, char) for char in text)

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def fetch_listings(session, province, page):
    province_english = turkish_to_english(province).lower()
    url = f"https://search.emlakjet.com/search/v1/listing/satilik-konut/istanbul-{province_english}/{page}"
    async with session.get(url, ssl=ssl_context) as response:
        if response.status == 200:
            data = await response.json()
            records = data['listingCard']['records']
            maximumPage = data['maximumPage']
            return records, maximumPage
        else:
            print(f"Province: {province}, Page {page}: Failed to collect records. Status code: {response.status}")
            return [], 0

@backoff.on_exception(backoff.expo, aiohttp.ClientOSError, max_time=60)
async def fetch_additional_info(session, listing_id):
    try:
        url = f"https://api.emlakjet.com/e6t/v1/listing/{listing_id}/"
        async with session.get(url, ssl=ssl_context) as response:
            if response.status == 200:
                data = await response.json()
                result = data.get('result', {})
                description = result.get('description', None)
                info = result.get('info', None)
                return description, info
            else:
                print(f"Listing ID: {listing_id}: Failed to collect additional information. Status code: {response.status}")
                return None, None
    except aiohttp.ClientError as e:
        print(f"Request failed: {e}")
        return None, None

async def main():
    all_records = []
    async with aiohttp.ClientSession() as session:
        for province in provinces:
            page = 0
            records, maximumPage = await fetch_listings(session, province, page)
            while page <= maximumPage:
                if records:
                    tasks = [fetch_additional_info(session, record['id']) for record in records]
                    listings_info = await asyncio.gather(*tasks)
                    for record, (description, info) in zip(records, listings_info):
                        if description is not None and info is not None:
                            record['description'] = description
                            record['info'] = info
                    all_records.extend(records)
                    print(f"Province: {province}, Page {page}: Collected {len(records)} records.")
                page += 1
                if page <= maximumPage:
                    records, _ = await fetch_listings(session, province, page) 
                await asyncio.sleep(0.1)  

    print(f"Total number of collected records: {len(all_records)}")
    return all_records

def save_records(records, filename="istanbul_emlakjet_all_records_updated.json"):
    # Load existing data if the file exists, otherwise initialize an empty dictionary
    if os.path.exists(filename):
        os.rename(filename, "istanbul_emlakjet_all_records_old.json")
    
    # Save the new records to the updated JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=4)


def update_emlakjet_data(new_data):
    today = datetime.now().strftime('%Y-%m-%d')
    old_filename = 'istanbul_emlakjet_all_records_old.json'
    
    # Load existing data from the old file if it exists, otherwise initialize an empty dictionary
    if os.path.exists(old_filename):
        with open(old_filename, 'r') as f:
            existing_data = {ad['id']: ad for ad in json.load(f)}
    else:
        existing_data = {}

    # Process new data to update existing ads and add new ads
    for ad in new_data:
        ad_id = ad['id']
        ad['ilanda_kalis_suresi'] = (datetime.now() - datetime.strptime(ad['createdAt'], '%Y-%m-%dT%H:%M:%SZ')).days
        if ad_id in existing_data:
            # Overwrite the existing ad with updated information
            existing_data[ad_id] = ad
        else:
            # Add new ad
            existing_data[ad_id] = ad

    # Check for deleted ads and mark them with 'ilan_bitis' if not in new data
    new_ad_ids = {ad['id'] for ad in new_data}
    for ad_id, ad in existing_data.items():
        if ad_id not in new_ad_ids:
            ad['ilan_bitis'] = today
            ad['ilanda_kalis_suresi'] = (datetime.now() - datetime.strptime(ad['createdAt'], '%Y-%m-%dT%H:%M:%SZ')).days

    # Write the updated data to the updated JSON file
    with open("istanbul_emlakjet_all_records_updated.json", 'w', encoding='utf-8') as f:
        json.dump(list(existing_data.values()), f, ensure_ascii=False, indent=4)


SCRAPE_LAST_RUN_FILE = "scrape_last_run.txt"

def get_last_run_time():
    """Get the time of the last scraper run from the file."""
    if os.path.exists(SCRAPE_LAST_RUN_FILE):
        with open(SCRAPE_LAST_RUN_FILE, "r") as file:
            last_run_str = file.read().strip()
            last_run_time = datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S")
            return last_run_time
    else:
        return datetime.min
    
def update_last_run_time():
    """Write the current time to the last run file."""
    with open(SCRAPE_LAST_RUN_FILE, "w") as file:
        file.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def run_scraper():
    """Run the scraper if it has been more than 24 hours since the last run."""
    # Get the time of the last run
    last_run_time = get_last_run_time()
    
    # Check if it has been more than 24 hours since the last run
    if datetime.now() - last_run_time > timedelta(hours=24):
        print("More than 24 hours since the last run. Running scraper...")
        
        # Run the scraper (synchronously)
        records = asyncio.run(main())
        save_records(records)
        update_emlakjet_data(records)
        
        # Update the last run time after the scraper runs
        update_last_run_time()
    else:
        print("It has been less than 24 hours since the last run. Skipping the scraper.")


if __name__ == "__main__":
    run_scraper()
