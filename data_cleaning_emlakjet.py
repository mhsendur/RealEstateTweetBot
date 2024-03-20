import json

def load_json_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def normalize_text(text):
    return text.strip().lower()

def validate_and_format_url(url, default_domain='https://imaj.emlakjet.com'):
    if not url.startswith('http'):
        url = f"{default_domain}{url}"
    return url

def preprocess_quickinfos(quickInfos):
    return '; '.join([f"{info['name']}: {info['value']}" for info in quickInfos])

def process_info_fields(info):
    processed_info = {}
    for entry in info:
        key = normalize_text(entry['name'])
        processed_info[key] = entry['value']
    return processed_info

def cleanse_and_preprocess_data(data):
    cleansed_data = []
    for item in data:
        images = [validate_and_format_url(url) for url in item.get('imagesFullPath', [])]
        title = normalize_text(item['title'])
        description = normalize_text(item.get('description', ''))
        
        if not images or not title:
            continue
        
        info = process_info_fields(item.get('info', []))
        
        cleansed_item = {
            'id': item['id'],
            'categoryTypeName': normalize_text(item['categoryTypeName']),
            'tradeTypeName': normalize_text(item['tradeTypeName']),
            'estateTypeName': normalize_text(item['estateTypeName']),
            'title': title,
            'url': validate_and_format_url(item['url']),
            'images': images,
            'locationSummary': normalize_text(item.get('locationSummary', 'unknown location')),
            'quickInfos': preprocess_quickinfos(item['quickInfos']),
            'priceDetail': item['priceDetail'],
            'description': description,
            'info': info,
            'location': item['location'],
        }
        
        cleansed_data.append(cleansed_item)
    return cleansed_data

def remove_duplicates(data):
    unique_data = {}
    for item in data:
        unique_data[item['id']] = item
    return list(unique_data.values())


def write_json_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def main():
    input_file_path = 'istanbul_emlakjet_all_records_updated.json'
    output_file_path = 'istanbul_emlakjet_all_records_clean.json'
    
    raw_data = load_json_data(input_file_path)
    
    cleansed_data = cleanse_and_preprocess_data(raw_data)
    
    write_json_data(output_file_path, cleansed_data)

if __name__ == '__main__':
    main()
