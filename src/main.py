import modeling
import webscrape_emlakjet
import send_tweet
import time

def main():
    while (True):
        webscrape_emlakjet.run_scraper()
        modeling.run_modeling()

        for i in range(12):
            send_tweet.send_tweet()
            print("SENT", i)
            time.sleep(7200)
            
if __name__ == "__main__":
    main()