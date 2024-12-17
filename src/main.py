import modeling
import webscrape_emlakjet
import send_tweet
from datetime import datetime, timedelta
import time

# Define Istanbul time-based tweet schedule (GMT+3)
TWEET_TIMES = ["06:30", "09:30", "12:30", "13:50", "14:00"]

def run_daily_workflow():
    print("Starting daily scraping and modeling workflow...")
    webscrape_emlakjet.run_scraper()
    modeling.run_modeling()
    print("Scraping and modeling completed for the day.")

def post_scheduled_tweets():
    today = datetime.now().strftime("%Y-%m-%d")
    for tweet_time in TWEET_TIMES:
        # Parse the next tweet time
        target_time = datetime.strptime(f"{today} {tweet_time}", "%Y-%m-%d %H:%M")
        now = datetime.now()
        if now > target_time:
            print(f"Skipping tweet time {tweet_time} as it has already passed.")
            continue

        # Wait until the scheduled time
        time_to_wait = (target_time - now).total_seconds()
        print(f"Waiting for {time_to_wait / 60:.2f} minutes to send the next tweet.")
        time.sleep(time_to_wait)

        # Send the tweet
        send_tweet.send_tweet()
        print(f"Tweet posted at {tweet_time}!")

def main():
    # Run the daily workflow at the start
    run_daily_workflow()

    # Post 5 tweets at scheduled times
    post_scheduled_tweets()

if __name__ == "__main__":
    main()
