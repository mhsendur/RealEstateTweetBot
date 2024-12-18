import modeling
import webscrape_emlakjet
import send_tweet
from datetime import datetime, timedelta
import time
import os

# Define Istanbul time-based tweet schedule (GMT+3)
TWEET_TIMES = ["06:30", "09:33", "13:25", "17:30", "19:30"]

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

def run_daily_workflow(skip_initial_scrape=False):
    """Run scraping and modeling workflow at 2 AM."""
    now = datetime.now()
    target_time = datetime(now.year, now.month, now.day, 2, 0)  # 2:00 AM today

    # If already past 2 AM, schedule for the next day
    if now > target_time:
        target_time += timedelta(days=1)

    if skip_initial_scrape:
        print("Skipping initial web scraping and modeling.")
        return  # Exit early if skipping scraping/modeling

    # Calculate wait time
    time_to_wait = (target_time - now).total_seconds()
    print(f"Waiting until 2:00 AM to start scraping and modeling...")
    time.sleep(time_to_wait)

    # Run scraping and modeling
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
    first_run = True  # Track if this is the first run
    while True:
        now = datetime.now()
        last_run = get_last_run_time()

        # Check if scraping and modeling were done today or skip on the first run
        if first_run:
            run_daily_workflow(skip_initial_scrape=True)
            first_run = False  # Ensure skip only happens once
        elif (now - last_run) >= timedelta(hours=24):
            run_daily_workflow()

        # Start posting tweets throughout the day
        post_scheduled_tweets()

if __name__ == "__main__":
    main()
