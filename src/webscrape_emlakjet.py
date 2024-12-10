import asyncio
import json
import backoff
import ssl
import aiohttp
import os
from datetime import datetime, timedelta
from google.cloud import storage

# Google Cloud Storage settings
GCS_BUCKET_NAME = "real-estate-bot-bucket"
JSON_FILE_NAME = "istanbul_emlakjet_all_records_updated.json"

# Maximum pages to scrape per province
MAX_PAGES_PER_PROVINCE = 45

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

@backoff.on_exception(backoff.expo, aiohttp.ClientError, max_tries=5, max_time=300)
async def fetch_listings(session, province, page):
    """Fetch property listings for a specific province and page."""
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

@backoff.on_exception(backoff.expo, aiohttp.ClientError, max_tries=5, max_time=300)
async def fetch_additional_info(session, listing_id):
    """Fetch additional details for a specific listing."""
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
    """Main scraping function."""
    all_records = []
    connector = aiohttp.TCPConnector(limit=10)  # Limit simultaneous connections
    timeout = aiohttp.ClientTimeout(total=60)   # Increase timeout
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for province in provinces:
            page = 0
            records, maximumPage = await fetch_listings(session, province, page)
            maximumPage = min(maximumPage, MAX_PAGES_PER_PROVINCE)  # Limit pages to scrape
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
                await asyncio.sleep(0.5)  # Delay to throttle requests

    print(f"Total number of collected records: {len(all_records)}")
    return all_records

def download_from_gcs(bucket_name, filename):
    """Download a file from Google Cloud Storage."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    if blob.exists():
        return json.loads(blob.download_as_text())
    return {}

def upload_to_gcs(bucket_name, filename, data):
    """Upload a file to Google Cloud Storage."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=4))
    print(f"Uploaded data to {bucket_name}/{filename}")

def update_emlakjet_data(new_data):
    """Update the property data in Google Cloud Storage."""
    today = datetime.now().strftime('%Y-%m-%d')

    # Download existing data from GCS
    existing_data = download_from_gcs(GCS_BUCKET_NAME, JSON_FILE_NAME)

    # Convert existing data to a dictionary (if it's a list)
    if isinstance(existing_data, list):
        existing_data = {ad['id']: ad for ad in existing_data}

    # Convert new data to a dictionary for easy merging
    new_data_dict = {ad['id']: ad for ad in new_data}

    # Update existing ads and add new ads
    for ad_id, ad in new_data_dict.items():
        ad['ilanda_kalis_suresi'] = (datetime.now() - datetime.strptime(ad['createdAt'], '%Y-%m-%dT%H:%M:%SZ')).days
        existing_data[ad_id] = ad

    # Remove inactive listings
    new_ad_ids = set(new_data_dict.keys())
    for ad_id in list(existing_data.keys()):
        if ad_id not in new_ad_ids:
            existing_data[ad_id]['ilan_bitis'] = today

    # Convert back to a list before uploading
    updated_data_list = list(existing_data.values())

    # Upload updated data to GCS
    upload_to_gcs(GCS_BUCKET_NAME, JSON_FILE_NAME, updated_data_list)


SCRAPE_LAST_RUN_FILE = "scrape_last_run.txt"

def get_last_run_time():
    """Get the last run time from the local file."""
    if os.path.exists(SCRAPE_LAST_RUN_FILE):
        with open(SCRAPE_LAST_RUN_FILE, "r") as file:
            last_run_str = file.read().strip()
            return datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S")
    return datetime.min

def update_last_run_time():
    """Update the last run time in the local file."""
    with open(SCRAPE_LAST_RUN_FILE, "w") as file:
        file.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def run_scraper():
    """Run the scraper if the last run was more than 24 hours ago."""
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
    
