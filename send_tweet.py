import json
import OpenAI_API
import Twitter_API
import random
import requests
import time 

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
            image_files.append(filename)
            print(f"Downloaded: {filename}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")
    return image_files

def preview_tweet(tweet_text, image_files=None):
    """Preview the tweet before posting."""
    print("\n--- Preview Tweet ---")
    print(tweet_text)
    if image_files:
        print(f"Attached images: {', '.join(image_files)}")
    else:
        print("No images attached.")
    print("---------------------")
    confirm = input("Post this tweet? (y/n): ").strip().lower()
    return confirm == 'y'


def load_top_urls(file_name="top_listings_ids_and_urls.txt"):
    """Load the top URLs and their IDs from the text file."""
    top_urls = []
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            lines = [line.strip() for line in file if line.strip()]
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
                            print(f"Missing or empty ID/URL at line {i + 1}. Skipping...")
                    else:
                        print(f"Invalid entry found at line {i + 1}. Skipping...")
                except IndexError:
                    print(f"Incomplete entry at line {i + 1}. Skipping...")
        return top_urls
    except Exception as e:
        print(f"Error reading top URLs file: {e}")
        return []


def load_listings_from_json(file_name="istanbul_emlakjet_all_records_updated.json"):
    """Load all listings from the JSON file."""
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return []


def find_listing_by_id(listings, listing_id):
    """Find a listing by its ID in the JSON data."""
    for listing in listings:
        if str(listing.get("id", "")) == str(listing_id):  # Ensure type consistency
            return listing
    return None


def process_top_listings(top_urls_file="top_listings_ids_and_urls.txt", json_file="istanbul_emlakjet_all_records_updated.json"):
    """Process the top listings using the URLs file and the JSON file."""
    top_urls = load_top_urls(top_urls_file)
    listings = load_listings_from_json(json_file)

    for top_url in top_urls:
        try:
            listing_id = top_url["id"]
            url = f"https://www.emlakjet.com{top_url['url']}"

            # Find the corresponding listing in the JSON data
            listing = find_listing_by_id(listings, listing_id)
            if not listing:
                print(f"Listing ID {listing_id} not found in the JSON data. Skipping...")
                continue

            # Extract details for the tweet
            title = listing.get("title", "N/A")
            price = listing.get("priceDetail", {}).get("price", "N/A")
            location = listing.get("locationSummary", "N/A")
            description = listing.get("description", "No description available")

            # Download images
            image_files = download_images(listing.get("imagesFullPath", []))

            print(f"Processing Listing ID: {listing_id}, Title: {title}")

            # Format raw data for the tweet
            raw_data = f"Başlık: {title}\nFiyat: {price} TL\nKonum: {location}\nAçıklama: {description}"

            # Generate the tweet text using OpenAI
            try:
                tweet_text = OpenAI_API.create_tweet_text(raw_data)
            except Exception as e:
                print(f"Error generating tweet text for Listing ID {listing_id}: {e}")
                continue

            # Preview the tweet
            if not preview_tweet(tweet_text, image_files):
                print("Tweet skipped.")
                continue

            # Post the tweet using Twitter API
            Twitter_API.send_tweet_v2(tweet_text, image_files)

        except Exception as e:
            print(f"Error processing Listing ID {listing_id}: {e}")


def process_first_listing(top_urls_file="top_listings_ids_and_urls.txt"):
    """Process and tweet the first listing."""
    top_urls = load_top_urls(top_urls_file)

    if not top_urls:
        print("No listings found in the file. Exiting...")
        return

    # Get the first listing
    first_listing = top_urls[0]
    listing_id = first_listing["id"]
    url = f"https://www.emlakjet.com{first_listing['url']}"

    try:
        # Use OpenAI to generate tweet content
        raw_data = f"Listing ID: {listing_id}\nURL: {url}"
        tweet_text = OpenAI_API.create_tweet_text(raw_data)

        # Preview the tweet
        if not preview_tweet(tweet_text):
            print("Tweet skipped.")
            return

        # Post the tweet
        Twitter_API.send_tweet_v2(tweet_text)
    except Exception as e:
        print(f"Error processing Listing ID {listing_id}: {e}")

def save_top_urls(file_path, top_urls):
    """Save the updated list of URLs back to the text file in the required format."""
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(f"Top {len(top_urls)} Best Valued Listings:\n")
            file.write("=" * (len(top_urls) * 2) + "\n")
            for listing in top_urls:
                file.write(f"ID: {listing['id']}\n")
                file.write(f"URL: {listing['url']}\n\n")
        print(f"Successfully saved {len(top_urls)} listings to {file_path}")
    except Exception as e:
        print(f"Error saving to file {file_path}: {e}")

def process_random_listing(top_urls_file="top_listings_ids_and_urls.txt", json_file="istanbul_emlakjet_all_records_updated.json"):
    """Process a random listing, generate a tweet, and post with up to 4 images."""
    top_urls = load_top_urls(top_urls_file)
    listings = load_listings_from_json(json_file)

    if not top_urls:
        print("No listings found. Exiting...")
        return

    # Select a random listing
    selected_listing = random.choice(top_urls)
    listing_id = selected_listing["id"]
    url = f"{selected_listing['url']}"

    # Find the listing details
    listing = find_listing_by_id(listings, listing_id)
    if not listing:
        print(f"Listing ID {listing_id} not found in JSON data.")
        return

    # Extract listing details
    title = listing.get("title", "N/A")
    price = listing.get("priceDetail", {}).get("price", "N/A")
    location = listing.get("locationSummary", "N/A")
    description = listing.get("description", "No description available")
    images = listing.get("imagesFullPath", [])

    print(f"Processing Listing ID: {listing_id}, Title: {title}")

    # Download images
    image_files = download_images(images)

    # Generate tweet text using OpenAI
    raw_data = f"Başlık: {title}\nFiyat: {price} TL\nKonum: {location}\nAçıklama: {description}"
    try:
        tweet_text = OpenAI_API.create_tweet_text(raw_data)
        tweet_text += f"\n🔗 Link: {url}"
    except Exception as e:
        print(f"Error generating tweet text: {e}")
        return

    # Post the tweet
    Twitter_API.send_tweet_v2(tweet_text, image_files)

def send_tweet():
    # process_first_listing()
    # process_top_listings()
    process_random_listing()


if __name__ == "__main__":
    send_tweet()
