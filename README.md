# Stock Market Dashboard

A real-time stock market dashboard built with Flask and React that provides technical analysis and visualization tools for various stock symbols.

## Features

- Real-time stock data visualization
- Multiple technical analysis tools:
  - Daily Returns Analysis
  - Rolling Mean (Simple Moving Average)
  - Bollinger Bands
  - Relative Strength Index (RSI)
  - Moving Average Convergence Divergence (MACD)
  - Candlestick Charts
  - Trading Volume Analysis

## Project Structure

```
dashboard-flask/
├── backend/
│   ├── unified_flask_server.py    # Main Flask server
│   ├── requirements.txt          # Python dependencies
│   └── Financial Data/          # Stock CSV data files
│       ├── AAPL.csv
│       ├── MSFT.csv
│       └── ...
└── frontend/
    ├── src/
    │   ├── App.js              # Main React component
    │   └── ...
    └── package.json            # Node dependencies
```

## Setup

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv flask-viz-env
# On Windows
flask-viz-env\Scripts\activate
# On Unix or MacOS
source flask-viz-env/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the Flask server:
```bash
python unified_flask_server.py
```

The server will start on `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## Available Stock Symbols

The dashboard currently supports the following stock symbols:
- AAPL (Apple)
- MSFT (Microsoft)
- GOOG (Google)
- AMZN (Amazon)
- TSLA (Tesla)
- SPY (S&P 500 ETF)
- NVDA (NVIDIA)
- META (Meta)
- NFLX (Netflix)
- AMD (Advanced Micro Devices)

## API Endpoints

- `GET /health` - Server health status
- `GET /symbols` - List of available stock symbols
- `GET /stock/graph` - Generate technical analysis graphs
  - Parameters:
    - `symbols`: Comma-separated list of stock symbols
    - `graph_type`: Type of analysis (daily_returns, rolling_mean, bollinger_bands, rsi, macd)
- `GET /api/stocks/<ticker>/chart` - Generate candlestick charts
- `GET /api/stocks/<ticker>/volume` - Generate volume analysis charts

## Technologies Used

### Backend
- Flask (Python web framework)
- Pandas (Data manipulation)
- Matplotlib (Data visualization)
- mplfinance (Financial charts)
- NumPy (Numerical computations)

### Frontend
- React
- Tailwind CSS
- Axios (API requests)

