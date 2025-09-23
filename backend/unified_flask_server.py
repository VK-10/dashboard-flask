from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import mplfinance as mpf
import io
import os

# Use non-interactive backend
matplotlib.use('Agg')

app = Flask(__name__)
CORS(app)

print("Starting unified Flask server with correct CSV format handling...")

# Load data from CSV files
stock_symbols = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "SPY", "NVDA", "META", "NFLX", "AMD"]
directory = "Financial Data"
data = {}

def load_stock_data():
    """Load all CSV files into memory with correct format handling"""
    print("Loading stock data from CSV files...")
    
    if not os.path.exists(directory):
        print(f"❌ Directory '{directory}' not found!")
        return
    
    for symbol in stock_symbols:
        filepath = os.path.join(directory, f"{symbol}.csv")
        if os.path.exists(filepath):
            try:
                print(f"🔄 Processing {symbol}...")
                
                # Read the CSV file with the correct structure
                # Skip first 3 rows to get past headers and ticker info
                stock_data = pd.read_csv(
                    filepath, 
                    skiprows=3,  # Skip: Price headers, Ticker row, Date header
                    names=['Date', 'Adj_Close', 'Close', 'High', 'Low', 'Open', 'Volume']
                )
                
                print(f"  📄 Raw data shape: {stock_data.shape}")
                print(f"  📅 First few dates: {stock_data['Date'].head(3).tolist()}")
                
                # Remove any remaining header-like rows that might have slipped through
                initial_rows = len(stock_data)
                stock_data = stock_data[~stock_data['Date'].str.contains('Date', na=False, case=False)]
                stock_data = stock_data[~stock_data['Date'].str.contains('Ticker', na=False, case=False)]
                stock_data = stock_data[~stock_data['Date'].str.contains('Price', na=False, case=False)]
                
                print(f"  🧹 After header cleaning: {len(stock_data)}/{initial_rows} rows")
                
                if stock_data.empty:
                    print(f"  ❌ No data rows found for {symbol}")
                    continue
                
                # Parse dates - your format is: "2020-01-02 00:00:00+00:00"
                # This is already in ISO8601 format, so pandas should handle it well
                try:
                    stock_data['Date'] = pd.to_datetime(stock_data['Date'], format='ISO8601', errors='coerce')
                    print(f"  ✅ Date parsing successful with ISO8601")
                except Exception as e:
                    print(f"  ⚠️  ISO8601 failed, trying alternative method: {e}")
                    try:
                        # Remove timezone info and parse
                        cleaned_dates = stock_data['Date'].str.replace(r'\+\d{2}:\d{2}$', '', regex=True)
                        stock_data['Date'] = pd.to_datetime(cleaned_dates, errors='coerce')
                        print(f"  ✅ Date parsing successful with timezone removal")
                    except Exception as e2:
                        print(f"  ❌ All date parsing failed: {e2}")
                        continue
                
                # Check date parsing success
                valid_dates = stock_data['Date'].notna()
                print(f"  📅 Valid dates: {valid_dates.sum()}/{len(stock_data)}")
                
                if valid_dates.sum() == 0:
                    print(f"  ❌ No valid dates found for {symbol}")
                    continue
                
                # Filter to valid dates only
                stock_data = stock_data[valid_dates]
                
                # Set date as index
                stock_data.set_index('Date', inplace=True)
                
                # Convert numeric columns
                numeric_cols = ['Adj_Close', 'Close', 'High', 'Low', 'Open', 'Volume']
                for col in numeric_cols:
                    if col in stock_data.columns:
                        before_conversion = stock_data[col].notna().sum()
                        stock_data[col] = pd.to_numeric(stock_data[col], errors='coerce')
                        after_conversion = stock_data[col].notna().sum()
                        print(f"    {col}: {after_conversion}/{before_conversion} valid values")
                
                # Remove rows where all numeric columns are NaN
                before_numeric_filter = len(stock_data)
                stock_data = stock_data.dropna(how='all', subset=numeric_cols)
                after_numeric_filter = len(stock_data)
                
                print(f"  🔢 After numeric filtering: {after_numeric_filter}/{before_numeric_filter}")
                
                if stock_data.empty:
                    print(f"  ❌ No valid data remaining for {symbol}")
                    continue
                
                # Sort by date
                stock_data.sort_index(inplace=True)
                
                # Store the cleaned data
                data[symbol] = stock_data
                
                # Show summary
                date_range = f"{stock_data.index.min().strftime('%Y-%m-%d')} to {stock_data.index.max().strftime('%Y-%m-%d')}"
                print(f"  ✅ Successfully loaded {symbol}: {len(stock_data)} rows")
                print(f"     📅 Date range: {date_range}")
                print(f"     💹 Adj_Close range: ${stock_data['Adj_Close'].min():.2f} - ${stock_data['Adj_Close'].max():.2f}")
                
            except Exception as e:
                print(f"❌ Failed to load {symbol}: {e}")
                import traceback
                print(f"   Full error: {traceback.format_exc()}")
        else:
            print(f"❌ File not found: {filepath}")
    
    print(f"\n📊 Successfully loaded {len(data)} symbols: {list(data.keys())}")
    
    # Show overall summary
    if data:
        total_rows = sum(len(df) for df in data.values())
        print(f"📈 Total data points across all symbols: {total_rows}")
        
        # Show date ranges for all loaded symbols
        print("\n📅 Date ranges by symbol:")
        for symbol, df in data.items():
            print(f"  {symbol}: {df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')} ({len(df)} rows)")

# Load data on startup
load_stock_data()

# Technical analysis functions
def calculate_rsi(series, window=14):
    """Calculate Relative Strength Index"""
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(series, window=20):
    """Calculate Bollinger Bands"""
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper_band = sma + (2 * std)
    lower_band = sma - (2 * std)
    return sma, upper_band, lower_band

def calculate_macd(series, short_window=12, long_window=26, signal_window=9):
    """Calculate MACD"""
    short_ema = series.ewm(span=short_window, adjust=False).mean()
    long_ema = series.ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    return macd, signal

# Routes
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "Stock Analysis Server - Ready!", 
        "status": "OK",
        "loaded_symbols": len(data),
        "symbols": list(data.keys()),
        "total_data_points": sum(len(df) for df in data.values()) if data else 0
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy" if data else "no_data",
        "loaded_symbols": list(data.keys()),
        "total_symbols": len(data),
        "data_summary": {
            symbol: {
                "rows": len(df),
                "date_range": f"{df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}"
            } for symbol, df in list(data.items())[:3]
        } if data else {}
    })

@app.route('/symbols', methods=['GET'])
def get_symbols():
    return jsonify({
        "available_symbols": list(data.keys()),
        "total_count": len(data)
    })

@app.route('/stock/graph', methods=['GET'])
def stock_graph():
    print(f"\n📊 Graph request received")
    print(f"Request args: {dict(request.args)}")
    
    symbols_param = request.args.get('symbols', '')
    graph_type = request.args.get('graph_type', '')
    
    # Validation
    if not data:
        return jsonify({"error": "No stock data available. Server may still be loading data."}), 500
    
    if not symbols_param.strip():
        return jsonify({"error": "Missing 'symbols' parameter"}), 400
    
    if not graph_type.strip():
        return jsonify({"error": "Missing 'graph_type' parameter"}), 400
    
    # Parse and validate symbols
    symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
    valid_symbols = [s for s in symbols if s in data]
    invalid_symbols = [s for s in symbols if s not in data]
    
    if not valid_symbols:
        return jsonify({
            "error": f"No valid symbols. Invalid: {invalid_symbols}. Available: {list(data.keys())}"
        }), 400
    
    print(f"✅ Processing symbols: {valid_symbols}")
    
    try:
        plt.figure(figsize=(14, 8))
        plt.style.use('default')  # Ensure consistent styling
        
        if graph_type == 'daily_returns':
            for symbol in valid_symbols:
                adj_close = data[symbol]['Adj_Close'].dropna()
                returns = adj_close.pct_change().dropna()
                plt.plot(returns.index, returns * 100, label=f'{symbol}', alpha=0.8, linewidth=1)
            
            plt.title('Daily Returns (%)', fontsize=16, fontweight='bold')
            plt.ylabel('Daily Return (%)', fontsize=12)
            plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
        elif graph_type == 'rolling_mean':
            window = 20
            for symbol in valid_symbols:
                adj_close = data[symbol]['Adj_Close'].dropna()
                rolling_mean = adj_close.rolling(window=window).mean()
                plt.plot(rolling_mean.index, rolling_mean, label=f'{symbol}', alpha=0.8, linewidth=1.5)
            
            plt.title(f'{window}-Day Simple Moving Average', fontsize=16, fontweight='bold')
            plt.ylabel('Price ($)', fontsize=12)
            
        elif graph_type == 'bollinger_bands':
            colors = ['blue', 'red', 'green', 'orange', 'purple']
            for i, symbol in enumerate(valid_symbols):
                color = colors[i % len(colors)]
                adj_close = data[symbol]['Adj_Close'].dropna()
                sma, upper, lower = calculate_bollinger_bands(adj_close)
                
                plt.plot(adj_close.index, adj_close, label=f'{symbol} Price', 
                        color=color, alpha=0.7, linewidth=1)
                plt.plot(sma.index, sma, label=f'{symbol} SMA', 
                        color=color, alpha=0.8, linewidth=1.5, linestyle='--')
                plt.fill_between(adj_close.index, upper, lower, alpha=0.1, color=color)
            
            plt.title('Bollinger Bands (20-day, 2σ)', fontsize=16, fontweight='bold')
            plt.ylabel('Price ($)', fontsize=12)
            
        elif graph_type == 'rsi':
            for symbol in valid_symbols:
                adj_close = data[symbol]['Adj_Close'].dropna()
                rsi = calculate_rsi(adj_close)
                plt.plot(rsi.index, rsi, label=f'{symbol}', alpha=0.8, linewidth=1.5)
            
            plt.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Overbought (70)')
            plt.axhline(y=30, color='red', linestyle='--', alpha=0.7, label='Oversold (30)')
            plt.axhline(y=50, color='gray', linestyle='-', alpha=0.3)
            plt.title('Relative Strength Index (RSI)', fontsize=16, fontweight='bold')
            plt.ylabel('RSI', fontsize=12)
            plt.ylim(0, 100)
            
        elif graph_type == 'macd':
            for symbol in valid_symbols:
                adj_close = data[symbol]['Adj_Close'].dropna()
                macd, signal = calculate_macd(adj_close)
                plt.plot(macd.index, macd, label=f'{symbol} MACD', alpha=0.8, linewidth=1.5)
                plt.plot(signal.index, signal, label=f'{symbol} Signal', alpha=0.8, linewidth=1, linestyle='--')
            
            plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            plt.title('MACD (12, 26, 9)', fontsize=16, fontweight='bold')
            plt.ylabel('MACD', fontsize=12)
            
        else:
            return jsonify({
                "error": f"Invalid graph type: {graph_type}. Available: daily_returns, rolling_mean, bollinger_bands, rsi, macd"
            }), 400
        
        # Common formatting
        plt.xlabel('Date', fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save plot
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        plt.close()
        
        print(f"✅ Successfully generated {graph_type} for {valid_symbols}")
        return send_file(buf, mimetype='image/png')
        
    except Exception as e:
        plt.close()
        error_msg = f"Error generating plot: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route('/api/stocks/<ticker>/chart', methods=['GET'])
def get_candlestick_chart(ticker):
    """Generate candlestick chart"""
    ticker = ticker.upper()
    
    if not data or ticker not in data:
        return jsonify({"error": f"Symbol {ticker} not found"}), 404
    
    try:
        stock_data = data[ticker]
        ohlc_data = stock_data[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
        
        if len(ohlc_data) > 500:  # Limit for performance
            ohlc_data = ohlc_data.tail(500)
        
        buf = io.BytesIO()
        mpf.plot(
            ohlc_data,
            type='candle',
            style='charles',
            title=f'{ticker} Candlestick Chart (Last {len(ohlc_data)} days)',
            ylabel='Price ($)',
            volume=True,
            figratio=(14, 8),
            figscale=1.0,
            savefig=dict(fname=buf, format='png', dpi=300, bbox_inches='tight')
        )
        buf.seek(0)
        
        print(f"✅ Generated candlestick chart for {ticker}")
        return send_file(buf, mimetype='image/png')
        
    except Exception as e:
        return jsonify({"error": f"Error generating candlestick: {str(e)}"}), 500

@app.route('/api/stocks/<ticker>/volume', methods=['GET'])
def get_trading_volume(ticker):
    """Generate volume chart"""
    ticker = ticker.upper()
    
    if not data or ticker not in data:
        return jsonify({"error": f"Symbol {ticker} not found"}), 404
    
    try:
        volume_data = data[ticker]['Volume'].dropna()
        
        plt.figure(figsize=(14, 7))
        plt.plot(volume_data.index, volume_data, color='steelblue', alpha=0.7, linewidth=1)
        plt.fill_between(volume_data.index, volume_data, alpha=0.3, color='steelblue')
        plt.title(f'{ticker} Trading Volume', fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Volume', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        plt.close()
        
        print(f"✅ Generated volume chart for {ticker}")
        return send_file(buf, mimetype='image/png')
        
    except Exception as e:
        plt.close()
        return jsonify({"error": f"Error generating volume chart: {str(e)}"}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    if not data:
        print("❌ WARNING: No data loaded!")
        print("   - Check if 'Financial Data' directory exists")
        print("   - Check if CSV files are present and readable")
        print("   - Review error messages above")
    else:
        print("🚀 SERVER READY!")
        print(f"📊 Loaded {len(data)} symbols: {list(data.keys())}")
        total_rows = sum(len(df) for df in data.values())
        print(f"📈 Total data points: {total_rows:,}")
        print(f"📅 Date range: {min(df.index.min() for df in data.values()).strftime('%Y-%m-%d')} to {max(df.index.max() for df in data.values()).strftime('%Y-%m-%d')}")
        
        print("\n🎯 Available endpoints:")
        print("  GET /health - Server status")
        print("  GET /symbols - Available symbols")
        print("  GET /stock/graph - Main charting endpoint")
        print("  GET /api/stocks/<ticker>/chart - Candlestick charts")
        print("  GET /api/stocks/<ticker>/volume - Volume charts")
    
    print("="*60)
    app.run(debug=True, host='127.0.0.1', port=5000)