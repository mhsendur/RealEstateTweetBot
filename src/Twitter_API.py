import tweepy
import credentials

# Load Twitter API credentials
api_key = credentials.consumer_key
api_secret = credentials.consumer_secret
access_token = credentials.access_token
access_token_secret = credentials.access_token_secret

# Initialize Twitter v2 API Client
client_v2 = tweepy.Client(
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
)

def send_manual_tweet():
    """Send a manual text-only tweet."""
    try:
        manual_text = "Test tweet: This is a manually written tweet to ensure the bot is working correctly."
        print("Sending manual text-only tweet...")
        response = client_v2.create_tweet(text=manual_text)

        # Validate response and print tweet URL
        if response and "data" in response and "id" in response.data:
            tweet_id = response.data['id']
            tweet_url = f"https://twitter.com/user/status/{tweet_id}"
            print(f"Manual tweet posted successfully! URL: {tweet_url}")
            return tweet_url
        else:
            print("Failed to post manual tweet. Invalid response.")
            print(response)
    except tweepy.TweepyException as e:
        print(f"Error posting manual tweet: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
