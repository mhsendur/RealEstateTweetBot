import tweepy
import time
import credentials
import os
import datetime
import random

# Initialize Twitter API clients
client_v2 = tweepy.Client(
    consumer_key=credentials.consumer_key,
    consumer_secret=credentials.consumer_secret,
    access_token=credentials.access_token,
    access_token_secret=credentials.access_token_secret,
)

auth = tweepy.OAuth1UserHandler(
    consumer_key=credentials.consumer_key,
    consumer_secret=credentials.consumer_secret,
    access_token=credentials.access_token,
    access_token_secret=credentials.access_token_secret,
)
client_v1 = tweepy.API(auth)

def upload_images_to_twitter(image_files):
    """Upload images to Twitter and return media IDs with pauses between uploads."""
    media_ids = []
    for image_file in image_files:
        try:
            print(f"Uploading {image_file} to Twitter...")
            response = client_v1.media_upload(image_file)
            media_ids.append(response.media_id_string)
            print(f"Uploaded {image_file}, Media ID: {response.media_id_string}")
            
            # Add a pause after each upload to reduce API activity spikes
            pause_time = random.randint(5, 15)  # Pause for 5 to 15 seconds
            print(f"Pausing for {pause_time} seconds before the next upload.")
            time.sleep(pause_time)
        except Exception as e:
            print(f"Failed to upload {image_file}: {e}")
    return media_ids


def send_tweet_v2(tweet_text, image_files=None, max_retries=5):
    """Post a tweet with media using Twitter API v2 with fallback logic."""
    retries = 0
    backoff_time = 5
    media_ids = upload_images_to_twitter(image_files) if image_files else []

    while retries <= max_retries:
        try:
            if media_ids:
                print("Attempting to post tweet with media...")
                response = client_v2.create_tweet(text=tweet_text, media_ids=media_ids)
            else:
                print("Attempting to post tweet without media...")
                response = client_v2.create_tweet(text=tweet_text)

            if response and "data" in response and "id" in response.data:
                tweet_id = response.data['id']
                print(f"Tweet posted successfully! URL: https://twitter.com/user/status/{tweet_id}")
                return tweet_id

        except tweepy.Forbidden as e:
            print(f"Forbidden error: {e}")
            if media_ids:
                print("Retrying without media...")
                media_ids = []  # Clear media IDs for retry
            else:
                print("Forbidden error persists without media. Aborting.")
                break

        except tweepy.TooManyRequests as e:
            print(f"Rate limit reached. Retrying after backoff...")
            time.sleep(backoff_time)
            backoff_time *= 2
            retries += 1
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

        # Add a random delay to mimic human behavior
        pause_time = random.randint(10, 20)
        print(f"Pausing for {pause_time} seconds between API actions...")
        time.sleep(pause_time)

    print("Failed to post tweet after all retries.")
    return None

