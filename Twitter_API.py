import tweepy
import credentials
import time

# Twitter API credentials
api_key = credentials.consumer_key
api_secret = credentials.consumer_secret
access_token = credentials.access_token
access_token_secret = credentials.access_token_secret

print(f"Loaded Credentials:")
print(f"Consumer Key: {api_key[:5]}*****")
print(f"Consumer Secret: {api_secret[:5]}*****")
print(f"Access Token: {access_token[:5]}*****")
print(f"Access Token Secret: {access_token_secret[:5]}*****")


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
        time.sleep(5)  # Ensure media is processed

    retries = 0
    while retries <= max_retries:
        try:
            if media_ids:
                response = client_v2.create_tweet(
                    text=tweet_text,
                    media_ids=media_ids
                )
            else:
                response = client_v2.create_tweet(text=tweet_text)

            print(f"Tweet posted successfully! URL: https://twitter.com/user/status/{response.data['id']}")
            return response
        except tweepy.Forbidden as e:
            print(f"Tweet with media failed: {e}")
            if media_ids:  # Retry without media
                print("Retrying tweet without media...")
                media_ids = []  # Clear media IDs
                retries = 0  # Reset retries for no-media attempt
            else:
                print("Forbidden error without media. Aborting.")
                break
        except tweepy.TooManyRequests as e:
            print(f"Rate limit reached: {e}")
            retries += 1
            time.sleep(retry_delay)
        except tweepy.TweepyException as e:
            print(f"Error posting tweet: {e}")
            break
