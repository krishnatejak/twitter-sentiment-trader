from typing import Dict, List
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Twitter Configuration
    TWITTER_HANDLES: List[str] = [  ]
    TWEET_FETCH_INTERVAL: int = 60  # seconds

    # Market Hours (Indian Standard Time)
    MARKET_OPEN_TIME: time = time(9, 15)  # 9:15 AM IST
    MARKET_CLOSE_TIME: time = time(15, 30)  # 3:30 PM IST
    MARKET_OPENING_WINDOW: int = 30  # minutes to monitor around market opening
    MARKET_CLOSING_WINDOW: int = 0  # minutes to monitor around market closing

    # Sentiment Analysis
    SENTIMENT_THRESHOLDS: Dict[str, float] = {
        'SUPER_POSITIVE': 0.8,
        'POSITIVE': 0.6,
        'NEGATIVE': 0.4,
        'SUPER_NEGATIVE': 0.2
    }

    # Trading Configuration
    TRADE_AMOUNT: float = 10000.0  # Amount per trade in INR
    MAX_POSITIONS: int = 5  # Maximum number of concurrent positions
    STOP_LOSS_PERCENTAGE: float = 2.0
    TARGET_PERCENTAGE: float = 4.0

    # Backtesting Configuration
    BACKTEST_START_DATE: str = '2024-01-01'
    BACKTEST_END_DATE: str = '2024-12-31'
    TWEETS_PER_DAY_LIMIT: int = 100  # Limit API calls during backtesting
    CACHE_TWEETS: bool = True  # Cache tweets for reuse in backtesting

    class Config:
        env_file = '.env'

settings = Settings()