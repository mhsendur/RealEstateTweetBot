import tweepy
import time
import credentials


def send_tweet_v2(tweet_text, retry_limit=3):
    """Post a tweet with retry logic for rate-limiting errors and enhanced error handling."""
    client = tweepy.Client(
        consumer_key=credentials.consumer_key,
        consumer_secret=credentials.consumer_secret,
        access_token=credentials.access_token,
        access_token_secret=credentials.access_token_secret
    )
    
    retries = 0
    while retries < retry_limit:
        try:
            # Post the tweet
            response = client.create_tweet(text=tweet_text)
            print("Tweet posted successfully!")
            print(f"Tweet URL: https://twitter.com/user/status/{response.data['id']}")
            return  # Exit after a successful post

        except tweepy.TooManyRequests as e:
            retries += 1
            # Calculate wait time using the x-rate-limit-reset header
            reset_time = int(e.response.headers.get("x-rate-limit-reset", 0))
            if reset_time > 0:
                wait_time = max(reset_time - int(time.time()), 60)
            else:
                wait_time = 900  # Default to 15 minutes if reset time is unavailable
            print(f"Rate limit exceeded. Retrying in {wait_time} seconds... (Retry {retries}/{retry_limit})")
            time.sleep(wait_time)

        except tweepy.TweepyException as e:
            # Handle other Tweepy exceptions
            print(f"Error posting tweet: {e}")
            break

        except Exception as e:
            # Handle any other exceptions
            print(f"Unexpected error: {e}")
            break

    # If retries exceeded
    if retries >= retry_limit:
        print("Failed to post tweet after maximum retries. Please try again later.")
