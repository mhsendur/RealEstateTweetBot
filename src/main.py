import modeling
import webscrape_emlakjet
import send_tweet
from datetime import datetime, timedelta
import random
import time
import os

# File to track scrape and post history
SCRAPE_LAST_RUN_FILE = "scrape_last_run.txt"

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

def generate_random_post_times():
    """Generate 5 random post times for the day with at least 3 hours gap."""
    base_times = [6, 9, 12, 15, 18]  # Base hours (around 6:30, 9:30, etc.)
    random_offsets = [random.randint(-15, 15) for _ in range(5)]  # Random minutes offset
    post_times = []

    for i, hour in enumerate(base_times):
        post_time = datetime.now().replace(hour=hour, minute=30, second=0, microsecond=0) + timedelta(minutes=random_offsets[i])
        post_times.append(post_time)

    # Ensure 3-hour gaps between posts
    for i in range(1, len(post_times)):
        if (post_times[i] - post_times[i - 1]).total_seconds() < 3 * 3600:
            post_times[i] = post_times[i - 1] + timedelta(hours=3)

    return post_times

def run_daily_workflow():
    """Run scraping and modeling workflow at 2 AM."""
    now = datetime.now()
    target_time = datetime(now.year, now.month, now.day, 2, 0)  # 2:00 AM today

    if now > target_time:
        target_time += timedelta(days=1)

    # Calculate wait time
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
    while True:
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



def main():
    """Main function to manage daily scraping and tweet posting."""
    print("Starting the bot...")

    # Perform initial scraping and modeling immediately
    run_daily_workflow()

    while True:
        now = datetime.now()
        last_run = get_last_run_time()

        # Run daily workflow if it's been more than 24 hours since the last run
        if (now - last_run) >= timedelta(hours=24):
            run_daily_workflow()

        post_scheduled_tweets()

if __name__ == "__main__":
    main()
