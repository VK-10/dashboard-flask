import React, { useState } from 'react';

const StockAnalysisApp = () => {
  const [selectedSymbols, setSelectedSymbols] = useState([]);
  const [graphType, setGraphType] = useState('');
  const [imageSrc, setImageSrc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const stockSymbols = [
    'AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'SPY', 'NVDA', 'META', 'NFLX', 'AMD',
  ];

  const graphTypes = [
    { value: 'daily_returns', label: 'Daily Returns' },
    { value: 'rolling_mean', label: 'Rolling Mean' },
    { value: 'bollinger_bands', label: 'Bollinger Bands' },
    { value: 'rsi', label: 'RSI' },
    { value: 'macd', label: 'MACD' },
    { value: 'trading', label: 'Trading Volume' },
    { value: 'candlestick', label: 'Candlestick Chart' }
  ];

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://127.0.0.1:5000';
  // const separateUrlCandelStick='http://127.0.0.1:5002';
  // const separateUrlTradingVolume='http://127.0.0.1:5003';

  const handleGenerateGraph = async () => {
    if (!selectedSymbols.length || !graphType) {
      alert('Please select stock symbols and graph type.');
      return;
    }

    setLoading(true);
    setImageSrc(null);
    setErrorMessage('');

    try {
      let apiUrl='';

      if(graphType==='candlestick'){
        apiUrl=`${backendUrl}/api/stocks/${selectedSymbols[0]}/chart`
      } else if(graphType==='trading'){
        apiUrl =  `${backendUrl}/api/stocks/${selectedSymbols[0]}/volume`;
      }else{
        apiUrl = `${backendUrl}/stock/graph?symbols=${selectedSymbols.join(',')}&graph_type=${graphType}`;
      }


      const response = await fetch(apiUrl);

      if (!response.ok) {
        throw new Error('Failed to generate graph. Please check if the backend server is running.');
      }

      const blob = await response.blob();
      console.log(blob)
      const imageUrl = URL.createObjectURL(blob);
      setImageSrc(imageUrl);
    } catch (error) {
      console.error('Error generating graph:', error);
      setErrorMessage('Failed to generate graph. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <div className="bg-gray-100 rounded-lg shadow-lg p-6">
        {/* Header Section */}
        <h1 className="text-2xl font-bold text-center mb-4">
          Stock Analysis Graph Generator
        </h1>
        <p className="text-center text-gray-500 mb-8">
          Analyze stocks with various visual tools by selecting symbols and graph type.
        </p>

        {/* Selection Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Stock Symbols
            </label>
            <select
              multiple
              value={selectedSymbols}
              onChange={(e) =>
                setSelectedSymbols(
                  Array.from(e.target.selectedOptions, (option) => option.value)
                )
              }
              className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
              aria-label="Select stock symbols"
            >
              {stockSymbols.map((symbol) => (
                <option key={symbol} value={symbol}>
                  {symbol}
                </option>
              ))}
            </select>
            <p className="text-sm text-gray-500 mt-2">
              Hold Ctrl (Cmd on Mac) to select multiple symbols.
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Graph Type
            </label>
            <select
              value={graphType}
              onChange={(e) => setGraphType(e.target.value)}
              className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
              aria-label="Select graph type"
            >
              <option value="">-- Select Graph Type --</option>
              {graphTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Generate Button */}
        <div className="text-center mt-6">
          <button
            onClick={handleGenerateGraph}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Generating...' : 'Generate Graph'}
          </button>
        </div>

        {/* Error Message */}
        {errorMessage && (
          <div className="mt-4 text-center text-red-500">
            {errorMessage}
          </div>
        )}

        {/* Result Section */}
        {imageSrc && (
          <div className="mt-6 text-center">
            <h3 className="font-bold mb-4">Generated Graph</h3>
            <img
              src={imageSrc}
              alt="Generated Graph"
              className="w-full max-w-4xl mx-auto rounded-md shadow-md"
              style={{height:'auto'}}

            />
          </div>
        )}
      </div>
    </div>
  );
};

export default StockAnalysisApp;
