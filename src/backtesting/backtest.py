import pandas as pd
import os
import numpy as np
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from ..models.tweet import Tweet
from ..models.trade import Trade
from ..sentiment.analyzer import SentimentAnalyzer
from ..twitter.stream import TwitterStream
from ..twitter.symbol_extractor import SymbolExtractor
from ..trading.historical_data import HistoricalDataFetcher
from ..config.settings import settings

class Backtester:
    def __init__(self, start_date: str, end_date: str):
        # Initialize components
        self.historical_data = HistoricalDataFetcher(
            api_key=os.getenv('KITE_API_KEY'),
            api_secret=os.getenv('KITE_API_SECRET')
        )
        
        self.symbol_extractor = SymbolExtractor(self.historical_data)
        self.analyzer = SentimentAnalyzer()
        self.twitter_stream = TwitterStream(
            api_key=os.getenv('TWITTER_API_KEY'),
            api_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )
        
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.trades: List[Trade] = []
        self.symbols_traded: Set[str] = set()
        self.performance_metrics: Dict = {}
        self.symbol_metrics: Dict[str, Dict] = {}

    def process_tweet(
        self, 
        tweet: Tweet, 
        price_data: Dict[str, pd.DataFrame]
    ) -> List[Trade]:
        """Process a single tweet for backtesting"""
        trades = []
        
        # Analyze sentiment
        tweet.sentiment = self.analyzer.analyze(tweet)
        
        # Only proceed if sentiment is super positive
        if tweet.sentiment != 'SUPER_POSITIVE':
            return trades
            
        # Extract symbols with confidence
        symbol_info = self.symbol_extractor.analyze_symbols(tweet.text)
        
        # Trade only high-confidence symbols
        for info in symbol_info:
            if info['confidence'] >= 0.7 and info['symbol'] in price_data:
                trade = self.simulate_trade(
                    info['symbol'],
                    tweet,
                    price_data[info['symbol']]
                )
                if trade:
                    trades.append(trade)
                    self.symbols_traded.add(info['symbol'])
        
        return trades

    def simulate_trade(
        self, 
        symbol: str, 
        tweet: Tweet, 
        price_data: pd.DataFrame
    ) -> Optional[Trade]:
        """Simulate a trade based on tweet sentiment and historical prices"""
        if price_data.empty:
            return None

        tweet_time = tweet.created_at
        
        # Find entry price (first price after tweet)
        entry_data = price_data[price_data.index > tweet_time]
        if entry_data.empty:
            return None
            
        entry_price = entry_data.iloc[0]['open']
        entry_time = entry_data.index[0]

        # Calculate position size
        quantity = int(settings.TRADE_AMOUNT / entry_price)
        if quantity <= 0:
            return None

        # Find exit price based on stop loss and target
        stop_loss = entry_price * (1 - settings.STOP_LOSS_PERCENTAGE / 100)
        target = entry_price * (1 + settings.TARGET_PERCENTAGE / 100)
        
        exit_data = price_data[price_data.index > entry_time]
        exit_price = None
        exit_time = None
        
        for idx, row in exit_data.iterrows():
            if row['low'] <= stop_loss:
                exit_price = stop_loss
                exit_time = idx
                break
            elif row['high'] >= target:
                exit_price = target
                exit_time = idx
                break

        # If no stop loss or target hit, use last price
        if exit_price is None:
            exit_price = exit_data.iloc[-1]['close']
            exit_time = exit_data.index[-1]

        # Calculate P&L
        pnl = (exit_price - entry_price) * quantity

        return Trade(
            symbol=symbol,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            entry_time=entry_time,
            exit_time=exit_time,
            tweet_id=tweet.id,
            handle=tweet.author,
            sentiment=tweet.sentiment,
            pnl=pnl,
            status='CLOSED'
        )

    def run_backtest(self, handle: str):
        """Run backtest for a specific handle"""
        print(f"Running backtest for {handle}")
        
        current_date = self.start_date
        tweets_processed = 0
        
        while current_date <= self.end_date:
            print(f"Processing date: {current_date.date()}")
            
            def tweet_callback(tweet: Tweet):
                nonlocal tweets_processed
                if tweets_processed >= settings.TWEETS_PER_DAY_LIMIT:
                    return
                
                # Get symbols from tweet
                symbol_info = self.symbol_extractor.analyze_symbols(tweet.text)
                symbols = [info['symbol'] for info in symbol_info if info['confidence'] >= 0.7]
                
                if not symbols:
                    return
                    
                # Get market data for all symbols
                market_data = {}
                for symbol in symbols:
                    data = self.historical_data.get_opening_closing_data(
                        symbol,
                        current_date,
                        window_minutes=settings.MARKET_OPENING_WINDOW
                    )
                    if not data['opening'].empty or not data['closing'].empty:
                        market_data[symbol] = pd.concat([data['opening'], data['closing']])
                
                # Process trades
                new_trades = self.process_tweet(tweet, market_data)
                self.trades.extend(new_trades)
                tweets_processed += 1

            # Get tweets for the day
            self.twitter_stream.start_stream(
                handles=[handle],
                callback=tweet_callback,
                is_backtest=True
            )

            current_date += timedelta(days=1)
            tweets_processed = 0

        self.calculate_performance()

    def calculate_symbol_metrics(self):
        """Calculate performance metrics for each symbol"""
        for symbol in self.symbols_traded:
            symbol_trades = [t for t in self.trades if t.symbol == symbol]
            
            if not symbol_trades:
                continue
                
            total_trades = len(symbol_trades)
            profitable_trades = len([t for t in symbol_trades if t.pnl > 0])
            total_pnl = sum(t.pnl for t in symbol_trades)
            
            self.symbol_metrics[symbol] = {
                'total_trades': total_trades,
                'profitable_trades': profitable_trades,
                'win_rate': profitable_trades / total_trades if total_trades > 0 else 0,
                'total_pnl': total_pnl,
                'avg_trade_pnl': total_pnl / total_trades if total_trades > 0 else 0
            }

    def generate_report(self) -> str:
        """Generate a detailed performance report"""
        if not self.performance_metrics:
            return "No performance data available."

        report = []
        report.append("=== Backtest Performance Report ===\n")
        
        # Overall performance
        report.append("Overall Performance:")
        report.append(f"Total Trades: {self.performance_metrics['total_trades']}")
        report.append(f"Win Rate: {self.performance_metrics['win_rate']:.2%}")
        report.append(f"Total P&L: ₹{self.performance_metrics['total_pnl']:,.2f}")
        report.append(f"Sharpe Ratio: {self.performance_metrics['sharpe_ratio']:.2f}")
        
        # Symbol-wise performance
        report.append("\nSymbol Performance:")
        for symbol, metrics in self.symbol_metrics.items():
            report.append(f"\n{symbol}:")
            report.append(f"  Trades: {metrics['total_trades']}")
            report.append(f"  Win Rate: {metrics['win_rate']:.2%}")
            report.append(f"  Total P&L: ₹{metrics['total_pnl']:,.2f}")
        
        # Market timing analysis
        report.append("\nMarket Timing Analysis:")
        report.append(f"Opening Win Rate: {self.performance_metrics['opening_win_rate']:.2%}")
        report.append(f"Closing Win Rate: {self.performance_metrics['closing_win_rate']:.2%}")
        
        # Risk metrics
        report.append("\nRisk Metrics:")
        report.append(f"Max Drawdown: ₹{abs(self.performance_metrics['max_drawdown']):,.2f}")
        report.append(f"Profit Factor: {self.performance_metrics['profit_factor']:.2f}")
        
        return "\n".join(report)