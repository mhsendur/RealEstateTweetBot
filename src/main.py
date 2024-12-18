import modeling
import webscrape_emlakjet
import send_tweet
from datetime import datetime, timedelta
import time
import os

# Define Istanbul time-based tweet schedule (GMT+3) - Alttakiler GMT saati, bizim icin +3 olarak dusun
TWEET_TIMES = ["06:30", "09:08", "12:30", "17:11", "20:25"]

SCRAPE_LAST_RUN_FILE = "scrape_last_run.txt"

def get_last_run_time():
    """Check when the scraper was last run."""
    if os.path.exists(SCRAPE_LAST_RUN_FILE):
        with open(SCRAPE_LAST_RUN_FILE, "r") as file:
            last_run_str = file.read().strip()
            return datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S")
    return datetime.min

def update_last_run_time():
    """Update the last run time."""
    with open(SCRAPE_LAST_RUN_FILE, "w") as file:
        file.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
def run_daily_workflow():
    """Run scraping and modeling workflow if 24 hours have passed since the last run."""
    now = datetime.now()
    last_run = get_last_run_time()

    # Check if 24 hours have passed since the last run
    if (now - last_run) < timedelta(hours=24):
        print(f"Skipping scraping and modeling. Last run was at {last_run}.")
        return

    print("Starting daily scraping and modeling workflow...")
    webscrape_emlakjet.run_scraper()
    modeling.run_modeling()
    update_last_run_time()
    print("Scraping and modeling completed for the day.")


def post_scheduled_tweets():
    """Post tweets at scheduled times every day."""
    while True:
        today = datetime.now().strftime("%Y-%m-%d")
        for tweet_time in TWEET_TIMES:
            # Parse the next tweet time
            target_time = datetime.strptime(f"{today} {tweet_time}", "%Y-%m-%d %H:%M")
            now = datetime.now()
            if now > target_time:
                continue  # Skip past tweet times
            
            # Wait until the next scheduled time
            time_to_wait = (target_time - now).total_seconds()
            print(f"Waiting for {time_to_wait / 60:.2f} minutes to send the next tweet.")
            time.sleep(time_to_wait)

            # Send the tweet
            print(f"Posting tweet at {tweet_time}...")
            send_tweet.send_tweet()
            print(f"Tweet posted at {tweet_time}!")

        # Sleep until the next day to repeat tweet scheduling
        print("All tweets for today have been posted. Sleeping until tomorrow...")
        time.sleep(60)  # Short sleep to avoid a busy loop

def main():
    # Run scraping and modeling once per day at 2 AM
    print("Starting the bot...")
    while True:
        now = datetime.now()
        last_run = get_last_run_time()

        # Check if scraping and modeling were done today
        if last_run.date() < now.date():  # Only run if it's a new day
            run_daily_workflow()
        
        # Start posting tweets throughout the day
        post_scheduled_tweets()

if __name__ == "__main__":
    main()
