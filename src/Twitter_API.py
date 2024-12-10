import tweepy
import credentials
import time
import os
import requests

# Initialize v1.1 API client for media upload
auth = tweepy.OAuth1UserHandler(
    consumer_key=credentials.consumer_key,
    consumer_secret=credentials.consumer_secret,
    access_token=credentials.access_token,
    access_token_secret=credentials.access_token_secret,
)
api_v1 = tweepy.API(auth)

# Initialize v2 API client for creating tweets
client_v2 = tweepy.Client(
    consumer_key=credentials.consumer_key,
    consumer_secret=credentials.consumer_secret,
    access_token=credentials.access_token,
    access_token_secret=credentials.access_token_secret,
)

def upload_media_v1(image_urls):
    """Upload media using Twitter API v1.1 and return media IDs."""
    media_ids = []
    for i, url in enumerate(image_urls[:4]):  # Limit to 4 images (Twitter's limit)
        temp_filename = f"temp_image_{i}.jpg"
        try:
            # Download the image from the URL
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Save the image temporarily
            with open(temp_filename, 'wb') as temp_file:
                for chunk in response.iter_content(1024):
                    temp_file.write(chunk)
            
            # Upload the image to Twitter
            media = api_v1.media_upload(filename=temp_filename)
            media_ids.append(media.media_id)
            print(f"Uploaded image from {url}, media ID: {media.media_id}")
        except Exception as e:
            print(f"Error uploading media from {url}: {e}")
        finally:
            # Clean up: Remove the temporary file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
                print(f"Deleted temporary file: {temp_filename}")
    return media_ids

def send_tweet_v2(tweet_text, image_urls=None, max_retries=3, retry_delay=60):
    """Post a tweet with media using Twitter API v2, with retry logic."""
    retries = 0
    media_ids = upload_media_v1(image_urls) if image_urls else []

    while retries <= max_retries:
        try:
            if media_ids:
                # Post the tweet with media
                response = client_v2.create_tweet(
                    text=tweet_text,
                    media_ids=media_ids
                )
            else:
                # Post the tweet without media
                response = client_v2.create_tweet(text=tweet_text)

            print(f"Tweet posted successfully: https://twitter.com/user/status/{response.data['id']}")
            return True  # Exit the retry loop after a successful post

        except tweepy.TooManyRequests as e:
            print(f"Rate limit reached: {e}")
            retries += 1
            if retries > max_retries:
                print("Maximum retries reached. Aborting.")
                return False
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

        except tweepy.TweepyException as e:
            print(f"Error posting tweet: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.json()}")
            return False  # Exit on non-rate limit errors

        except Exception as e:
            print(f"Unexpected error: {e}")
            return False  # Exit on unexpected errors
