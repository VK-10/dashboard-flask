import pandas as pd
import matplotlib.pyplot as plt
import os

# Define the directory where CSV files are stored
directory = "Financial Data"

# List of stock symbols
stock_symbols = [
    "AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "SPY", "NVDA", "META", "NFLX", "AMD",
]

# Initialize a dictionary to store the drawdown for each stock
drawdowns = {}

# Loop over each stock symbol to load data and plot the trading volume and drawdown
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
        
        # Calculate daily returns using the Adjusted Close price
        stock_data['Daily_Returns'] = stock_data['Adj_Close'].pct_change()
        
        # Calculate cumulative returns
        stock_data['Cumulative_Returns'] = (1 + stock_data['Daily_Returns']).cumprod()
        
        # Calculate drawdown
        stock_data['Drawdown'] = stock_data['Cumulative_Returns'] / stock_data['Cumulative_Returns'].cummax() - 1
        
        # Store the drawdown for each stock
        drawdowns[ticker] = stock_data['Drawdown']
        
        # Plot the trading volume
        plt.figure(figsize=(14, 7))
        plt.plot(stock_data.index, stock_data['Volume'], label=f'{ticker} Volume', color='tab:blue')
        
        # Customize the plot
        plt.title(f'{ticker} Trading Volume Over Time')
        plt.xlabel('Date')
        plt.ylabel('Volume')
        plt.legend(loc='upper left')
        plt.grid(True)
        
        # Display the plot for trading volume
        plt.show()

    else:
        print(f"Data for {ticker} not found in {directory}. Skipping.")

# Plot the drawdown for each stock
plt.figure(figsize=(14, 7))
for ticker in drawdowns:
    plt.plot(drawdowns[ticker].index, drawdowns[ticker], label=f'{ticker} Drawdown')

plt.title('Drawdown Over Time')
plt.xlabel('Date')
plt.ylabel('Drawdown')
plt.legend(loc='lower left')
plt.grid(True)
plt.show()
