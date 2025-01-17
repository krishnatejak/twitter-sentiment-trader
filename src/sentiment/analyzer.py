from transformers import pipeline
from typing import Dict
from ..models.tweet import Tweet
from ..config.settings import settings

class SentimentAnalyzer:
    def __init__(self):
        self.sentiment_pipeline = pipeline(
            'sentiment-analysis',
            model='finiteautomata/bertweet-base-sentiment-analysis'
        )

    def analyze(self, tweet: Tweet) -> str:
        """Analyze tweet sentiment and return category"""
        result = self.sentiment_pipeline(tweet.text)[0]
        score = result['score']

        if score >= settings.SENTIMENT_THRESHOLDS['SUPER_POSITIVE']:
            return 'SUPER_POSITIVE'
        elif score >= settings.SENTIMENT_THRESHOLDS['POSITIVE']:
            return 'POSITIVE'
        elif score <= settings.SENTIMENT_THRESHOLDS['SUPER_NEGATIVE']:
            return 'SUPER_NEGATIVE'
        elif score <= settings.SENTIMENT_THRESHOLDS['NEGATIVE']:
            return 'NEGATIVE'
        else:
            return 'NEUTRAL'