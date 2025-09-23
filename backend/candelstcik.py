import pandas as pd
import mplfinance as mpf
import os

# Define the directory where CSV files are stored
directory = "Financial Data"

# List of stock symbols
stock_symbols = [
    "AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "SPY", "NVDA", "META", "NFLX", "AMD",
]

# Loop over each stock symbol to load data and plot the candlestick chart
for ticker in stock_symbols:
    # Define the file path for each stock symbol CSV file
    filepath = os.path.join(directory, f"{ticker}.csv")
    
    if os.path.exists(filepath):
        # Load the CSV file into a DataFrame
        stock_data = pd.read_csv(filepath, skiprows=2, names=['Date', 'Adj_Close', 'Close', 'High', 'Low', 'Open', 'Volume'])
        
        # Remove rows where 'Date' column contains 'Date' or any other non-date values
        stock_data = stock_data[~stock_data['Date'].str.contains('Date', na=False)]
        
        # Convert the 'Date' column to datetime
        stock_data['Date'] = pd.to_datetime(stock_data['Date'].str.split('.').str[0], format='%Y-%m-%d %H:%M:%S')
        
        # Set the 'Date' column as the index
        stock_data.set_index('Date', inplace=True)
        
        # Extract OHLC data for the candlestick chart
        ohlc_data = stock_data[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        # Plot candlestick chart using mplfinance
        mpf.plot(
            ohlc_data,
            type='candle',
            style='charles',
            title=f'{ticker} Candlestick Chart',
            ylabel='Price',
            volume=True,
            figratio=(12, 8),  # Optional: Adjust the figure ratio for better viewing
            figscale=1.2        # Optional: Adjust the figure scale
        )
    else:
        print(f"Data for {ticker} not found in {directory}. Skipping.")
