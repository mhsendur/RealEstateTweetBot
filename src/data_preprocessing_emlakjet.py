import json
import json
import re

# Load JSON data from a file.
def load_json_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

# Normalize text to lowercase and strip leading/trailing spaces.
def normalize_text(text):
    if isinstance(text, str):
        return text.strip().lower()
    return text  # Return as is if not a string


# Validate and format URL. 
def validate_and_format_url(url, default_domain='https://imaj.emlakjet.com'):
    if not url.startswith('http'):
        url = f"{default_domain}{url}"
    return url

def process_quickinfos(quickInfos):
    if isinstance(quickInfos, list):
        return '; '.join([f"{info['name']}: {info['value']}" for info in quickInfos if 'name' in info and 'value' in info])
    elif isinstance(quickInfos, str):
        return normalize_text(quickInfos)
    return ''  # Return an empty string if quickInfos is neither a list nor a string


# Function to clean HTML content
def remove_html_tags(text):
    # Step 1: Replace line break tags with a single newline
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    
    # Step 2: Replace paragraph end tags with two newlines
    text = text.replace('</p>', '\n\n')
    
    # Step 3: Remove all remaining HTML tags
    clean_text = re.sub('<.*?>', '', text)
    
    # Step 4: Condense multiple consecutive newlines to two at most
    clean_text = re.sub('\n{3,}', '\n\n', clean_text)
    
    return clean_text

def convert_turkish_date_to_iso(date_str):
    # Map of Turkish month names to their numeric values
    month_mapping = {
        "Ocak": "01", "Şubat": "02", "Mart": "03", "Nisan": "04",
        "Mayıs": "05", "Haziran": "06", "Temmuz": "07", "Ağustos": "08",
        "Eylül": "09", "Ekim": "10", "Kasım": "11", "Aralık": "12"
    }

    # Split the date string into components
    day, month_name, year = date_str.split()
    
    # Map the Turkish month name to a numeric value
    month = month_mapping.get(month_name)
    
    return f"{year}-{month}-{day.zfill(2)}" if month else date_str

def process_info_fields(info_list):
    processed_info = {}
    for item in info_list:
        if 'key' in item and 'value' in item:  # Ensure both 'key' and 'value' exist
            key = item['key']
            value = item['value']

            # Convert 'net_square' and 'gross_square' values from "XX m2" to numeric values
            if key in ['net_square', 'gross_square'] and value and value.endswith("m2"):
                numeric_part = value[:-2].strip()  # Remove the " m2" part
                try:
                    # Convert the numeric part to an integer if possible, or a float if it contains decimals
                    processed_value = int(numeric_part) if numeric_part.isdigit() else float(numeric_part)
                    value = processed_value
                except ValueError:
                    print(f"Warning: Could not convert '{numeric_part}' to a numeric value for '{key}'.")

            # Convert dates from Turkish format to ISO format (YYYY-MM-DD)
            if key in ['created_at', 'updated_at'] and value is not None:
                value = convert_turkish_date_to_iso(value)
            
            processed_info[key] = value
    
    return processed_info


# Cleanse and preprocess data, retaining specified fields and applying transformations.
def cleanse_and_preprocess_data(data):
    cleansed_data = []
    for item in data:
        images = [validate_and_format_url(url) for url in item.get('images', [])]  
        title = normalize_text(item['title'])
        description = normalize_text(remove_html_tags(item.get('description', '')))  # Removing HTML tags
        
        if not images or not title:
            continue
        
        ilan_bitis = item.get('ilan_bitis')
        is_active = not bool(item.get('ilan_bitis'))

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
            'quickInfos': process_quickinfos(item.get('quickInfos', '')),
            'priceDetail': item['priceDetail'],
            'description': description,
            'info': info,
            'location': item['location'],
            'ilanda_kalis_suresi': item['ilanda_kalis_suresi'],
            'ilan_bitis': ilan_bitis,
            'is_active': is_active
        }
        
        cleansed_data.append(cleansed_item)
    return cleansed_data

# Remove duplicate entries based on their ID.
def remove_duplicates(data):
    unique_data = {}
    for item in data:
        unique_data[item['id']] = item
    return list(unique_data.values())

# Write processed data to a JSON file, ensuring it is UTF-8 encoded.
def write_json_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Main function to orchestrate the loading, processing, and saving of data.
def main():
    input_file_path = 'istanbul_emlakjet_all_records_updated.json'
    output_file_path = 'istanbul_emlakjet_all_records_clean.json'
    
    # Load the raw data from a file.
    raw_data = load_json_data(input_file_path)
    
    # Cleanse and preprocess the raw data.
    cleansed_data = cleanse_and_preprocess_data(raw_data)
    
    # Write the cleansed data to a new JSON file.
    write_json_data(output_file_path, cleansed_data)

if __name__ == '__main__':
    main()
