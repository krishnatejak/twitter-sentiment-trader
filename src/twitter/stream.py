import tweepy
import pytz
from typing import List, Callable, Optional
from datetime import datetime, timedelta
import json
import os
from ..config.settings import settings
from ..models.tweet import Tweet
import logging

logger = logging.getLogger(__name__)

class TwitterStream:
    def __init__(self, api_key: str, api_secret: str, access_token: str, access_token_secret: str, bearer_token: str = None):
        logger.debug("Initializing TwitterStream")
        
        if not bearer_token:
            logger.error("Bearer token is required for Twitter API v2")
            raise ValueError("Bearer token is required")

        try:
            logger.debug("Initializing Twitter Client with Bearer Token")
            self.client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                wait_on_rate_limit=True
            )
            logger.info("Successfully initialized Twitter API client")
        except Exception as e:
            logger.error(f"Error initializing Twitter API: {str(e)}")
            raise

        self.ist_tz = pytz.timezone('Asia/Kolkata')
        self.cache_dir = 'tweet_cache'
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_users_tweets(self, user_id: str, limit: Optional[int] = None) -> List[dict]:
        logger.debug(f"Fetching tweets for user_id: {user_id}, limit: {limit}")
        try:
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=limit or 100,
                exclude=['retweets', 'replies'],
                tweet_fields=['created_at', 'public_metrics']
            )
            
            if not tweets.data:
                logger.info(f"No tweets found for user_id: {user_id}")
                return []
            
            logger.info(f"Successfully fetched {len(tweets.data)} tweets")
            return tweets.data
            
        except Exception as e:
            logger.error(f"Error fetching tweets: {str(e)}")
            return []

    def test_connection(self) -> bool:
        """Test the Twitter API connection"""
        try:
            logger.debug("Testing Twitter API connection")
            test_user = self.client.get_user(username="Twitter")
            if test_user.data:
                logger.info("Twitter API connection test successful")
                return True
            return False
        except Exception as e:
            logger.error(f"Twitter API connection test failed: {str(e)}")
            return False

    def start_stream(self, handles: List[str], callback: Callable[[Tweet], None], is_backtest: bool = False):
        """Start streaming tweets from specified handles"""
        logger.info(f"Starting stream for handles: {handles}, is_backtest: {is_backtest}")
        current_time = datetime.now(self.ist_tz)
        
        if not is_backtest and not self.is_market_hours(current_time):
            logger.info("Skipping - Not market hours")
            return

        for handle in handles:
            logger.debug(f"Processing handle: {handle}")
            try:
                # Try loading from cache first
                cached_tweets = self.load_from_cache(handle, current_time)
                
                if cached_tweets is not None:
                    logger.info(f"Using cached tweets for {handle}")
                    for tweet_data in cached_tweets:
                        tweet_obj = Tweet(
                            id=tweet_data['id'],
                            text=tweet_data['text'],
                            author=handle,
                            created_at=datetime.fromisoformat(tweet_data['created_at'])
                        )
                        callback(tweet_obj)
                    continue

                # Get user details
                logger.debug(f"Fetching user details for {handle}")
                user = self.client.get_user(username=handle.lstrip('@'))
                if not user.data:
                    logger.warning(f"User not found: {handle}")
                    continue
                
                logger.info(f"Found user {handle} with id: {user.data.id}")
                
                # Get tweets
                tweet_limit = settings.TWEETS_PER_DAY_LIMIT if is_backtest else None
                tweets = self.get_users_tweets(user.data.id, limit=tweet_limit)
                
                # Process tweets
                market_tweets = []
                for tweet in tweets:
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
                
                # Cache tweets
                if market_tweets:
                    logger.info(f"Caching {len(market_tweets)} tweets for {handle}")
                    self.save_to_cache(handle, current_time, market_tweets)

            except Exception as e:
                logger.error(f"Error processing handle {handle}: {str(e)}", exc_info=True)

    def is_market_hours(self, dt: datetime) -> bool:
        ist_time = dt.astimezone(self.ist_tz).time()
        
        market_open = datetime.combine(dt.date(), settings.MARKET_OPEN_TIME)
        open_start = market_open - timedelta(minutes=settings.MARKET_OPENING_WINDOW)
        open_end = market_open + timedelta(minutes=settings.MARKET_OPENING_WINDOW)
        
        market_close = datetime.combine(dt.date(), settings.MARKET_CLOSE_TIME)
        close_start = market_close - timedelta(minutes=settings.MARKET_CLOSING_WINDOW)
        close_end = market_close + timedelta(minutes=settings.MARKET_CLOSING_WINDOW)
        
        is_opening = open_start.time() <= ist_time <= open_end.time()
        is_closing = close_start.time() <= ist_time <= close_end.time()
        
        logger.debug(f"Time: {ist_time}, Is opening: {is_opening}, Is closing: {is_closing}")
        return is_opening or is_closing

    def get_cache_path(self, handle: str, date: datetime) -> str:
        date_str = date.strftime('%Y-%m-%d')
        return os.path.join(self.cache_dir, f'{handle}_{date_str}.json')

    def save_to_cache(self, handle: str, date: datetime, tweets: List[dict]):
        if settings.CACHE_TWEETS:
            cache_path = self.get_cache_path(handle, date)
            try:
                with open(cache_path, 'w') as f:
                    json.dump(tweets, f)
                logger.debug(f"Saved tweets to cache: {cache_path}")
            except Exception as e:
                logger.error(f"Error saving to cache: {str(e)}")

    def load_from_cache(self, handle: str, date: datetime) -> Optional[List[dict]]:
        if settings.CACHE_TWEETS:
            cache_path = self.get_cache_path(handle, date)
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, 'r') as f:
                        tweets = json.load(f)
                        logger.debug(f"Loaded {len(tweets)} tweets from cache: {cache_path}")
                        return tweets
                except Exception as e:
                    logger.error(f"Error loading from cache: {str(e)}")
        return None