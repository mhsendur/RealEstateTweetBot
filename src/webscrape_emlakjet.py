import asyncio
import json
import backoff
import ssl
import aiohttp
import os
from datetime import datetime, timedelta
from google.cloud import storage

# Define Google Cloud Storage settings
GCS_BUCKET_NAME = "real-estate-bot-bucket"
JSON_FILE_NAME = "istanbul_emlakjet_all_records_updated.json"

# Initialize Google Cloud Storage client
storage_client = storage.Client()

provinces = [
    "Adalar", "Arnavutköy", "Ataşehir", "Avcılar", "Bağcılar", "Bahçelievler", "Bakırköy", "Başakşehir",
    "Bayrampaşa", "Beşiktaş", "Beykoz", "Beylikdüzü", "Beyoğlu", "Büyükçekmece", "Çatalca", "Çekmeköy",
    "Esenler", "Esenyurt", "Eyüp", "Fatih", "Gaziosmanpaşa", "Güngören", "Kadıköy", "Kağıthane",
    "Kartal", "Küçükçekmece", "Maltepe", "Pendik", "Sancaktepe", "Sariyer", "Şile", "Silivri", "Şişli",
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

def download_from_gcs(bucket_name, filename):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    if blob.exists():
        return json.loads(blob.download_as_text())
    return {}

def upload_to_gcs(bucket_name, filename, data):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=4))
    print(f"Uploaded data to {bucket_name}/{filename}")

def update_emlakjet_data(new_data):
    today = datetime.now().strftime('%Y-%m-%d')

    # Download existing data from GCS
    existing_data = download_from_gcs(GCS_BUCKET_NAME, JSON_FILE_NAME)

    # Process new data to update existing ads and add new ads
    for ad in new_data:
        ad_id = ad['id']
        ad['ilanda_kalis_suresi'] = (datetime.now() - datetime.strptime(ad['createdAt'], '%Y-%m-%dT%H:%M:%SZ')).days
        if ad_id in existing_data:
            existing_data[ad_id] = ad
        else:
            existing_data[ad_id] = ad

    # Remove inactive listings
    new_ad_ids = {ad['id'] for ad in new_data}
    inactive_ads = [ad_id for ad_id in existing_data if ad_id not in new_ad_ids]
    for ad_id in inactive_ads:
        existing_data[ad_id]['ilan_bitis'] = today

    # Upload updated data to GCS
    upload_to_gcs(GCS_BUCKET_NAME, JSON_FILE_NAME, existing_data)

SCRAPE_LAST_RUN_FILE = "scrape_last_run.txt"

def get_last_run_time():
    if os.path.exists(SCRAPE_LAST_RUN_FILE):
        with open(SCRAPE_LAST_RUN_FILE, "r") as file:
            last_run_str = file.read().strip()
            return datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S")
    return datetime.min

def update_last_run_time():
    with open(SCRAPE_LAST_RUN_FILE, "w") as file:
        file.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def run_scraper():
    last_run_time = get_last_run_time()
    if datetime.now() - last_run_time > timedelta(hours=24):
        print("Running scraper...")
        records = asyncio.run(main())
        update_emlakjet_data(records)
        update_last_run_time()
    else:
        print("Scraper run skipped.")

if __name__ == "__main__":
    run_scraper()
