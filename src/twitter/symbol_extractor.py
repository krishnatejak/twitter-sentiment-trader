import re
from typing import List, Set
import pandas as pd
from ..trading.historical_data import HistoricalDataFetcher

class SymbolExtractor:
    def __init__(self, historical_data: HistoricalDataFetcher):
        self.historical_data = historical_data
        self._nse_symbols = self._load_nse_symbols()
        self._symbol_patterns = self._compile_patterns()

    def _load_nse_symbols(self) -> Set[str]:
        """Load all NSE symbols from Zerodha"""
        try:
            instruments = self.historical_data.kite.instruments("NSE")
            return {instrument['tradingsymbol'] for instrument in instruments}
        except Exception as e:
            print(f"Error loading NSE symbols: {str(e)}")
            return set()

    def _compile_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for symbol extraction"""
        patterns = [
            # Match $SYMBOL format
            re.compile(r'\$([A-Z0-9]+)'),
            # Match NSE:SYMBOL format
            re.compile(r'NSE:([A-Z0-9]+)'),
            # Match common Indian stock variations
            re.compile(r'(?:^|\s)([A-Z0-9]+)-?(?:EQ|NSE|BSE)(?:\s|$)'),
            # Match standalone uppercase words that match NSE symbols
            re.compile(r'(?:^|\s)([A-Z0-9]{2,})(?:\s|$)')
        ]
        return patterns

    def extract_symbols(self, text: str) -> List[str]:
        """
        Extract potential stock symbols from tweet text
        Returns list of valid NSE symbols
        """
        potential_symbols = set()
        
        # Extract using all patterns
        for pattern in self._symbol_patterns:
            matches = pattern.findall(text)
            potential_symbols.update(matches)
        
        # Filter to only valid NSE symbols
        valid_symbols = [
            symbol for symbol in potential_symbols 
            if symbol in self._nse_symbols
        ]
        
        return valid_symbols

    def _clean_text(self, text: str) -> str:
        """Clean text for better symbol extraction"""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove mentions
        text = re.sub(r'@\w+', '', text)
        # Remove hashtags
        text = re.sub(r'#\w+', '', text)
        # Remove punctuation except $ and :
        text = re.sub(r'[^\w\s$:]', ' ', text)
        return text.strip()

    def analyze_symbols(self, text: str) -> List[dict]:
        """
        Analyze text and return detailed information about extracted symbols
        Returns list of dicts with symbol and confidence score
        """
        cleaned_text = self._clean_text(text)
        symbols = self.extract_symbols(cleaned_text)
        
        results = []
        for symbol in symbols:
            confidence = self._calculate_confidence(symbol, cleaned_text)
            results.append({
                'symbol': symbol,
                'confidence': confidence
            })
        
        # Sort by confidence
        return sorted(results, key=lambda x: x['confidence'], reverse=True)

    def _calculate_confidence(self, symbol: str, text: str) -> float:
        """Calculate confidence score for symbol extraction"""
        confidence = 0.0
        
        # Check for exact cashtag match ($SYMBOL)
        if f'${symbol}' in text:
            confidence += 0.4
        
        # Check for NSE:SYMBOL format
        if f'NSE:{symbol}' in text:
            confidence += 0.4
            
        # Check for symbol with -EQ suffix
        if f'{symbol}-EQ' in text:
            confidence += 0.3
            
        # Check for standalone symbol
        if re.search(f'(?:^|\s){symbol}(?:\s|$)', text):
            confidence += 0.2
            
        # Additional context-based scoring
        if 'buy' in text.lower() or 'sell' in text.lower():
            confidence += 0.1
            
        if 'target' in text.lower() or 'stop' in text.lower():
            confidence += 0.1
            
        return min(confidence, 1.0)  # Cap at 1.0