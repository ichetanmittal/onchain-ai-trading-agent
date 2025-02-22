from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator
import torch
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Advanced feature engineering for crypto trading"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize feature engineer
        
        Args:
            config: Optional dictionary containing feature parameters
        """
        self.config = config or {}
        self.scalers = {}
        
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical analysis indicators"""
        try:
            # Trend Indicators
            df['sma_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
            df['sma_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
            df['ema_12'] = EMAIndicator(close=df['close'], window=12).ema_indicator()
            df['ema_26'] = EMAIndicator(close=df['close'], window=26).ema_indicator()
            
            # MACD
            macd = MACD(close=df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
            
            # Momentum Indicators
            df['rsi'] = RSIIndicator(close=df['close']).rsi()
            
            stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'])
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            # Volatility Indicators
            bb = BollingerBands(close=df['close'])
            df['bb_high'] = bb.bollinger_hband()
            df['bb_low'] = bb.bollinger_lband()
            df['bb_mid'] = bb.bollinger_mavg()
            
            df['atr'] = AverageTrueRange(
                high=df['high'],
                low=df['low'],
                close=df['close']
            ).average_true_range()
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {str(e)}")
            raise
            
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features"""
        try:
            # Price changes
            df['price_change'] = df['close'].pct_change()
            df['price_change_1h'] = df['close'].pct_change(periods=1)
            df['price_change_4h'] = df['close'].pct_change(periods=4)
            df['price_change_24h'] = df['close'].pct_change(periods=24)
            
            # Price ratios
            df['high_low_ratio'] = df['high'] / df['low']
            df['close_open_ratio'] = df['close'] / df['open']
            
            # Price volatility
            df['volatility_1h'] = df['price_change_1h'].rolling(window=1).std()
            df['volatility_4h'] = df['price_change_4h'].rolling(window=4).std()
            df['volatility_24h'] = df['price_change_24h'].rolling(window=24).std()
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding price features: {str(e)}")
            raise
            
    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based features"""
        try:
            # Volume changes
            df['volume_change'] = df['volume'].pct_change()
            df['volume_ma_20'] = df['volume'].rolling(window=20).mean()
            df['volume_ma_50'] = df['volume'].rolling(window=50).mean()
            
            # Volume indicators
            df['obv'] = OnBalanceVolumeIndicator(
                close=df['close'],
                volume=df['volume']
            ).on_balance_volume()
            
            # Volume ratios
            df['volume_price_ratio'] = df['volume'] / df['close']
            df['volume_volatility'] = df['volume'].rolling(window=24).std()
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding volume features: {str(e)}")
            raise
            
    def _add_market_microstructure_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add market microstructure features"""
        try:
            if 'bid_ask_spread' in df.columns:
                # Spread features
                df['spread_pct'] = df['bid_ask_spread'] / df['close']
                df['spread_ma'] = df['bid_ask_spread'].rolling(window=20).mean()
                df['spread_std'] = df['bid_ask_spread'].rolling(window=20).std()
                
            if 'order_book_depth' in df.columns:
                # Order book features
                df['depth_ma'] = df['order_book_depth'].rolling(window=20).mean()
                df['depth_std'] = df['order_book_depth'].rolling(window=20).std()
                
            return df
            
        except Exception as e:
            logger.error(f"Error adding market microstructure features: {str(e)}")
            raise
            
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in features"""
        try:
            # Forward fill missing values
            df = df.fillna(method='ffill')
            
            # If any missing values remain, fill with 0
            df = df.fillna(0)
            
            return df
            
        except Exception as e:
            logger.error(f"Error handling missing values: {str(e)}")
            raise
            
    def _scale_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Scale features using StandardScaler"""
        try:
            # Initialize scalers for each symbol if not exists
            for symbol in df['symbol'].unique():
                if symbol not in self.scalers:
                    self.scalers[symbol] = StandardScaler()
                    
            # Scale features for each symbol separately
            scaled_dfs = []
            for symbol in df['symbol'].unique():
                symbol_df = df[df['symbol'] == symbol].copy()
                
                # Get numeric columns
                numeric_cols = symbol_df.select_dtypes(include=[np.number]).columns
                
                # Scale numeric features
                if len(symbol_df) > 0:
                    symbol_df[numeric_cols] = self.scalers[symbol].fit_transform(symbol_df[numeric_cols])
                    
                scaled_dfs.append(symbol_df)
                
            # Combine scaled DataFrames
            return pd.concat(scaled_dfs)
            
        except Exception as e:
            logger.error(f"Error scaling features: {str(e)}")
            raise
            
    def prepare_features(self, data_dict: Dict[str, pd.DataFrame]) -> torch.Tensor:
        """
        Prepare features from all data sources
        
        Args:
            data_dict: Dictionary containing different types of data
            
        Returns:
            torch.Tensor: Prepared feature tensor
        """
        try:
            # Start with market data
            df = data_dict['market_data'].copy()
            
            # Add technical indicators
            df = self._add_technical_indicators(df)
            
            # Add price-based features
            df = self._add_price_features(df)
            
            # Add volume-based features
            df = self._add_volume_features(df)
            
            # Add market microstructure features
            df = self._add_market_microstructure_features(df)
            
            # Handle missing values
            df = self._handle_missing_values(df)
            
            # Scale features
            df = self._scale_features(df)
            
            # Convert to tensor
            features = torch.tensor(df.drop(['timestamp', 'symbol'], axis=1).values, dtype=torch.float32)
            
            return features
            
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            raise
            
    def inverse_transform_predictions(self, predictions: torch.Tensor, symbol: str) -> np.ndarray:
        """Transform predictions back to original scale"""
        if symbol in self.scalers:
            return self.scalers[symbol].inverse_transform(predictions.cpu().numpy())
        return predictions.cpu().numpy()
