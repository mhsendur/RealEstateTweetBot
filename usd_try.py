import yfinance as yf
import pandas as pd

def get_usd_try_rate_history():
    # Use the ticker for USD/TRY on Yahoo Finance
    ticker = yf.Ticker("TRY=X")
    
    # Get historical price data for the past 12 months
    history = ticker.history(period="1y")
    
    # Select only the 'Close' prices and reset the index
    history = history[['Close']].reset_index()
    
    # Rename the columns for better readability
    history.columns = ['Date', 'USD/TRY']
    
    return history

def save_to_csv(data, filename='usd_try_rates.csv'):
    # Save the DataFrame to a CSV file
    data.to_csv(filename, index=False)

def update_usd_data():

    # Get USD/TRY rate history
    usd_try_data = get_usd_try_rate_history()

    # Save the data to a CSV file
    save_to_csv(usd_try_data)

    print("USD/TRY rate history for the past 12 months has been saved to 'usd_try_rates.csv'.")

#update_usd_data()
