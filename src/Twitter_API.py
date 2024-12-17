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

            # Verify if response contains a valid tweet ID
            if response and response.data and "id" in response.data:
                tweet_url = f"https://twitter.com/user/status/{response.data['id']}"
                print(f"Tweet posted successfully! URL: {tweet_url}")
                tweet_posted = True
                return response  # Exit after successful tweet

        except tweepy.Forbidden as e:
            print(f"Tweet failed with Forbidden error: {e}")
            if media_ids:  # Retry without media
                print("Retrying tweet without media...")
                media_ids = []  # Clear media IDs
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
