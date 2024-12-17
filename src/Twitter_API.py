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
            media_ids.append(str(media.media_id))
            print(f"Uploaded {image_file}, Media ID: {media.media_id}")
        except Exception as e:
            print(f"Error uploading {image_file}: {e}")
    return media_ids


def send_tweet_v2(tweet_text, image_files=None, max_retries=3, retry_delay=5):
    """Post a tweet with up to 4 media files using Twitter API v2."""
    media_ids = upload_media_v1(image_files) if image_files else []
    if media_ids:
        print("Waiting for media processing to finalize...")
        time.sleep(5)  # Ensure media is processed before tweeting

    retries = 0
    tweet_posted = False  # Flag to check if tweet was successfully posted

    while retries <= max_retries:
        try:
            # Attempt to post a tweet with media if media_ids exist
            if media_ids:
                print("Posting tweet with media...")
                response = client_v2.create_tweet(
                    text=tweet_text,
                    media_ids=media_ids
                )
            else:
                print("Posting tweet without media...")
                response = client_v2.create_tweet(text=tweet_text)

            # Verify response and log tweet URL
            if response and "id" in response.data:
                print(f"Tweet posted successfully! URL: https://twitter.com/user/status/{response.data['id']}")
                tweet_posted = True  # Mark tweet as posted successfully
                return response  # Exit after successful tweet

        except tweepy.Forbidden as e:
            print(f"Tweet failed with Forbidden error: {e}")
            if media_ids:
                print("Retrying tweet without media...")
                media_ids = []  # Clear media IDs for retry without images
                retries = 0  # Reset retries when switching to text-only tweet
            else:
                print("Forbidden error occurred without media. Aborting.")
                break  # Stop retries if Forbidden persists without media

        except tweepy.TooManyRequests as e:
            print(f"Rate limit reached. Retrying after {retry_delay} seconds...")
            retries += 1
            time.sleep(retry_delay)

        except tweepy.TweepyException as e:
            print(f"Error posting tweet: {e}")
            break  # Stop retries for unexpected exceptions

        except Exception as e:
            print(f"Unexpected error: {e}")
            break  # Catch-all for unexpected errors

        # Increment retries if tweet not yet posted
        retries += 1

    # Log failure if tweet still not posted
    if not tweet_posted:
        print("Failed to post tweet after all retries.")
    return None  # Return None if tweet fails entirely
