import tweepy
import pytz
from typing import List, Callable, Optional
from datetime import datetime, timedelta
import json
import os
from ..config.settings import settings
from ..models.tweet import Tweet

class TwitterStream:
    def __init__(self, api_key: str, api_secret: str, access_token: str, access_token_secret: str):
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        self.ist_tz = pytz.timezone('Asia/Kolkata')
        self.cache_dir = 'tweet_cache'
        os.makedirs(self.cache_dir, exist_ok=True)

    def is_market_hours(self, dt: datetime) -> bool:
        """Check if given time is within market opening or closing window"""
        ist_time = dt.astimezone(self.ist_tz).time()
        
        # Check market opening window
        market_open = datetime.combine(dt.date(), settings.MARKET_OPEN_TIME)
        open_start = market_open - timedelta(minutes=settings.MARKET_OPENING_WINDOW)
        open_end = market_open + timedelta(minutes=settings.MARKET_OPENING_WINDOW)
        
        # Check market closing window
        market_close = datetime.combine(dt.date(), settings.MARKET_CLOSE_TIME)
        close_start = market_close - timedelta(minutes=settings.MARKET_CLOSING_WINDOW)
        close_end = market_close + timedelta(minutes=settings.MARKET_CLOSING_WINDOW)
        
        return (open_start.time() <= ist_time <= open_end.time() or 
                close_start.time() <= ist_time <= close_end.time())

    def get_cache_path(self, handle: str, date: datetime) -> str:
        """Get cache file path for a specific handle and date"""
        date_str = date.strftime('%Y-%m-%d')
        return os.path.join(self.cache_dir, f'{handle}_{date_str}.json')

    def save_to_cache(self, handle: str, date: datetime, tweets: List[dict]):
        """Save tweets to cache"""
        if settings.CACHE_TWEETS:
            cache_path = self.get_cache_path(handle, date)
            with open(cache_path, 'w') as f:
                json.dump(tweets, f)

    def load_from_cache(self, handle: str, date: datetime) -> Optional[List[dict]]:
        """Load tweets from cache if available"""
        if settings.CACHE_TWEETS:
            cache_path = self.get_cache_path(handle, date)
            if os.path.exists(cache_path):
                with open(cache_path, 'r') as f:
                    return json.load(f)
        return None

    def start_stream(self, handles: List[str], callback: Callable[[Tweet], None], is_backtest: bool = False):
        """Start streaming tweets from specified handles"""
        current_time = datetime.now(self.ist_tz)
        
        # Skip if not market hours (only for live trading)
        if not is_backtest and not self.is_market_hours(current_time):
            return

        for handle in handles:
            try:
                # Try loading from cache first
                cached_tweets = self.load_from_cache(handle, current_time)
                
                if cached_tweets is not None:
                    for tweet_data in cached_tweets:
                        tweet_obj = Tweet(
                            id=tweet_data['id'],
                            text=tweet_data['text'],
                            author=handle,
                            created_at=datetime.fromisoformat(tweet_data['created_at'])
                        )
                        callback(tweet_obj)
                    continue

                # If not in cache, fetch from API
                user = self.client.get_user(username=handle)
                if user.data:
                    # For backtesting, limit the number of tweets
                    tweet_limit = settings.TWEETS_PER_DAY_LIMIT if is_backtest else None
                    
                    tweets = self.client.get_users_tweets(
                        user.data.id,
                        max_results=tweet_limit
                    )
                    
                    if tweets.data:
                        # Filter tweets by market hours
                        market_tweets = []
                        for tweet in tweets.data:
                            tweet_time = tweet.created_at.astimezone(self.ist_tz)
                            if is_backtest or self.is_market_hours(tweet_time):
                                tweet_obj = Tweet(
                                    id=tweet.id,
                                    text=tweet.text,
                                    author=handle,
                                    created_at=tweet_time
                                )
                                callback(tweet_obj)
                                market_tweets.append({
                                    'id': str(tweet.id),
                                    'text': tweet.text,
                                    'created_at': tweet_time.isoformat()
                                })
                        
                        # Cache the tweets
                        self.save_to_cache(handle, current_time, market_tweets)

            except Exception as e:
                print(f'Error processing handle {handle}: {str(e)}')