import tweepy
import time
import credentials


def send_tweet_v2(tweet_text, image_urls=None, max_retries=3, retry_delay=60):
    """1Post a tweet with media using Twitter API v2, with retry logic."""
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

