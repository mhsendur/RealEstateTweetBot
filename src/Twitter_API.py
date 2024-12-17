import tweepy
import time
import credentials

# Initialize client_v2 globally
client_v2 = tweepy.Client(
    consumer_key=credentials.consumer_key,
    consumer_secret=credentials.consumer_secret,
    access_token=credentials.access_token,
    access_token_secret=credentials.access_token_secret,
)

def send_tweet_v2(tweet_text, image_urls=None, max_retries=3, retry_delay=60):
    """Post a tweet with media using Twitter API v2, with retry logic."""
    retries = 0
    media_ids = image_urls if image_urls else []  # Directly pass the image URLs if already hosted

    while retries <= max_retries:
        try:
            if media_ids:
                # Post the tweet with media
                print("Attempting to post tweet with media...")
                response = client_v2.create_tweet(
                    text=tweet_text,
                    media_ids=media_ids  # Use media_ids directly
                )
            else:
                # Post the tweet without media
                print("Attempting to post tweet without media...")
                response = client_v2.create_tweet(text=tweet_text)

            # Verify response and print success message
            if response and "data" in response and "id" in response.data:
                tweet_id = response.data['id']
                print(f"Tweet posted successfully: https://twitter.com/user/status/{tweet_id}")
                return tweet_id  # Return tweet ID on success

            print("Failed to post tweet. Invalid response.")
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
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

        retries += 1

    print("Failed to post tweet after all retries.")
    return None  # Return None if tweet failed
