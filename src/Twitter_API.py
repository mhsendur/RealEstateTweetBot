import tweepy
import credentials
import time

# Twitter API credentials
api_key = credentials.consumer_key
api_secret = credentials.consumer_secret
access_token = credentials.access_token
access_token_secret = credentials.access_token_secret

# Function to get Twitter API v1.1 connection
def get_twitter_conn_v1(api_key, api_secret, access_token, access_token_secret) -> tweepy.API:
    auth = tweepy.OAuth1UserHandler(api_key, api_secret)
    auth.set_access_token(access_token, access_token_secret)
    return tweepy.API(auth)

# Function to get Twitter API v2 connection
def get_twitter_conn_v2(api_key, api_secret, access_token, access_token_secret) -> tweepy.Client:
    return tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )

# Initialize connections
client_v1 = get_twitter_conn_v1(api_key, api_secret, access_token, access_token_secret)
client_v2 = get_twitter_conn_v2(api_key, api_secret, access_token, access_token_secret)


def upload_media_v1(image_files):
    """Upload media using Twitter API v1.1 and return media IDs."""
    media_ids = []
    for image_file in image_files[:4]:  # Twitter allows up to 4 images per tweet
        try:
            print(f"Uploading {image_file}...")
            media = client_v1.media_upload(image_file)
            print(f"Uploaded {image_file}, Media ID: {media.media_id}")

            # Wait for media to finish processing
            status = None
            while status != 'succeeded':
                print(f"Checking media processing status for Media ID: {media.media_id}")
                media_status = client_v1.get_media_upload_status(media.media_id)
                status = media_status.get('processing_info', {}).get('state', 'succeeded')
                if status == 'failed':
                    print(f"Media upload failed for {image_file}.")
                    break
                elif status != 'succeeded':
                    print("Media still processing, waiting 5 seconds...")
                    time.sleep(5)

            if status == 'succeeded':
                media_ids.append(str(media.media_id))
        except Exception as e:
            print(f"Error uploading {image_file}: {e}")
    return media_ids


def send_tweet_v2(tweet_text, image_files=None, max_retries=3, retry_delay=5):
    """Post a tweet with up to 4 media files using Twitter API v2."""
    media_ids = upload_media_v1(image_files) if image_files else []
    retries = 0

    while retries <= max_retries:
        try:
            if media_ids:
                print("Posting tweet with media...")
                response = client_v2.create_tweet(text=tweet_text, media_ids=media_ids)
            else:
                print("Posting tweet without media...")
                response = client_v2.create_tweet(text=tweet_text)

            # Verify the response
            if response and "id" in response.data:
                tweet_id = response.data["id"]
                print(f"Tweet posted successfully! URL: https://twitter.com/user/status/{tweet_id}")
                return response  # Exit if successful
            else:
                print("Response did not contain a valid tweet ID. Retrying...")

        except tweepy.Forbidden as e:
            print(f"Forbidden error: {e}. Retrying without media...")
            media_ids = []  # Clear media for retry
            retries = 0  # Reset retry count for text-only tweets
        except tweepy.TooManyRequests as e:
            print(f"Rate limit reached. Waiting for {retry_delay} seconds...")
            time.sleep(retry_delay)
        except tweepy.TweepyException as e:
            print(f"Error posting tweet: {e}")
            break  # Stop on other errors
        retries += 1

    print("Failed to post tweet after all retries.")
    return None
