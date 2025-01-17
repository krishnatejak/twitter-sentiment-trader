from kiteconnect import KiteConnect
from typing import Dict
from ..models.trade import Trade
from ..config.settings import settings

class Trader:
    def __init__(self, api_key: str, api_secret: str):
        self.kite = KiteConnect(api_key=api_key)
        self.positions: Dict[str, Trade] = {}
        self._api_secret = api_secret

    def login(self, request_token: str):
        """Complete Kite login process"""
        data = self.kite.generate_session(request_token, api_secret=self._api_secret)
        self.kite.set_access_token(data['access_token'])

    def place_trade(self, symbol: str, quantity: int, trade_type: str):
        """Place a trade on Zerodha"""
        try:
            order_id = self.kite.place_order(
                tradingsymbol=symbol,
                exchange='NSE',
                transaction_type=trade_type,
                quantity=quantity,
                order_type='MARKET',
                product='MIS'
            )
            return order_id
        except Exception as e:
            print(f'Error placing trade: {str(e)}')
            return None

    def get_ltp(self, symbol: str) -> float:
        """Get Last Traded Price for a symbol"""
        try:
            quote = self.kite.quote(f'NSE:{symbol}')
            return quote[f'NSE:{symbol}']['last_price']
        except Exception as e:
            print(f'Error getting LTP: {str(e)}')
            return None