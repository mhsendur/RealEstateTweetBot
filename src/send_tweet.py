import json
import OpenAI_API
import Twitter_API
import random
import requests
import time
from google.cloud import storage
import os
import requests

# Google Cloud Storage Configuration
GCS_BUCKET_NAME = "real-estate-bot-bucket"
TOP_URLS_FILE = "top_listings_ids_and_urls.txt"
LISTINGS_JSON_FILE = "istanbul_emlakjet_all_records_updated.json"

client_v2 = Twitter_API.client_v2

# Initialize the GCS client
storage_client = storage.Client()


def download_from_gcs(bucket_name, filename):
    """Download a file from Google Cloud Storage."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    if blob.exists():
        return blob.download_as_text()
    else:
        print(f"File {filename} not found in bucket {bucket_name}.")
        return None


def upload_to_gcs(bucket_name, filename, content):
    """Upload content to Google Cloud Storage."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(content, content_type="text/plain")
    print(f"Uploaded {filename} to bucket {bucket_name}.")

def download_images(image_urls, max_images=4):
    """Download up to 4 images from URLs and save them locally."""
    image_files = []
    for i, url in enumerate(image_urls[:max_images]):
        filename = f"downloaded_image_{i+1}.jpg"
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(filename, 'wb') as f:
                f.write(response.content)
            # Check file size
            if os.path.getsize(filename) > 5 * 1024 * 1024:  # 5 MB
                print(f"Skipping {filename}: exceeds 5 MB.")
                os.remove(filename)
                continue
            image_files.append(filename)
            print(f"Downloaded: {filename}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")
    return image_files


def load_top_urls():
    """Load the top URLs and their IDs from GCS."""
    try:
        content = download_from_gcs(GCS_BUCKET_NAME, TOP_URLS_FILE)
        if content:
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            top_urls = []
            for i in range(0, len(lines), 2):  # Process in pairs of ID and URL
                try:
                    id_line = lines[i]
                    url_line = lines[i + 1]
                    if id_line.startswith("ID:") and url_line.startswith("URL:"):
                        listing_id = id_line.replace("ID:", "").strip()
                        url = url_line.replace("URL:", "").strip()
                        if listing_id and url:
                            top_urls.append({"id": listing_id, "url": url})
                    else:
                        print(f"Invalid entry at line {i + 1}. Skipping...")
                except IndexError:
                    print(f"Incomplete entry at line {i + 1}. Skipping...")
            return top_urls
        else:
            return []
    except Exception as e:
        print(f"Error loading top URLs from GCS: {e}")
        return []


def save_top_urls(top_urls):
    """Save the updated top URLs back to GCS."""
    try:
        content = "Top Listings:\n" + "=" * 40 + "\n\n"
        for item in top_urls:
            content += f"ID: {item['id']}\nURL: {item['url']}\n\n"
        upload_to_gcs(GCS_BUCKET_NAME, TOP_URLS_FILE, content)
    except Exception as e:
        print(f"Error saving top URLs to GCS: {e}")


def load_listings_from_json():
    """Load all listings from the JSON file in GCS."""
    try:
        content = download_from_gcs(GCS_BUCKET_NAME, LISTINGS_JSON_FILE)
        if content:
            return json.loads(content)
        else:
            return []
    except Exception as e:
        print(f"Error loading listings JSON from GCS: {e}")
        return []


# Rest of the Code (Unchanged)
def find_listing_by_id(listings, listing_id):
    """Find a listing by its ID in the JSON data."""
    for listing in listings:
        if str(listing.get("id", "")) == str(listing_id):  # Ensure type consistency
            return listing
    return None

POSTED_IDS_FILE = "posted_ids.txt"

def load_posted_ids():
    """Load the IDs of already posted listings from a file."""
    if os.path.exists(POSTED_IDS_FILE):
        with open(POSTED_IDS_FILE, "r") as file:
            return set(line.strip() for line in file)
    return set()

def save_posted_id(listing_id):
    """Save a posted listing ID to the file."""
    with open(POSTED_IDS_FILE, "a") as file:
        file.write(f"{listing_id}\n")


def is_listing_active(url):
    """
    Check if a listing is still active by comparing the requested URL to the final URL.
    
    Args:
        url (str): The listing URL to check.

    Returns:
        bool: True if the listing is active, False otherwise.
    """
    try:
        # Make a request to the URL and allow redirects
        response = requests.get(url, allow_redirects=True, timeout=10)

        # Check if the URL after redirects matches the original
        if response.url != url:
            print(f"Listing is closed. Original URL: {url}, Redirected URL: {response.url}")
            return False
        return True
    except requests.RequestException as e:
        print(f"Error checking listing URL {url}: {e}")
        return False

def process_random_listing(max_retries=5, retry_delay=60):
    """Process and tweet a random listing, ensuring no duplicates and active status."""
    posted_ids = load_posted_ids()
    top_urls = load_top_urls()
    listings = load_listings_from_json()

    if not top_urls:
        print("No listings found in the file. Exiting...")
        return

    for _ in range(max_retries):
        # Randomly select a listing
        selected_listing = random.choice(top_urls)
        listing_id = selected_listing["id"]
        listing_url = selected_listing["url"]

        # Skip if the listing has already been tweeted
        if listing_id in posted_ids:
            print(f"Listing ID {listing_id} has already been tweeted. Skipping...")
            continue

        # Check if the listing is still active
        if not is_listing_active(listing_url):
            print(f"Listing ID {listing_id} is closed. Skipping...")
            continue

        try:
            # Proceed to process the listing (existing logic)
            listing = find_listing_by_id(listings, listing_id)
            if not listing:
                print(f"Listing ID {listing_id} not found in the JSON data. Skipping...")
                continue

            # Extract details for the tweet
            title = listing.get("title", "N/A")
            price = listing.get("priceDetail", {}).get("price", "N/A")
            location = listing.get("locationSummary", "N/A")
            description = listing.get("description", "No description available")
            images = listing.get("imagesFullPath", [])

            print(f"Processing Listing ID: {listing_id}, Title: {title}")

            # Generate tweet text
            raw_data = f"Başlık: {title}\nFiyat: {price} TL\nKonum: {location}\nAçıklama: {description}"
            tweet_text = OpenAI_API.create_tweet_text(raw_data)
            tweet_text += f"\n🔗 Link: {listing_url}"

            # Download images
            image_files = download_images(images)

            # Post the tweet
            print("Sending the tweet...")
            Twitter_API.send_tweet_v2(tweet_text, image_files)
            print("Tweet successfully sent.")
            save_posted_id(listing_id)  # Mark as posted
            return  # Exit after successful tweet
        except Exception as e:
            print(f"Error processing Listing ID {listing_id}: {e}")
        finally:
            # Cleanup downloaded images
            for image_file in image_files:
                if os.path.exists(image_file):
                    os.remove(image_file)
                    print(f"Deleted temporary file: {image_file}")

    print("Failed to find an active and untweeted listing after all retries.")

def send_tweet():
    process_random_listing()


if __name__ == "__main__":
    send_tweet()
