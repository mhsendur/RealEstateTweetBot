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


def send_tweet_v2(tweet_text, image_files=None, max_retries=3, retry_delay=5):
    """Post a tweet with media using Twitter API v2."""
    retries = 0
    media_ids = []

    # Upload media if images are provided
    if image_files:
        media_ids = upload_images_to_twitter(image_files)

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
        except tweepy.TooManyRequests as e:
            print(f"Rate limit reached: {e}. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        except tweepy.Forbidden as e:
            print(f"Forbidden error: {e}")
            if media_ids:
                print("Retrying tweet without media...")
                media_ids = []  # Remove media IDs and retry without images
                retries = 0  # Reset retries
            else:
                print("Tweet failed without media. Aborting.")
                break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

        retries += 1

    print("Failed to post tweet after all retries.")
    return None
