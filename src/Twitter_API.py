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
    tweet_posted = False  # Flag to confirm successful posting
    retries = 0  # Retry counter

    # Step 1: Try to upload media if available
    media_ids = []
    if image_files:
        print("Uploading media...")
        media_ids = upload_media_v1(image_files)  # Upload media and get media IDs
        print(f"Media IDs: {media_ids}")

    while retries <= max_retries and not tweet_posted:
        try:
            # Step 2: Post the tweet with or without media
            if media_ids:
                print("Attempting to post tweet with media...")
                response = client_v2.create_tweet(text=tweet_text, media_ids=media_ids)
            else:
                print("Attempting to post text-only tweet...")
                response = client_v2.create_tweet(text=tweet_text)

            # Step 3: Validate the response
            if response and "id" in response.data:
                tweet_url = f"https://twitter.com/user/status/{response.data['id']}"
                print(f"Tweet posted successfully: {tweet_url}")
                tweet_posted = True  # Mark as successfully posted
                return response  # Exit function after successful post
            else:
                print("Failed to get a valid tweet ID from the response. Retrying...")

        except tweepy.Forbidden as e:
            print(f"Forbidden error: {e}")
            if media_ids:
                print("Retrying tweet without media...")
                media_ids = []  # Clear media IDs to retry without images
                retries = 0  # Reset retries for text-only tweet
            else:
                print("Forbidden error without media. Aborting.")
                break  # Stop retries if forbidden persists without media

        except tweepy.TooManyRequests as e:
            print(f"Rate limit reached. Retrying after {retry_delay} seconds...")
            time.sleep(retry_delay)
            retries += 1

        except tweepy.TweepyException as e:
            print(f"Error posting tweet: {e}")
            break  # Stop on unexpected exceptions

        except Exception as e:
            print(f"Unexpected error: {e}")
            break

        retries += 1

    # Step 4: Log final failure if tweet still not posted
    if not tweet_posted:
        print("Failed to post tweet after all retries.")
    return None
