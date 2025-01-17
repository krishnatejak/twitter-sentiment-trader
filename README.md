# Twitter Sentiment Trader

An automated trading system that monitors specific Twitter handles, analyzes tweet sentiment, and executes trades based on sentiment analysis. Includes backtesting capabilities and performance scoring.

## Features

- Real-time Twitter stream monitoring
- Sentiment analysis using transformer models
- Automated trading via Zerodha Kite
- Backtesting framework
- Performance scoring for Twitter handles
- Support for multiple stock symbols
- Configurable trading parameters
- Performance analytics and reporting

## Prerequisites

- Python 3.8+
- Twitter API credentials (Developer Account)
- Zerodha Kite API credentials
- PostgreSQL database (optional, for storing historical data)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/krishnatejak/twitter-sentiment-trader.git
cd twitter-sentiment-trader
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy .env.example to .env and fill in your credentials:
```bash
cp .env.example .env
```

## Configuration

Edit `src/config/settings.py` to configure:
- Twitter handles to monitor
- Sentiment thresholds
- Trading parameters (amount, stop loss, target)
- Backtesting parameters

## Usage

1. Start the main trading application:
```bash
python src/main.py
```

2. Run backtesting:
```bash
python src/backtesting/run_backtest.py
```

3. View handle performance:
```bash
python src/analysis/handle_performance.py
```

## Trading Strategy

The system follows these steps:
1. Monitors specified Twitter handles in real-time
2. Analyzes sentiment of each tweet using a pre-trained model
3. Extracts stock symbols from tweets
4. Places trades when sentiment is "SUPER_POSITIVE"
5. Manages positions with configurable stop-loss and target levels

## Backtesting

The backtesting module allows you to:
- Test your strategy on historical data
- Analyze performance metrics
- Compare different parameter settings
- Generate performance reports

## Handle Performance Analysis

Evaluate Twitter handle performance based on:
- Total number of trades
- Win rate
- Total P&L
- Average return per trade
- Risk-adjusted metrics

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.