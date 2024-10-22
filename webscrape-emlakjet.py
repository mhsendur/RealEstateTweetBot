import asyncio
import json
import backoff
import ssl
import aiohttp

provinces = [
    "Adalar", "Arnavutköy", "Ataşehir", "Avcılar", "Bağcılar", "Bahçelievler", "Bakırköy", "Başakşehir", 
    "Bayrampaşa", "Beşiktaş", "Beykoz", "Beylikdüzü", "Beyoğlu", "Büyükçekmece", "Çatalca", "Çekmeköy", 
    "Esenler", "Esenyurt", "Eyüpsultan", "Fatih", "Gaziosmanpaşa", "Güngören", "Kadıköy", "Kağıthane", 
    "Kartal", "Küçükçekmece", "Maltepe", "Pendik", "Sancaktepe", "Sarıyer", "Şile", "Silivri", "Şişli", 
    "Sultanbeyli", "Sultangazi", "Tuzla", "Ümraniye", "Üsküdar", "Zeytinburnu"]

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

if __name__ == "__main__":
    records = asyncio.run(main())

    with open('istanbul_emlakjet_all_records.json', 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=4)
