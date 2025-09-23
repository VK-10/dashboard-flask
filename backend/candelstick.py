from flask import Flask, jsonify, request, send_file
import pandas as pd
from flask_cors import CORS
import os
import mplfinance as mpf
import io
import matplotlib
from datetime import datetime

# Use Agg backend for Matplotlib in a headless server environment
matplotlib.use("Agg")

app = Flask(__name__)
CORS(app)

# Define the directory where CSV files are stored
directory = "Financial Data"

@app.route('/api/stocks/<ticker>', methods=['GET'])
def get_stock_data(ticker):
    """
    Fetch and return stock data for a given ticker.
    """
    filepath = os.path.join(directory, f"{ticker}.csv")
    
    if not os.path.exists(filepath):
        return jsonify({"error": f"Data for {ticker} not found."}), 404
    
    try:
        # Load and clean data
        stock_data = pd.read_csv(filepath, skiprows=2, names=['Date', 'Adj_Close', 'Close', 'High', 'Low', 'Open', 'Volume'])
        stock_data = stock_data[~stock_data['Date'].str.contains('Date', na=False)]
        
        # Parse the 'Date' column, handling various possible formats
        stock_data['Date'] = pd.to_datetime(stock_data['Date'], errors='coerce')
        stock_data = stock_data.dropna(subset=['Date'])  # Drop rows where 'Date' conversion failed
        
        return stock_data.to_json(orient='records', date_format='iso'), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stocks/<ticker>/chart', methods=['GET'])
def get_candlestick_chart(ticker):
    """
    Generate and return a candlestick chart for a given ticker as an image.
    """
    filepath = os.path.join(directory, f"{ticker}.csv")
    
    if not os.path.exists(filepath):
        return jsonify({"error": f"Data for {ticker} not found."}), 404
    
    try:
        # Load and clean data
        stock_data = pd.read_csv(filepath, skiprows=2, names=['Date', 'Adj_Close', 'Close', 'High', 'Low', 'Open', 'Volume'])
        stock_data = stock_data[~stock_data['Date'].str.contains('Date', na=False)]
        
        # Parse the 'Date' column, handling various possible formats
        stock_data['Date'] = pd.to_datetime(stock_data['Date'], errors='coerce')
        stock_data = stock_data.dropna(subset=['Date'])  # Drop rows where 'Date' conversion failed
        
        stock_data.set_index('Date', inplace=True)
        ohlc_data = stock_data[['Open', 'High', 'Low', 'Close', 'Volume']]

        # If the dataset is too large, consider plotting only a subset of the data
        if len(ohlc_data) > 1000:  # Limit to the last 1000 rows
            ohlc_data = ohlc_data.tail(1000)

        # Create chart
        img = io.BytesIO()
        mpf.plot(
            ohlc_data,
            type='candle',
            style='charles',
            title=f'{ticker} Candlestick Chart',
            ylabel='Price',
            volume=True,
            figratio=(12, 8),
            figscale=1.2,
            savefig=dict(fname=img, format='png'),
            warn_too_much_data=1000  # Suppress large data warnings
        )
        img.seek(0)
        return send_file(img, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True,port=5002)
