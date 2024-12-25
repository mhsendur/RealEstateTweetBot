import modeling
import webscrape_emlakjet
import send_tweet
from datetime import datetime, timedelta
import random
import time
import os

# File to track scrape and post history
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
    """Post tweets based on the random schedule."""
    post_times = generate_random_post_times()
    print(f"Today's tweet schedule: {[time.strftime('%H:%M') for time in post_times]}")

    for i, target_time in enumerate(post_times):
        now = datetime.now()
        if now > target_time:
            continue  # Skip past post times

        # Wait until the next post time
        time_to_wait = (target_time - now).total_seconds()
        print(f"Waiting for {time_to_wait / 60:.2f} minutes to send the next tweet.")
        time.sleep(time_to_wait)

        # Send the tweet with varying numbers of images
        num_images = 4 if i % 4 == 0 else random.choice([1, 2, 3])  # 1st and 4th post: 4 images, others random
        print(f"Posting tweet with {num_images} image(s)...")
        send_tweet.send_tweet(max_images=num_images)
        print(f"Tweet posted at {target_time.strftime('%H:%M')}!")

    print("All tweets for today have been posted.")

def main():
    """Main function to manage daily scraping and tweet posting."""
    print("Starting the bot...")
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
