import modeling
import webscrape_emlakjet
import send_tweet
from datetime import datetime, timedelta
import random
import time
import os

# File to track scrape and post history
SCRAPE_LAST_RUN_FILE = "/home/istanbulrealestatebot/RealEstateTweetBot/src/scrape_last_run.txt"

def generate_random_tweet_schedule():
    """
    Generate a randomized tweet schedule with 3–4 tweets per day.
    Ensure at least 3 hours and some randomness in intervals.
    """
    start_time = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)  # Start at 6:00 AM
    tweet_times = []

    for _ in range(random.randint(3, 4)):  # 3 to 4 tweets per day
        offset_minutes = random.randint(190, 240)  # Between 3h 10m to 4h
        start_time += timedelta(minutes=offset_minutes)
        tweet_times.append(start_time.strftime("%H:%M"))

    print(f"Today's tweet schedule: {tweet_times}")
    return tweet_times


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

    if now > target_time:
        target_time += timedelta(days=1)

    if skip_initial_scrape:
        print("Skipping initial web scraping and modeling.")
        return

    time_to_wait = (target_time - now).total_seconds()
    print(f"Waiting until 2:00 AM to start scraping and modeling...")
    time.sleep(time_to_wait)

    print("Starting daily scraping and modeling workflow...")
    webscrape_emlakjet.run_scraper()
    modeling.run_modeling()
    update_last_run_time()
    print("Scraping and modeling completed for the day.")

def post_scheduled_tweets():
    """Post tweets at scheduled times every day."""
    today_schedule = generate_random_tweet_schedule()  # Generate a new schedule each day
    today = datetime.now().strftime("%Y-%m-%d")

    for tweet_time in today_schedule:
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

        # Pause briefly after posting to avoid triggering spam filters
        pause_time = random.randint(30, 60)  # 30 to 60 seconds
        print(f"Pausing for {pause_time} seconds before next action.")
        time.sleep(pause_time)

    # Sleep until the next day to repeat tweet scheduling
    print("All tweets for today have been posted. Sleeping until tomorrow...")
    time.sleep(300)  # Sleep for 5 minutes before checking for the next day's schedule

def post_test_tweet():
    """Post a test tweet after the bot starts."""
    print("Posting a test tweet to verify functionality...")
    try:
        send_tweet.send_tweet()
        print("Test tweet posted successfully.")
    except Exception as e:
        print(f"Failed to post test tweet: {e}")

def main():
    """Main function to manage daily scraping and tweet posting."""
    print("Starting the bot...")

    # Post an initial test tweet to ensure everything works
    post_test_tweet()

    first_run = True
    while True:
        now = datetime.now()
        last_run = get_last_run_time()

        if first_run:
            run_daily_workflow(skip_initial_scrape=True)
            first_run = False
        elif (now - last_run) >= timedelta(hours=24):
            run_daily_workflow()

        post_scheduled_tweets()

if __name__ == "__main__":
    main()
