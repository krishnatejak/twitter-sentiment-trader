import pandas as pd
import os
from typing import List, Dict
from datetime import datetime, timedelta
from ..models.tweet import Tweet
from ..models.trade import Trade
from ..sentiment.analyzer import SentimentAnalyzer
from ..twitter.stream import TwitterStream
from ..config.settings import settings

class Backtester:
    def __init__(self, start_date: str, end_date: str):
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.analyzer = SentimentAnalyzer()
        self.trades: List[Trade] = []
        self.performance_metrics: Dict = {}
        
        # Initialize Twitter stream with environment variables
        self.twitter_stream = TwitterStream(
            api_key=os.getenv('TWITTER_API_KEY'),
            api_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )

    def load_historical_data(self, symbol: str) -> pd.DataFrame:
        """Load historical price data for a symbol"""
        # Implementation needed to fetch historical data
        # Could be from a CSV file or an API
        pass

    def process_tweet(self, tweet: Tweet):
        """Process a single tweet for backtesting"""
        tweet.sentiment = self.analyzer.analyze(tweet)
        # Store tweet data for analysis
        # Implementation needed

    def run_backtest(self, handle: str, symbol: str):
        """Run backtest for a specific handle and symbol"""
        print(f"Running backtest for {handle} on {symbol}")
        
        # Load historical price data
        prices = self.load_historical_data(symbol)
        if prices is None:
            print(f"No historical data available for {symbol}")
            return

        current_date = self.start_date
        tweets_processed = 0
        
        while current_date <= self.end_date:
            # Check if we've hit the API limit for the day
            if tweets_processed >= settings.TWEETS_PER_DAY_LIMIT:
                print(f"API limit reached for {current_date.date()}")
                current_date += timedelta(days=1)
                tweets_processed = 0
                continue

            # Get tweets for the current date
            def tweet_callback(tweet: Tweet):
                # Process tweet if within market hours
                if self.twitter_stream.is_market_hours(tweet.created_at):
                    self.process_tweet(tweet)
                    nonlocal tweets_processed
                    tweets_processed += 1

            self.twitter_stream.start_stream(
                handles=[handle],
                callback=tweet_callback,
                is_backtest=True
            )

            current_date += timedelta(days=1)

        self.calculate_performance()

    def calculate_performance(self):
        """Calculate performance metrics"""
        if not self.trades:
            return

        # Calculate various metrics
        total_trades = len(self.trades)
        profitable_trades = len([t for t in self.trades if t.pnl > 0])
        win_rate = profitable_trades / total_trades
        total_pnl = sum(t.pnl for t in self.trades)

        # Calculate market hours specific metrics
        open_trades = [t for t in self.trades if t.entry_time.hour < 10]  # Trades near market open
        close_trades = [t for t in self.trades if t.entry_time.hour > 14]  # Trades near market close

        self.performance_metrics = {
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'open_trades_pnl': sum(t.pnl for t in open_trades),
            'close_trades_pnl': sum(t.pnl for t in close_trades),
            'open_trades_win_rate': len([t for t in open_trades if t.pnl > 0]) / len(open_trades) if open_trades else 0,
            'close_trades_win_rate': len([t for t in close_trades if t.pnl > 0]) / len(close_trades) if close_trades else 0
        }