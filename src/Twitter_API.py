import tweepy
import credentials
import time

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

def upload_media_v1(image_files):
    """Upload media using Twitter API v1.1 and return media IDs."""
    media_ids = []
    for image_file in image_files[:4]:  # Twitter allows up to 4 images per tweet
        try:
            media = api_v1.media_upload(image_file)
            media_ids.append(media.media_id)
            print(f"Uploaded {image_file}, media ID: {media.media_id_string}")
        except Exception as e:
            print(f"Error uploading {image_file}: {e}")
    return media_ids

def send_tweet_v2(tweet_text, image_urls=None, max_retries=3, retry_delay=60):
    """Post a tweet with media using Twitter API v2, with retry logic."""
    retries = 0
    media_ids = image_urls if image_urls else []  # Directly pass the image URLs if already hosted

    while retries <= max_retries:
        try:
            if media_ids:
                # Post the tweet with media
                response = client_v2.create_tweet(
                    text=tweet_text,
                    media_ids=media_ids  # Use media_ids directly
                )
            else:
                # Post the tweet without media
                response = client_v2.create_tweet(text=tweet_text)

            print(f"Tweet posted successfully: https://twitter.com/user/status/{response.data['id']}")
            return  # Exit the retry loop after a successful post
        except tweepy.TooManyRequests as e:
            print(f"Rate limit reached: {e}")
            retries += 1
            if retries > max_retries:
                print("Maximum retries reached. Aborting.")
                break
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        except tweepy.TweepyException as e:
            print(f"Error posting tweet: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.json()}")
            break  # Non-rate limit errors won't be retried
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
