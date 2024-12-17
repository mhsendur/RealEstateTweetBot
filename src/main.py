import modeling
import webscrape_emlakjet
import send_tweet
from datetime import datetime, timedelta
import time
import os

# Define Istanbul time-based tweet schedule (GMT+3)
TWEET_TIMES = ["06:30", "09:30", "12:30", "15:15", "15:20"]

SCRAPE_LAST_RUN_FILE = "scrape_last_run.txt"

def get_last_run_time():
    """Check when the scraper was last run."""
    if os.path.exists(SCRAPE_LAST_RUN_FILE):
        with open(SCRAPE_LAST_RUN_FILE, "r") as file:
            last_run_str = file.read().strip()
            return datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S")
    return datetime.min

def run_daily_workflow():
    """Run scraping and modeling if scraping hasn't been run today."""
    last_run_time = get_last_run_time()
    now = datetime.now()
    
    if now - last_run_time > timedelta(hours=24):
        print("Starting daily scraping and modeling workflow...")
        webscrape_emlakjet.run_scraper()
        modeling.run_modeling()
        print("Scraping and modeling completed for the day.")
    else:
        print("Scraping already completed today. Skipping modeling as well.")

def post_scheduled_tweets():
    """Post tweets at scheduled times."""
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

    # Post tweets at scheduled times
    post_scheduled_tweets()

if __name__ == "__main__":
    main()
