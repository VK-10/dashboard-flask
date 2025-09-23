from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import mplfinance as mpf
import io
import os

app = Flask(__name__)
CORS(app)

# Load data into a global dictionary (simulate loaded stock data)
stock_symbols = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "SPY", "NVDA", "META", "NFLX", "AMD"]
directory = "Financial Data"
data = {}

# Load CSV data at startup
for symbol in stock_symbols:
    filepath = os.path.join(directory, f"{symbol}.csv")
    try:
        stock_data = pd.read_csv(filepath, skiprows=2, names=['Date', 'Adj_Close', 'Close', 'High', 'Low', 'Open', 'Volume'])
        stock_data = stock_data[~stock_data['Date'].str.contains('Date', na=False)]
        stock_data['Date'] = pd.to_datetime(stock_data['Date'].str.split('.').str[0], format='%Y-%m-%d %H:%M:%S')
        stock_data.set_index('Date', inplace=True)
        stock_data['Adj_Close'] = pd.to_numeric(stock_data['Adj_Close'], errors='coerce')
        data[symbol] = stock_data
    except Exception as e:
        print(f"Failed to load {symbol}: {e}")

# [Previous utility functions remain the same]
def calculate_daily_returns(adj_close):
    return adj_close.pct_change().dropna()

def calculate_rsi(series, window=14):
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(series, window=20):
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper_band = sma + (2 * std)
    lower_band = sma - (2 * std)
    return sma, upper_band, lower_band

def calculate_macd(series, short_window=12, long_window=26, signal_window=9):
    short_ema = series.ewm(span=short_window, adjust=False).mean()
    long_ema = series.ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    return macd, signal

@app.route('/stock/graph', methods=['GET'])
def stock_graph():
    symbols = request.args.get('symbols', '').split(',')
    graph_type = request.args.get('graph_type', 'daily_returns')

    if not symbols or not graph_type:
        return jsonify({"error": "Please provide 'symbols' and 'graph_type' parameters."}), 400

    # Validate symbols
    valid_symbols = [symbol for symbol in symbols if symbol in data]
    if not valid_symbols:
        return jsonify({"error": "No valid stock symbols provided."}), 400

    if graph_type == 'candlestick':
        if len(valid_symbols) > 1:
            return jsonify({"error": "Candlestick chart can only be generated for a single symbol."}), 400

        symbol = valid_symbols[0]
        stock_data = data[symbol]
        
        # Prepare OHLC data
        ohlc_data = stock_data[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        # Convert numeric columns
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            ohlc_data[col] = pd.to_numeric(ohlc_data[col], errors='coerce')
        
        # Create a bytes buffer for the plot
        buf = io.BytesIO()
        
        # Create and save the candlestick chart
        mpf.plot(
            ohlc_data,
            type='candle',
            style='charles',
            title=f'{symbol} Candlestick Chart',
            ylabel='Price',
            volume=True,
            figratio=(12, 8),
            figscale=1.2,
            savefig=dict(fname=buf, format='png', dpi=300, bbox_inches='tight')
        )
        
        buf.seek(0)
        return send_file(buf, mimetype='image/png')

    # Combine the data for the requested symbols (for non-candlestick charts)
    adj_close = pd.DataFrame({symbol: data[symbol]['Adj_Close'] for symbol in valid_symbols})

    plt.figure(figsize=(12, 8))

    if graph_type == 'daily_returns':
        returns = adj_close.pct_change().dropna()
        sns.lineplot(data=returns, dashes=False)
        plt.title('Daily Returns for Selected Symbols')
        plt.xlabel('Date')
        plt.ylabel('Daily Return')

    elif graph_type == 'rolling_mean':
        sma = adj_close.rolling(window=20).mean()
        sns.lineplot(data=sma, dashes=False)
        plt.title('Rolling Mean (20-day) for Selected Symbols')
        plt.xlabel('Date')
        plt.ylabel('Rolling Mean')

    elif graph_type == 'bollinger_bands':
        for symbol in valid_symbols:
            series = adj_close[symbol]
            sma, upper, lower = calculate_bollinger_bands(series)
            plt.plot(series, label=f"{symbol} Price")
            plt.plot(sma, label=f"{symbol} SMA")
            plt.fill_between(series.index, upper, lower, alpha=0.2)
        plt.title("Bollinger Bands")
        plt.legend()

    elif graph_type == 'rsi':
        for symbol in valid_symbols:
            rsi = calculate_rsi(adj_close[symbol])
            plt.plot(rsi, label=symbol)
        plt.axhline(y=70, color='r', linestyle='--')
        plt.axhline(y=30, color='r', linestyle='--')
        plt.title("Relative Strength Index (RSI)")
        plt.legend()

    elif graph_type == 'macd':
        for symbol in valid_symbols:
            macd, signal = calculate_macd(adj_close[symbol])
            plt.plot(macd, label=f"{symbol} MACD")
            plt.plot(signal, label=f"{symbol} Signal")
        plt.title("MACD (Moving Average Convergence Divergence)")
        plt.legend()

    else:
        return jsonify({"error": "Invalid graph type"}), 400

    # Save plot to a bytes buffer (for non-candlestick charts)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    buf.seek(0)
    plt.close()

    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)