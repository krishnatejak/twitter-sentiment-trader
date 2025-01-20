import os
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigValidator:
    @staticmethod
    def validate_twitter_credentials() -> Dict[str, str]:
        """Validate and return Twitter credentials"""
        logger.debug("Validating Twitter credentials")
        
        # Load environment variables
        load_dotenv()
        
        # Required credentials
        required_creds = [
            'TWITTER_API_KEY',
            'TWITTER_API_SECRET',
            'TWITTER_ACCESS_TOKEN',
            'TWITTER_ACCESS_TOKEN_SECRET'
        ]
        
        # Check each credential
        creds = {}
        missing_creds = []
        for cred in required_creds:
            value = os.getenv(cred)
            if not value:
                missing_creds.append(cred)
            creds[cred.lower()] = value
            
        if missing_creds:
            logger.error(f"Missing Twitter credentials: {missing_creds}")
            raise ValueError(f"Missing required Twitter credentials: {missing_creds}")
            
        logger.info("Twitter credentials validation successful")
        return creds

    @staticmethod
    def validate_zerodha_credentials() -> Dict[str, str]:
        """Validate and return Zerodha credentials"""
        logger.debug("Validating Zerodha credentials")
        
        # Required credentials
        required_creds = [
            'KITE_API_KEY',
            'KITE_API_SECRET'
        ]
        
        # Check each credential
        creds = {}
        missing_creds = []
        for cred in required_creds:
            value = os.getenv(cred)
            if not value:
                missing_creds.append(cred)
            creds[cred.lower()] = value
            
        if missing_creds:
            logger.error(f"Missing Zerodha credentials: {missing_creds}")
            raise ValueError(f"Missing required Zerodha credentials: {missing_creds}")
            
        logger.info("Zerodha credentials validation successful")
        return creds

    @staticmethod
    def test_connections() -> Dict[str, bool]:
        """Test all API connections"""
        logger.info("Testing API connections")
        results = {}
        
        try:
            twitter_creds = ConfigValidator.validate_twitter_credentials()
            # Test Twitter connection
            from ..twitter.stream import TwitterStream
            twitter = TwitterStream(
                api_key=twitter_creds['twitter_api_key'],
                api_secret=twitter_creds['twitter_api_secret'],
                access_token=twitter_creds['twitter_access_token'],
                access_token_secret=twitter_creds['twitter_access_token_secret']
            )
            # Test by getting a user
            twitter.client.get_user(username="twitter")
            results['twitter'] = True
            logger.info("Twitter connection test successful")
        except Exception as e:
            logger.error(f"Twitter connection test failed: {str(e)}")
            results['twitter'] = False
            
        try:
            zerodha_creds = ConfigValidator.validate_zerodha_credentials()
            # Test Zerodha connection
            from ..trading.historical_data import HistoricalDataFetcher
            zerodha = HistoricalDataFetcher(
                api_key=zerodha_creds['kite_api_key'],
                api_secret=zerodha_creds['kite_api_secret']
            )
            # Test by getting instruments
            zerodha.get_instrument_token("RELIANCE")
            results['zerodha'] = True
            logger.info("Zerodha connection test successful")
        except Exception as e:
            logger.error(f"Zerodha connection test failed: {str(e)}")
            results['zerodha'] = False
            
        return results

    @staticmethod
    def validate_all():
        """Validate all configurations and test connections"""
        logger.info("Starting complete configuration validation")
        
        try:
            # Validate credentials
            twitter_creds = ConfigValidator.validate_twitter_credentials()
            zerodha_creds = ConfigValidator.validate_zerodha_credentials()
            
            # Test connections
            connection_results = ConfigValidator.test_connections()
            
            if not all(connection_results.values()):
                failed_connections = [k for k, v in connection_results.items() if not v]
                raise ValueError(f"Connection tests failed for: {failed_connections}")
                
            logger.info("All validations passed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            raise