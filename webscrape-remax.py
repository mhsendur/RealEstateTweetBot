import requests
from bs4 import BeautifulSoup
import json

def get_listing_details(portfolio_number):
    portfolio_number = portfolio_number.replace('Portföy No: ', '').strip()
    detailed_url = f'https://www.remax.com.tr/portfoy/{portfolio_number}'
    response = requests.get(detailed_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    details_dict = {'url': detailed_url}
    details = soup.find_all('li')
    for detail in details:
        strong_tag = detail.find('strong')
        if strong_tag and detail.find('span'):
            label = strong_tag.get_text(strip=True)
            value = detail.find('span').get_text(strip=True)
            details_dict[label] = value
    
    description_section = soup.find('section', class_='detail-info')
    description = ''
    if description_section:
        content_div = description_section.find('div', class_='content')
        if content_div:
            description = ' '.join(p.get_text(strip=True) for p in content_div.find_all('p'))
    
    details_dict['Description'] = description

    return details_dict

json_file_path = 'detailed_listings.json'

data = []

print(f'Creating JSON file at: {json_file_path}')

headers = ['Title', 'Details', 'Price', 'Portfolio Number', 'Description', 'm2 (Brüt)', 'm2 (Net)', 'Bina Yaşı', 'Oda Sayısı', 'Bulunduğu Kat', 'Kat Sayısı', 'Isıtma', 'Banyo Sayısı', 'Balkon', 'Tuvalet Sayısı', 'Eşyalı', 'Kullanım Durumu', 'Site İçerisinde', 'Krediye Uygun', 'url']

for page in range(1, 23):
    url = f'https://www.remax.com.tr/konut/satilik/istanbul-anadolu/kadikoy?page={page}'
    print(f'Fetching data from {url}')
    
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    listings = soup.find_all('div', class_='item')

    print(f'Found {len(listings)} listings on page {page}.')

    for listing in listings:
        listing_data = {}
        listing_data['Title'] = listing.find('div', class_='title').get_text(strip=True) if listing.find('div', class_='title') else 'No Title'
        listing_data['Details'] = listing.find('footer').get_text(separator=' ', strip=True) if listing.find('footer') else 'No Details'
        listing_data['Price'] = listing.find('div', class_='price-container').get_text(strip=True) if listing.find('div', class_='price-container') else 'No Price'
        listing_data['Portfolio Number'] = listing.find('span', class_='portfoy-no').get_text(strip=True) if listing.find('span', class_='portfoy-no') else 'No Portfolio Number'

        detailed_info = get_listing_details(listing_data['Portfolio Number'])
        for key in headers[4:]:  # Starting from 'Description' to the end
            listing_data[key] = detailed_info.get(key, 'N/A')

        data.append(listing_data)
        print(f'Detailed info for listing {listing_data["Portfolio Number"]} written.')

with open(json_file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print('Scraping complete, JSON file is ready.')
