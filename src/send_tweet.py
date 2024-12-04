import json
import OpenAI_API
import Twitter_API
import random
import requests
import time


def download_images(image_urls, max_images=4):
    """Download images from URLs and save them locally."""
    image_files = []
    for i, url in enumerate(image_urls[:max_images]):
        filename = f"downloaded_image_{i+1}.jpg"
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(filename, 'wb') as f:
                f.write(response.content)
            image_files.append(filename)
        except Exception as e:
            print(f"Error downloading {url}: {e}")
    return image_files


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


def process_random_listing(top_urls_file="top_listings_ids_and_urls.txt", json_file="istanbul_emlakjet_all_records_updated.json", max_retries=3, retry_delay=60):
    """Process and tweet a random listing, then remove it from the list with retry logic."""
    top_urls = load_top_urls(top_urls_file)
    listings = load_listings_from_json(json_file)

    if not top_urls:
        print("No listings found in the file. Exiting...")
        return

    # Randomly select a listing from the list
    selected_listing = random.choice(top_urls)
    listing_id = selected_listing["id"]
    url = f"https://www.emlakjet.com{selected_listing['url']}"

    try:
        # Find the corresponding listing in the JSON data
        listing = find_listing_by_id(listings, listing_id)
        if not listing:
            print(f"Listing ID {listing_id} not found in the JSON data. Skipping...")
            return

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
            tweet_text += f"\n🔗 Link: {url}"  # Append the hardcoded link
        except Exception as e:
            print(f"Error generating tweet text for Listing ID {listing_id}: {e}")
            return

        # Retry logic for posting the tweet
        retries = 0
        while retries <= max_retries:
            try:
                Twitter_API.send_tweet_v2(tweet_text, image_files)
                print("Tweet posted successfully!")
                break  # Exit loop on success
            except Twitter_API.TooManyRequests as e:
                print(f"Rate limit reached: {e}")
                retries += 1
                if retries > max_retries:
                    print("Maximum retries reached. Aborting.")
                    break
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            except Exception as e:
                print(f"Error posting tweet: {e}")
                break  # Stop on other errors

        # Remove the selected listing from the list
        top_urls.remove(selected_listing)

        # Save the updated list back to the file
        save_top_urls(top_urls_file, top_urls)

        print(f"Successfully processed and tweeted Listing ID {listing_id}.")
    except Exception as e:
        print(f"Error processing Listing ID {listing_id}: {e}")


def send_tweet():
    process_random_listing()


if __name__ == "__main__":
    send_tweet()
