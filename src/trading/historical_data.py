from typing import Optional, Dict, List
from datetime import datetime, timedelta
import pandas as pd
from kiteconnect import KiteConnect
import pytz

class HistoricalDataFetcher:
    def __init__(self, api_key: str, api_secret: str):
        self.kite = KiteConnect(api_key=api_key)
        self._api_secret = api_secret
        self.ist_tz = pytz.timezone('Asia/Kolkata')
        self.cache: Dict[str, pd.DataFrame] = {}

    def login(self, request_token: str):
        """Complete Kite login process"""
        data = self.kite.generate_session(request_token, api_secret=self._api_secret)
        self.kite.set_access_token(data['access_token'])

    def get_instrument_token(self, symbol: str) -> Optional[int]:
        """Get instrument token for a symbol"""
        try:
            instruments = self.kite.instruments("NSE")
            for instrument in instruments:
                if instrument['tradingsymbol'] == symbol:
                    return instrument['instrument_token']
            return None
        except Exception as e:
            print(f"Error getting instrument token: {str(e)}")
            return None

    def get_historical_data(
        self,
        symbol: str,
        from_date: datetime,
        to_date: datetime,
        interval: str = "minute"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'RELIANCE')
            from_date: Start date
            to_date: End date
            interval: Data interval ('minute', 'day', '3minute', '5minute', '10minute', 
                     '15minute', '30minute', '60minute')
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_{from_date.date()}_{to_date.date()}_{interval}"
            if cache_key in self.cache:
                return self.cache[cache_key]

            # Get instrument token
            token = self.get_instrument_token(symbol)
            if not token:
                print(f"Could not find instrument token for {symbol}")
                return None

            # Convert dates to IST
            from_date_ist = self.ist_tz.localize(from_date)
            to_date_ist = self.ist_tz.localize(to_date)

            # Fetch historical data
            data = self.kite.historical_data(
                token,
                from_date_ist,
                to_date_ist,
                interval,
                continuous=False
            )

            if not data:
                return None

            # Convert to DataFrame
            df = pd.DataFrame(data)
            df.set_index('date', inplace=True)

            # Cache the data
            self.cache[cache_key] = df

            return df

        except Exception as e:
            print(f"Error fetching historical data: {str(e)}")
            return None

    def get_historical_market_data(
        self,
        symbol: str,
        from_date: datetime,
        to_date: datetime,
        interval: str = "minute"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for market hours only
        
        This function filters data to include only market hours and
        handles data fetching in chunks to avoid API limits
        """
        try:
            all_data = []
            current_date = from_date

            while current_date <= to_date:
                next_date = current_date + timedelta(days=1)
                
                # Get data for current day
                day_data = self.get_historical_data(
                    symbol,
                    current_date,
                    next_date,
                    interval
                )

                if day_data is not None:
                    # Filter for market hours (9:15 AM to 3:30 PM IST)
                    market_data = day_data.between_time('09:15', '15:30')
                    all_data.append(market_data)

                current_date = next_date

            if not all_data:
                return None

            # Combine all data
            return pd.concat(all_data)

        except Exception as e:
            print(f"Error fetching market data: {str(e)}")
            return None

    def get_opening_closing_data(
        self,
        symbol: str,
        date: datetime,
        window_minutes: int = 30
    ) -> Dict[str, pd.DataFrame]:
        """
        Get data around market opening and closing times
        
        Args:
            symbol: Trading symbol
            date: Date to fetch data for
            window_minutes: Minutes before and after market open/close
            
        Returns:
            Dictionary with 'opening' and 'closing' DataFrames
        """
        try:
            # Get full day data
            day_data = self.get_historical_data(
                symbol,
                date,
                date + timedelta(days=1),
                interval="minute"
            )

            if day_data is None:
                return {'opening': pd.DataFrame(), 'closing': pd.DataFrame()}

            # Filter for opening window (9:15 AM ± window_minutes)
            opening_start = pd.Timestamp('09:15', tz=self.ist_tz).time()
            opening_data = day_data.between_time(
                (pd.Timestamp('09:15', tz=self.ist_tz) - pd.Timedelta(minutes=window_minutes)).time(),
                (pd.Timestamp('09:15', tz=self.ist_tz) + pd.Timedelta(minutes=window_minutes)).time()
            )

            # Filter for closing window (3:30 PM ± window_minutes)
            closing_start = pd.Timestamp('15:30', tz=self.ist_tz).time()
            closing_data = day_data.between_time(
                (pd.Timestamp('15:30', tz=self.ist_tz) - pd.Timedelta(minutes=window_minutes)).time(),
                (pd.Timestamp('15:30', tz=self.ist_tz) + pd.Timedelta(minutes=window_minutes)).time()
            )

            return {
                'opening': opening_data,
                'closing': closing_data
            }

        except Exception as e:
            print(f"Error fetching opening/closing data: {str(e)}")
            return {'opening': pd.DataFrame(), 'closing': pd.DataFrame()}