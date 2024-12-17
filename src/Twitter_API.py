import tweepy
import time
import credentials
import os

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
    """Upload images to Twitter and return media IDs."""
    media_ids = []
    for image_file in image_files:
        try:
            print(f"Uploading {image_file} to Twitter...")
            response = client_v1.media_upload(image_file)
            media_ids.append(response.media_id_string)
            print(f"Uploaded {image_file}, Media ID: {response.media_id_string}")
        except Exception as e:
            print(f"Failed to upload {image_file}: {e}")
    return media_ids

import tweepy
import time
import datetime

def send_tweet_v2(tweet_text, image_files=None, max_retries=5):
    """Post a tweet with media using Twitter API v2 with rate limit monitoring."""
    retries = 0
    backoff_time = 5  # Initial backoff time in seconds

    # Upload images if provided
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
            else:
                print("Failed to post tweet. Invalid response.")
                return None

        except tweepy.TooManyRequests as e:
            print(f"Rate limit reached. Retrying after checking reset time...")
            if e.response and "x-rate-limit-reset" in e.response.headers:
                reset_time = int(e.response.headers['x-rate-limit-reset'])
                reset_dt = datetime.datetime.fromtimestamp(reset_time)
                wait_time = (reset_dt - datetime.datetime.now()).total_seconds()
                print(f"Rate limit resets at: {reset_dt}. Waiting for {wait_time:.2f} seconds...")
                time.sleep(wait_time + 1)  # Add 1 second buffer
            else:
                print("No rate limit reset time found. Retrying with exponential backoff.")
                time.sleep(backoff_time)
                backoff_time *= 2
            retries += 1

        except Exception as e:
            print(f"Unexpected error: {e}")
            break

    print("Failed to post tweet after all retries.")
    return None
