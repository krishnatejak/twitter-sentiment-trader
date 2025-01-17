import os
import time
from datetime import datetime
from dotenv import load_dotenv
from twitter.stream import TwitterStream
from sentiment.analyzer import SentimentAnalyzer
from trading.trader import Trader
from models.trade import Trade
from config.settings import settings

class TweetSentimentTrader:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Initialize components
        self.twitter_stream = TwitterStream(
            api_key=os.getenv('TWITTER_API_KEY'),
            api_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )

        self.sentiment_analyzer = SentimentAnalyzer()
        
        self.trader = Trader(
            api_key=os.getenv('KITE_API_KEY'),
            api_secret=os.getenv('KITE_API_SECRET')
        )

    def process_tweet(self, tweet):
        """Process incoming tweet and make trading decisions"""
        # Analyze sentiment
        sentiment = self.sentiment_analyzer.analyze(tweet)
        tweet.sentiment = sentiment

        # If super positive sentiment, place trade
        if sentiment == 'SUPER_POSITIVE':
            # Extract stock symbol from tweet (implement your logic here)
            symbol = self.extract_symbol(tweet.text)
            if symbol:
                # Get current price
                price = self.trader.get_ltp(symbol)
                if price:
                    # Calculate quantity based on settings.TRADE_AMOUNT
                    quantity = int(settings.TRADE_AMOUNT / price)
                    
                    # Place buy order
                    order_id = self.trader.place_trade(symbol, quantity, 'BUY')
                    if order_id:
                        # Create trade record
                        trade = Trade(
                            symbol=symbol,
                            entry_price=price,
                            quantity=quantity,
                            entry_time=datetime.now(),
                            tweet_id=tweet.id,
                            handle=tweet.author,
                            sentiment=sentiment,
                            status='OPEN'
                        )
                        # Store trade for tracking
                        self.trader.positions[order_id] = trade

    def extract_symbol(self, text: str) -> str:
        """Extract stock symbol from tweet text"""
        # Implement your symbol extraction logic here
        # This could involve looking for cashtags ($AAPL) or company names
        # For now, return None
        return None

    def run(self):
        """Main application loop"""
        print("Starting Tweet Sentiment Trader...")
        
        while True:
            try:
                # Start streaming tweets
                self.twitter_stream.start_stream(
                    handles=settings.TWITTER_HANDLES,
                    callback=self.process_tweet
                )
                
                # Sleep for the configured interval
                time.sleep(settings.TWEET_FETCH_INTERVAL)
                
            except Exception as e:
                print(f"Error in main loop: {str(e)}")
                time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    trader = TweetSentimentTrader()
    trader.run()