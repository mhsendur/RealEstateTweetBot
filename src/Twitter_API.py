import tweepy
import time
import credentials

# Load Twitter API credentials
api_key = credentials.consumer_key
api_secret = credentials.consumer_secret
access_token = credentials.access_token
access_token_secret = credentials.access_token_secret

# Log loaded credentials (partially masked)
print("Loaded Credentials:")
print(f"Consumer Key: {api_key[:5]}*****")
print(f"Consumer Secret: {api_secret[:5]}*****")
print(f"Access Token: {access_token[:5]}*****")
print(f"Access Token Secret: {access_token_secret[:5]}*****")
def send_tweet_v2(tweet_text, image_files=None, max_retries=3, retry_delay=5):
    """Post a tweet with up to 4 media files using Twitter API v2."""
    media_ids = upload_media_v1(image_files) if image_files else []
    if media_ids:
        print("Waiting for media processing to finalize...")
        time.sleep(5)  # Allow media processing

    retries = 0
    while retries <= max_retries:
        try:
            if media_ids:
                print("Attempting to post tweet with media...")
                response = client_v2.create_tweet(text=tweet_text, media_ids=media_ids)
            else:
                print("Attempting to post tweet without media...")
                response = client_v2.create_tweet(text=tweet_text)

            # Check response and validate tweet URL
            if response and "data" in response and "id" in response.data:
                tweet_id = response.data['id']
                tweet_url = f"https://twitter.com/user/status/{tweet_id}"
                print(f"Tweet successfully posted! URL: {tweet_url}")
                print(f"Full Twitter API Response: {response.data}")
                return tweet_url  # Return the URL for the posted tweet

            # If response is invalid
            print("Twitter response did not contain a valid tweet ID. Full response:")
            print(response)
            retries += 1
        except tweepy.Forbidden as e:
            print(f"Forbidden error: {e}")
            if media_ids:
                print("Retrying without media...")
                media_ids = []  # Clear media IDs and retry without media
                retries = 0  # Reset retries for no-media attempt
            else:
                print("Forbidden error persists without media. Aborting.")
                break
        except tweepy.TooManyRequests as e:
            print(f"Rate limit reached. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            retries += 1
        except Exception as e:
            print(f"Unexpected error: {e}")
            break  # Stop for unexpected errors

        retries += 1

    print("Failed to post tweet after all retries.")
    return None
