"""
Price Data Module for Trading Dashboard
Fetches historical price data for chart creation with trade markers
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Tuple
import json

class PriceDataManager:
    """Manages price data fetching and caching for multiple timeframes"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    def get_binance_klines(self, symbol: str, interval: str, limit: int = 500) -> Optional[pd.DataFrame]:
        """
        Fetch price data from Binance API
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Timeframe ('1h', '4h', '1d')
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"{symbol}_{interval}_{limit}"
        current_time = time.time()
        
        # Check cache
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if current_time - cache_time < self.cache_duration:
                return data
        
        try:
            # Convert symbol format (BTC/USDT -> BTCUSDT)
            binance_symbol = symbol.replace('/', '')
            
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': binance_symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                'taker_buy_quote_volume', 'ignore'
            ])
            
            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            df['quote_volume'] = df['quote_volume'].astype(float)
            
            # Cache the result
            self.cache[cache_key] = (current_time, df)
            
            return df
            
        except Exception as e:
            print(f"Error fetching price data for {symbol}: {e}")
            return None
    
    def get_price_at_time(self, symbol: str, timestamp: str, interval: str = '1h') -> Optional[float]:
        """
        Get price at specific timestamp for trade markers
        
        Args:
            symbol: Trading pair
            timestamp: ISO timestamp string
            interval: Timeframe to search
            
        Returns:
            Price at that time or None
        """
        try:
            target_time = pd.to_datetime(timestamp)
            df = self.get_binance_klines(symbol, interval, 100)
            
            if df is None or len(df) == 0:
                return None
            
            # Find closest candle to target time
            df['time_diff'] = abs(df['timestamp'] - target_time)
            closest_idx = df['time_diff'].idxmin()
            
            return df.loc[closest_idx, 'close']
            
        except Exception as e:
            print(f"Error getting price at time for {symbol}: {e}")
            return None
    
    def get_multiple_symbols_data(self, symbols: List[str], interval: str = '1h') -> Dict[str, pd.DataFrame]:
        """
        Get price data for multiple symbols
        
        Args:
            symbols: List of trading pairs
            interval: Timeframe
            
        Returns:
            Dictionary of symbol -> DataFrame
        """
        results = {}
        
        for symbol in symbols:
            df = self.get_binance_klines(symbol, interval)
            if df is not None:
                results[symbol] = df
            time.sleep(0.1)  # Rate limiting
        
        return results
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for chart display
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            DataFrame with added technical indicators
        """
        if df is None or len(df) < 20:
            return df
        
        try:
            # Simple Moving Averages
            df['SMA_20'] = df['close'].rolling(window=20).mean()
            df['SMA_50'] = df['close'].rolling(window=50).mean()
            
            # Exponential Moving Averages
            df['EMA_12'] = df['close'].ewm(span=12).mean()
            df['EMA_26'] = df['close'].ewm(span=26).mean()
            
            # MACD
            df['MACD'] = df['EMA_12'] - df['EMA_26']
            df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['BB_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
            df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
            
            # Volume indicators
            df['Volume_SMA'] = df['volume'].rolling(window=20).mean()
            df['Volume_ratio'] = df['volume'] / df['Volume_SMA']
            
            # Support and Resistance levels (simplified)
            # Find local highs and lows
            df['local_high'] = df['high'][(df['high'].shift(1) < df['high']) & (df['high'].shift(-1) < df['high'])]
            df['local_low'] = df['low'][(df['low'].shift(1) > df['low']) & (df['low'].shift(-1) > df['low'])]
            
            return df
            
        except Exception as e:
            print(f"Error calculating technical indicators: {e}")
            return df

# Global price data manager instance
price_manager = PriceDataManager()

def get_trade_symbols_from_jsonl() -> List[str]:
    """
    Extract unique symbols from trade history for chart generation
    """
    symbols = set()
    
    try:
        with open('/Users/kolade/clawd/trading-bot/data/trades.jsonl', 'r') as f:
            for line in f:
                if line.strip():
                    trade = json.loads(line)
                    symbols.add(trade.get('symbol', ''))
    except:
        pass
    
    # Remove empty strings and return sorted list
    return sorted([s for s in symbols if s])

def get_trades_for_symbol(symbol: str) -> List[Dict]:
    """
    Get all trades for a specific symbol
    """
    trades = []
    
    try:
        with open('/Users/kolade/clawd/trading-bot/data/trades.jsonl', 'r') as f:
            for line in f:
                if line.strip():
                    trade = json.loads(line)
                    if trade.get('symbol') == symbol:
                        trades.append(trade)
    except:
        pass
    
    return sorted(trades, key=lambda x: x.get('entry_time', ''))

def calculate_price_levels(df: pd.DataFrame, lookback: int = 20) -> Dict[str, List[float]]:
    """
    Calculate support and resistance levels from price data
    
    Args:
        df: OHLCV DataFrame
        lookback: Number of periods to look back for levels
        
    Returns:
        Dict with support and resistance levels
    """
    if df is None or len(df) < lookback:
        return {'support': [], 'resistance': []}
    
    try:
        # Find pivot points
        highs = df['high'].rolling(window=lookback, center=True).max() == df['high']
        lows = df['low'].rolling(window=lookback, center=True).min() == df['low']
        
        # Get resistance levels (pivot highs)
        resistance_levels = df[highs]['high'].tolist()
        
        # Get support levels (pivot lows)  
        support_levels = df[lows]['low'].tolist()
        
        # Remove duplicates and sort
        resistance_levels = sorted(list(set(resistance_levels)), reverse=True)
        support_levels = sorted(list(set(support_levels)))
        
        # Keep only the most significant levels (top 3-5)
        return {
            'resistance': resistance_levels[:5],
            'support': support_levels[-5:]
        }
        
    except Exception as e:
        print(f"Error calculating price levels: {e}")
        return {'support': [], 'resistance': []}