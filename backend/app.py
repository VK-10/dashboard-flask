from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import mplfinance as mpf
import io
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

app = Flask(__name__)
CORS(app)

# Load data into a global dictionary (simulate loaded stock data)
stock_symbols = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "SPY", "NVDA", "META", "NFLX", "AMD"]
directory = "Financial Data"
data = {}

# Load CSV data at startup
print("Loading stock data...")
for symbol in stock_symbols:
    filepath = os.path.join(directory, f"{symbol}.csv")
    try:
        stock_data = pd.read_csv(filepath, skiprows=2, names=['Date', 'Adj_Close', 'Close', 'High', 'Low', 'Open', 'Volume'])
        stock_data = stock_data[~stock_data['Date'].str.contains('Date', na=False)]
        stock_data['Date'] = pd.to_datetime(stock_data['Date'].str.split('.').str[0], format='%Y-%m-%d %H:%M:%S')
        stock_data.set_index('Date', inplace=True)
        
        # Convert all numeric columns
        numeric_cols = ['Adj_Close', 'Close', 'High', 'Low', 'Open', 'Volume']
        for col in numeric_cols:
            stock_data[col] = pd.to_numeric(stock_data[col], errors='coerce')
        
        data[symbol] = stock_data
        print(f"Successfully loaded {symbol}")
    except Exception as e:
        print(f"Failed to load {symbol}: {e}")

print(f"Loaded data for {len(data)} symbols")

# Utility Functions
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

@app.route('/stock/sma-ema', methods=['GET'])
def stock_sma_ema():
    symbol = request.args.get('symbol')
    sma_window = request.args.get('sma_window', 20, type=int)  
    ema_window = request.args.get('ema_window', 20, type=int)  

    print(f"SMA-EMA request: symbol={symbol}, sma_window={sma_window}, ema_window={ema_window}")

    if not symbol:
        return jsonify({"error": "Please provide a 'symbol' parameter."}), 400

    if symbol not in data:
        return jsonify({"error": f"Symbol {symbol} not found. Available symbols: {list(data.keys())}"}), 404

    stock_data = data[symbol].copy()

    # Ensure 'Adj_Close' is available and contains valid data
    if 'Adj_Close' not in stock_data.columns or stock_data['Adj_Close'].isnull().all():
        return jsonify({"error": f"Adjusted Close data not available for {symbol}."}), 400

    # Calculate SMA and EMA
    stock_data['SMA'] = stock_data['Adj_Close'].rolling(window=sma_window).mean()
    stock_data['EMA'] = stock_data['Adj_Close'].ewm(span=ema_window, adjust=False).mean()

    # If the rolling window is too large for the available data, make sure we handle it gracefully
    if stock_data['SMA'].isnull().all() or stock_data['EMA'].isnull().all():
        return jsonify({"error": f"Insufficient data for the specified window sizes."}), 400

    try:
        # Plot Adjusted Close, SMA, and EMA
        plt.figure(figsize=(14, 7))
        plt.plot(stock_data.index, stock_data['Adj_Close'], label='Adjusted Close', alpha=0.7, color='blue')
        plt.plot(stock_data.index, stock_data['SMA'], label=f'{sma_window}-Day SMA', alpha=0.7, color='orange')
        plt.plot(stock_data.index, stock_data['EMA'], label=f'{ema_window}-Day EMA', alpha=0.7, color='green')

        plt.title(f'{symbol} SMA and EMA')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend(loc='upper left')
        plt.grid(True)

        # Save plot to a BytesIO buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plt.close()

        # Return the image
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        plt.close()  # Make sure to close the plot in case of error
        return jsonify({"error": f"Error generating plot: {str(e)}"}), 500

@app.route('/stock/graph', methods=['GET'])
def stock_graph():
    symbols_param = request.args.get('symbols', '')
    graph_type = request.args.get('graph_type', 'daily_returns')
    
    print(f"Graph request: symbols={symbols_param}, graph_type={graph_type}")
    
    # Split symbols and clean up
    symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
    
    # Fixed validation logic
    if not symbols or not symbols_param.strip():
        return jsonify({"error": "Please provide 'symbols' parameter. Example: AAPL,MSFT"}), 400
    
    if not graph_type:
        return jsonify({"error": "Please provide 'graph_type' parameter."}), 400

    # Validate symbols
    valid_symbols = [symbol for symbol in symbols if symbol in data and not data[symbol].empty]
    invalid_symbols = [symbol for symbol in symbols if symbol not in data]
    
    if invalid_symbols:
        print(f"Invalid symbols: {invalid_symbols}")
        print(f"Available symbols: {list(data.keys())}")
    
    if not valid_symbols:
        return jsonify({
            "error": f"No valid stock symbols provided. Invalid: {invalid_symbols}. Available: {list(data.keys())}"
        }), 400

    print(f"Processing {len(valid_symbols)} valid symbols: {valid_symbols}")

    try:
        # Handle candlestick chart separately
        if graph_type == 'candlestick':
            if len(valid_symbols) > 1:
                return jsonify({"error": "Candlestick chart can only be generated for a single symbol."}), 400

            symbol = valid_symbols[0]
            stock_data = data[symbol]
            
            # Prepare OHLC data
            ohlc_data = stock_data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            
            # Remove any NaN values
            ohlc_data = ohlc_data.dropna()
            
            if ohlc_data.empty:
                return jsonify({"error": f"No valid OHLC data for {symbol}"}), 400
            
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

        # For other chart types, combine adjusted close data
        adj_close_data = {}
        for symbol in valid_symbols:
            if 'Adj_Close' in data[symbol].columns:
                adj_close_data[symbol] = data[symbol]['Adj_Close']
        
        if not adj_close_data:
            return jsonify({"error": "No Adjusted Close data available for the specified symbols"}), 400
        
        adj_close = pd.DataFrame(adj_close_data)

        plt.figure(figsize=(12, 8))

        if graph_type == 'daily_returns':
            returns = adj_close.pct_change().dropna()
            if returns.empty:
                return jsonify({"error": "No valid return data to plot"}), 400
            
            for col in returns.columns:
                plt.plot(returns.index, returns[col], label=col, alpha=0.7)
            plt.title('Daily Returns for Selected Symbols')
            plt.xlabel('Date')
            plt.ylabel('Daily Return')
            plt.legend()
            plt.grid(True)

        elif graph_type == 'rolling_mean':
            sma = adj_close.rolling(window=20).mean()
            for col in sma.columns:
                plt.plot(sma.index, sma[col], label=f'{col} 20-day SMA', alpha=0.7)
            plt.title('Rolling Mean (20-day) for Selected Symbols')
            plt.xlabel('Date')
            plt.ylabel('Rolling Mean')
            plt.legend()
            plt.grid(True)

        elif graph_type == 'bollinger_bands':
            for symbol in valid_symbols:
                if symbol in adj_close.columns:
                    series = adj_close[symbol].dropna()
                    sma, upper, lower = calculate_bollinger_bands(series)
                    plt.plot(series.index, series, label=f"{symbol} Price", alpha=0.7)
                    plt.plot(sma.index, sma, label=f"{symbol} SMA", alpha=0.7)
                    plt.fill_between(series.index, upper, lower, alpha=0.2)
            plt.title("Bollinger Bands")
            plt.xlabel('Date')
            plt.ylabel('Price')
            plt.legend()
            plt.grid(True)

        elif graph_type == 'rsi':
            for symbol in valid_symbols:
                if symbol in adj_close.columns:
                    rsi = calculate_rsi(adj_close[symbol])
                    plt.plot(rsi.index, rsi, label=symbol, alpha=0.7)
            plt.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='Overbought (70)')
            plt.axhline(y=30, color='r', linestyle='--', alpha=0.7, label='Oversold (30)')
            plt.title("Relative Strength Index (RSI)")
            plt.xlabel('Date')
            plt.ylabel('RSI')
            plt.legend()
            plt.grid(True)

        elif graph_type == 'macd':
            for symbol in valid_symbols:
                if symbol in adj_close.columns:
                    macd, signal = calculate_macd(adj_close[symbol])
                    plt.plot(macd.index, macd, label=f"{symbol} MACD", alpha=0.7)
                    plt.plot(signal.index, signal, label=f"{symbol} Signal", alpha=0.7)
            plt.title("MACD (Moving Average Convergence Divergence)")
            plt.xlabel('Date')
            plt.ylabel('MACD')
            plt.legend()
            plt.grid(True)

        else:
            plt.close()
            return jsonify({"error": f"Invalid graph type: {graph_type}. Available types: daily_returns, rolling_mean, bollinger_bands, rsi, macd, candlestick"}), 400

        # Save plot to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=300, bbox_inches='tight')
        buf.seek(0)
        plt.close()

        return send_file(buf, mimetype='image/png')
    
    except Exception as e:
        plt.close()  # Make sure to close any open plots
        print(f"Error generating graph: {str(e)}")
        return jsonify({"error": f"Error generating graph: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "loaded_symbols": list(data.keys()),
        "total_symbols": len(data)
    })

@app.route('/symbols', methods=['GET'])
def get_available_symbols():
    return jsonify({
        "available_symbols": list(data.keys()),
        "total_count": len(data)
    })

if __name__ == '__main__':
    print("Starting Flask server...")
    print(f"Available symbols: {list(data.keys())}")
    app.run(debug=True, host='127.0.0.1', port=5000)