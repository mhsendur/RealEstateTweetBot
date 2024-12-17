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
        time.sleep(5)  # Ensure media is processed

    retries = 0
    tweet_posted = False  # Flag to check if the tweet was successfully posted

    while retries <= max_retries:
        try:
            # Attempt to post a tweet
            if media_ids:
                print("Posting tweet with media...")
                response = client_v2.create_tweet(
                    text=tweet_text,
                    media_ids=media_ids
                )
            else:
                print("Posting tweet without media...")
                response = client_v2.create_tweet(text=tweet_text)

            # Validate response
            if response and response.data and "id" in response.data:
                tweet_id = response.data['id']
                tweet_url = f"https://twitter.com/your_username/status/{tweet_id}"
                print(f"Tweet successfully posted! URL: {tweet_url}")
                print(f"Full Response: {response.data}")
                return tweet_url  # Return tweet URL on success
            else:
                print("Failed to get valid tweet ID in the response.")
                return None

        except tweepy.Forbidden as e:
            print(f"Tweet failed with Forbidden error: {e}")
            if media_ids:
                print("Retrying tweet without media...")
                media_ids = []  # Clear media IDs
                retries = 0  # Reset retries for no-media attempt
            else:
                print("Forbidden error without media. Aborting.")
                break  # Stop retries if Forbidden persists

        except tweepy.TooManyRequests as e:
            print(f"Rate limit reached. Retrying after {retry_delay} seconds...")
            retries += 1
            time.sleep(retry_delay)

        except tweepy.TweepyException as e:
            print(f"Error posting tweet: {e}")
            break  # Stop retries for unexpected exceptions

        except Exception as e:
            print(f"Unexpected error: {e}")
            break

        retries += 1

    print("Failed to post tweet after all retries.")
    return None  # Return None if tweet fails
