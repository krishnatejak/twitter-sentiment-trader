from typing import Dict, List
from datetime import time
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Twitter API Credentials
    TWITTER_API_KEY: str = Field(default="")
    TWITTER_API_SECRET: str = Field(default="")
    TWITTER_ACCESS_TOKEN: str = Field(default="")
    TWITTER_ACCESS_TOKEN_SECRET: str = Field(default="")

    # Zerodha Credentials
    KITE_API_KEY: str = Field(default="")
    KITE_API_SECRET: str = Field(default="")

    # Database Configuration
    DATABASE_URL: str = Field(default="postgresql://user:password@localhost/dbname")

    # Twitter Configuration
    TWITTER_HANDLES: List[str] = Field(default=[])
    TWEET_FETCH_INTERVAL: int = Field(default=60)  # seconds

    # Market Hours (Indian Standard Time)
    MARKET_OPEN_TIME: time = Field(default=time(9, 15))  # 9:15 AM IST
    MARKET_CLOSE_TIME: time = Field(default=time(15, 30))  # 3:30 PM IST
    MARKET_OPENING_WINDOW: int = Field(default=30)  # minutes to monitor around market opening
    MARKET_CLOSING_WINDOW: int = Field(default=30)  # minutes to monitor around market closing

    # Sentiment Analysis
    SENTIMENT_THRESHOLDS: Dict[str, float] = Field(default={
        'SUPER_POSITIVE': 0.8,
        'POSITIVE': 0.6,
        'NEGATIVE': 0.4,
        'SUPER_NEGATIVE': 0.2
    })

    # Trading Configuration
    TRADE_AMOUNT: float = Field(default=10000.0)  # Amount per trade in INR
    MAX_POSITIONS: int = Field(default=5)  # Maximum number of concurrent positions
    STOP_LOSS_PERCENTAGE: float = Field(default=2.0)
    TARGET_PERCENTAGE: float = Field(default=4.0)

    # Backtesting Configuration
    BACKTEST_START_DATE: str = Field(default='2024-01-01')
    BACKTEST_END_DATE: str = Field(default='2024-12-31')
    TWEETS_PER_DAY_LIMIT: int = Field(default=100)  # Limit API calls during backtesting
    CACHE_TWEETS: bool = Field(default=True)  # Cache tweets for reuse in backtesting

    class Config:
        env_file = '.env'
        case_sensitive = False
        extra = 'ignore'  # This will ignore extra fields in the environment

settings = Settings()