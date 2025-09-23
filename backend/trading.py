from flask import Flask, jsonify, request, send_file
import pandas as pd
import matplotlib.pyplot as plt
import os
import io
import matplotlib
from flask_cors import CORS

matplotlib.use('Agg')
app = Flask(__name__)

CORS(app)

# Define the directory where CSV files are stored
directory = "Financial Data"

# List of stock symbols
stock_symbols = [
    "AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "SPY", "NVDA", "META", "NFLX", "AMD",
]

# Helper function to load and process data
def load_stock_data(filepath):
    try:
        stock_data = pd.read_csv(filepath, skiprows=2, names=['Date', 'Adj_Close', 'Close', 'High', 'Low', 'Open', 'Volume'])
        stock_data = stock_data[~stock_data['Date'].str.contains('Date', na=False)]
        stock_data['Date'] = pd.to_datetime(stock_data['Date'].str.split('.').str[0], format='%Y-%m-%d %H:%M:%S')
        stock_data.set_index('Date', inplace=True)
        return stock_data
    except Exception as e:
        raise ValueError(f"Error loading data: {str(e)}")

@app.route('/api/stocks/<ticker>/volume', methods=['GET'])
def get_trading_volume(ticker):
    """
    Generate and return the trading volume plot for a given stock ticker.
    """
    filepath = os.path.join(directory, f"{ticker}.csv")
    if not os.path.exists(filepath):
        return jsonify({"error": f"Data for {ticker} not found."}), 404

    try:
        stock_data = load_stock_data(filepath)

        # Create the plot for trading volume
        plt.figure(figsize=(14, 7))
        plt.plot(stock_data.index, stock_data['Volume'], label=f'{ticker} Volume', color='tab:blue')
        plt.title(f'{ticker} Trading Volume Over Time')
        plt.xlabel('Date')
        plt.ylabel('Volume')
        plt.legend(loc='upper left')
        plt.grid(True)

        # Save the plot to a BytesIO object
        img = io.BytesIO()
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        return send_file(img, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stocks/drawdown', methods=['GET'])
def get_drawdown_plot():
    """
    Generate and return the drawdown plot for all stocks.
    """
    drawdowns = {}
    for ticker in stock_symbols:
        filepath = os.path.join(directory, f"{ticker}.csv")
        if os.path.exists(filepath):
            try:
                stock_data = load_stock_data(filepath)
                # Calculate daily and cumulative returns
                stock_data['Daily_Returns'] = stock_data['Adj_Close'].pct_change()
                stock_data['Cumulative_Returns'] = (1 + stock_data['Daily_Returns']).cumprod()
                # Calculate drawdown
                stock_data['Drawdown'] = stock_data['Cumulative_Returns'] / stock_data['Cumulative_Returns'].cummax() - 1
                drawdowns[ticker] = stock_data['Drawdown']
            except Exception as e:
                print(f"Error processing {ticker}: {str(e)}")
                continue

    # Create the plot for drawdowns
    plt.figure(figsize=(14, 7))
    for ticker, drawdown in drawdowns.items():
        plt.plot(drawdown.index, drawdown, label=f'{ticker} Drawdown')

    plt.title('Drawdown Over Time')
    plt.xlabel('Date')
    plt.ylabel('Drawdown')
    plt.legend(loc='lower left')
    plt.grid(True)

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    return send_file(img, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True,port=5003)
