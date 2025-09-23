import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns  # Import seaborn for heatmap
import os

# Define the directory where CSV files are stored
directory = "Financial Data"

# List of stock symbols
stock_symbols = [
    "AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "SPY", "NVDA", "META", "NFLX", "AMD",
]

# Dictionary to store adjusted close prices for each stock
data = {}

# Load data from CSV files
for symbol in stock_symbols:
    filepath = os.path.join(directory, f"{symbol}.csv")
    if os.path.exists(filepath):
        try:
            # Skip first two rows and use custom column names
            stock_data = pd.read_csv(filepath, skiprows=2, names=['Date', 'Adj_Close', 'Close', 'High', 'Low', 'Open', 'Volume'])
            
            # Print first few rows of raw data for debugging
            print(f"\nFirst few rows of {symbol} data:")
            print(stock_data.head())
            
            # Remove any rows where Date column contains 'Date' or other headers
            stock_data = stock_data[~stock_data['Date'].str.contains('Date', na=False)]
            
            # Convert the date strings to datetime, handling the specific format
            stock_data['Date'] = pd.to_datetime(stock_data['Date'].str.split('.').str[0], format='%Y-%m-%d %H:%M:%S')
            
            # Convert numeric columns to float
            numeric_columns = ['Adj_Close', 'Close', 'High', 'Low', 'Open', 'Volume']
            for col in numeric_columns:
                stock_data[col] = pd.to_numeric(stock_data[col], errors='coerce')
            
            stock_data.set_index('Date', inplace=True)
            
            # Use Adj_Close for calculations
            data[symbol] = stock_data['Adj_Close']
            
            print(f"\nSuccessfully processed {symbol}")
            
        except Exception as e:
            print(f"Error processing {symbol}: {str(e)}")
            if 'stock_data' in locals():
                print("Sample data causing error:")
                print(stock_data['Date'].head())
    else:
        print(f"Data for {symbol} not found in {directory}. Skipping.")

# Check if we have any data
if not data:
    print("No data was successfully loaded!")
else:
    # Combine all stock data into a single DataFrame
    adj_close = pd.DataFrame(data)
    
    # Calculate daily returns
    daily_returns = adj_close.pct_change().dropna()
    
    if not daily_returns.empty:
        # Plot daily returns
        plt.figure(figsize=(14, 7))
        for symbol in stock_symbols:
            if symbol in daily_returns.columns:
                plt.plot(daily_returns.index, daily_returns[symbol], label=symbol)
        
        plt.title('Daily Returns Over Time')
        plt.xlabel('Date')
        plt.ylabel('Daily Return')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True)
        plt.tight_layout()
        plt.show()
        
        # Print some basic statistics
        print("\nDaily Returns Statistics:")
        print("\nMean Daily Returns:")
        print(daily_returns.mean().round(4))
        print("\nDaily Returns Standard Deviation:")
        print(daily_returns.std().round(4))

        # Calculate and plot the correlation matrix
        corr = daily_returns.corr()
        
        plt.figure(figsize=(10, 7))
        sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
        plt.title('Correlation Matrix of Daily Returns')
        plt.show()

        # Calculate rolling mean and rolling standard deviation with a 30-day window
        window = 30  # 30-day window
        rolling_mean = adj_close.rolling(window=window).mean()
        rolling_std = adj_close.rolling(window=window).std()

        # Plot rolling mean
        plt.figure(figsize=(14, 7))
        for ticker in stock_symbols:
            if ticker in rolling_mean.columns:
                plt.plot(rolling_mean.index, rolling_mean[ticker], label=f'{ticker} Rolling Mean')
        
        plt.title(f'{window}-Day Rolling Mean of Adjusted Close Price')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        # Plot rolling standard deviation
        plt.figure(figsize=(14, 7))
        for ticker in stock_symbols:
            if ticker in rolling_std.columns:
                plt.plot(rolling_std.index, rolling_std[ticker], label=f'{ticker} Rolling Std Dev')

        plt.title(f'{window}-Day Rolling Standard Deviation of Adjusted Close Price')
        plt.xlabel('Date')
        plt.ylabel('Standard Deviation')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        # Plot the distribution of daily returns with KDE

        plt.figure(figsize=(14, 7))
        for ticker in stock_symbols:
            if ticker in daily_returns.columns:
                sns.histplot(daily_returns[ticker], kde=True, label=ticker, bins=50)

        plt.title('Distribution of Daily Returns')
        plt.xlabel('Daily Return')
        plt.ylabel('Frequency')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        cumulative_returns = (1 + daily_returns).cumprod()

        # Plot cumulative returns over time
        plt.figure(figsize=(14, 7))
        for ticker in stock_symbols:
            if ticker in cumulative_returns.columns:
                plt.plot(cumulative_returns.index, cumulative_returns[ticker], label=ticker)

        plt.title('Cumulative Returns Over Time')
        plt.xlabel('Date')
        plt.ylabel('Cumulative Return')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        window_sma = 50  # 50-day SMA
        window_ema = 50  # 50-day EMA

        # Plot SMA and EMA for each stock
        plt.figure(figsize=(14, 7))
        for ticker in stock_symbols:
            if ticker in adj_close.columns:
                # Plot the adjusted close price
                adj_close[ticker].plot(label=f'{ticker} Price', alpha=0.5)
                
                # Plot 50-day SMA
                adj_close[ticker].rolling(window=window_sma).mean().plot(label=f'{ticker} {window_sma}-Day SMA')
                
                # Plot 50-day EMA
                adj_close[ticker].ewm(span=window_ema, adjust=False).mean().plot(label=f'{ticker} {window_ema}-Day EMA')

        # Customize the plot
        plt.title('SMA and EMA')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        window_bb = 20  # 20-day SMA for Bollinger Bands

        # Plot Bollinger Bands for each stock
        plt.figure(figsize=(14, 7))
        for ticker in stock_symbols:
            if ticker in adj_close.columns:
                # Calculate 20-day SMA
                sma = adj_close[ticker].rolling(window=window_bb).mean()
                
                # Calculate the standard deviation for the same window
                std = adj_close[ticker].rolling(window=window_bb).std()
                
                # Calculate the upper and lower Bollinger Bands
                upper_band = sma + (std * 2)
                lower_band = sma - (std * 2)

                # Plot the adjusted close price, SMA, and Bollinger Bands
                plt.plot(adj_close[ticker], label=f'{ticker} Price', alpha=0.5)
                plt.plot(sma, label=f'{ticker} {window_bb}-Day SMA')
                plt.plot(upper_band, label=f'{ticker} Upper Bollinger Band')
                plt.plot(lower_band, label=f'{ticker} Lower Bollinger Band')

        # Customize the plot
        plt.title('Bollinger Bands')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        def calculate_rsi(data, window=14):
    # Calculate the daily price changes
            delta = data.diff(1)
            # Separate the gains (positive changes) and losses (negative changes)
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            # Calculate the rolling averages of gains and losses
            avg_gain = gain.rolling(window=window).mean()
            avg_loss = loss.rolling(window=window).mean()
            # Calculate the relative strength (RS)
            rs = avg_gain / avg_loss
            # Calculate the RSI
            rsi = 100 - (100 / (1 + rs))
            return rsi

    # Plot RSI for each stock
        plt.figure(figsize=(14, 7))
        for symbol in stock_symbols:
            if symbol in adj_close.columns:
                rsi = calculate_rsi(adj_close[symbol])
                plt.plot(rsi, label=f'{symbol} RSI')

        # Plot horizontal lines for overbought (70) and oversold (30) levels
        plt.axhline(70, color='red', linestyle='--', label='Overbought (70)')
        plt.axhline(30, color='green', linestyle='--', label='Oversold (30)')

        plt.title('RSI for Stocks')
        plt.xlabel('Date')
        plt.ylabel('RSI')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        short_window = 12
        long_window = 26
        signal_window = 9

        # Assuming 'adj_close' is a DataFrame containing adjusted close prices for each stock symbol
        plt.figure(figsize=(14, 7))
        for symbol in stock_symbols:  # Use stock_symbols directly as per your reference
            if symbol in adj_close.columns:
                # Calculate the short-term and long-term EMAs
                exp1 = adj_close[symbol].ewm(span=short_window, adjust=False).mean()
                exp2 = adj_close[symbol].ewm(span=long_window, adjust=False).mean()
                
                # Calculate MACD
                macd = exp1 - exp2
                
                # Calculate the Signal Line
                signal = macd.ewm(span=signal_window, adjust=False).mean()
                
                # Plot MACD and Signal Line
                plt.plot(macd, label=f'{symbol} MACD')
                plt.plot(signal, label=f'{symbol} Signal Line')

        # Customize the plot
        plt.title('MACD (Moving Average Convergence Divergence)')
        plt.xlabel('Date')
        plt.ylabel('MACD')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.tight_layout()

        # Display the plot
        plt.show()




    else:
        print("No valid daily returns data to plot.")
