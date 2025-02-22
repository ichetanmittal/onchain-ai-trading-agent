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
        
    def _handle_nan_values(self, df: pd.DataFrame, method: str = 'ffill') -> pd.DataFrame:
        """
        Handle NaN values in the DataFrame
        
        Args:
            df: Input DataFrame
            method: Method to handle NaN values ('ffill', 'bfill', or 'both')
            
        Returns:
            DataFrame with NaN values handled
        """
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Log NaN status before cleaning
        nan_cols = df.isna().sum()
        if nan_cols.any():
            logger.debug("NaN values before cleaning:")
            for col in nan_cols[nan_cols > 0].index:
                logger.debug(f"{col}: {nan_cols[col]}")
        
        if method == 'ffill' or method == 'both':
            df = df.ffill()
        if method == 'bfill' or method == 'both':
            df = df.bfill()
            
        # For any remaining NaNs (e.g., at the start of the series), fill with zeros
        if df.isna().any().any():
            df = df.fillna(0)
            
        return df
        
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical analysis indicators"""
        try:
            # Process each symbol separately
            all_data = []
            for symbol in df['symbol'].unique():
                symbol_data = df[df['symbol'] == symbol].copy()
                symbol_data = symbol_data.sort_values('timestamp')  # Ensure data is sorted
                
                # Store non-feature columns
                timestamp = symbol_data['timestamp']
                symbol_col = symbol_data['symbol']
                
                # Convert price/volume columns to numeric, replacing any invalid values with NaN
                numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_cols:
                    symbol_data[col] = pd.to_numeric(symbol_data[col], errors='coerce')
                
                # Handle any NaN values in input data
                symbol_data = self._handle_nan_values(symbol_data, method='both')
                
                # Calculate indicators
                # Trend
                symbol_data['sma_20'] = SMAIndicator(close=symbol_data['close'], window=20).sma_indicator()
                symbol_data['sma_50'] = SMAIndicator(close=symbol_data['close'], window=50).sma_indicator()
                symbol_data['ema_12'] = EMAIndicator(close=symbol_data['close'], window=12).ema_indicator()
                symbol_data['ema_26'] = EMAIndicator(close=symbol_data['close'], window=26).ema_indicator()
                
                # MACD
                macd = MACD(close=symbol_data['close'])
                symbol_data['macd'] = macd.macd()
                symbol_data['macd_signal'] = macd.macd_signal()
                symbol_data['macd_diff'] = macd.macd_diff()
                
                # Momentum
                symbol_data['rsi'] = RSIIndicator(close=symbol_data['close']).rsi()
                
                stoch = StochasticOscillator(
                    high=symbol_data['high'],
                    low=symbol_data['low'],
                    close=symbol_data['close']
                )
                symbol_data['stoch_k'] = stoch.stoch()
                symbol_data['stoch_d'] = stoch.stoch_signal()
                
                # Volatility
                bb = BollingerBands(close=symbol_data['close'])
                symbol_data['bb_high'] = bb.bollinger_hband()
                symbol_data['bb_low'] = bb.bollinger_lband()
                symbol_data['bb_mid'] = bb.bollinger_mavg()
                
                symbol_data['atr'] = AverageTrueRange(
                    high=symbol_data['high'],
                    low=symbol_data['low'],
                    close=symbol_data['close']
                ).average_true_range()
                
                # Handle NaN values created by indicators
                symbol_data = self._handle_nan_values(symbol_data, method='both')
                
                # Restore non-feature columns
                symbol_data['timestamp'] = timestamp
                symbol_data['symbol'] = symbol_col
                
                all_data.append(symbol_data)
            
            result = pd.concat(all_data)
            logger.info(f"Technical indicators shape: {result.shape}")
            return result
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {str(e)}")
            raise
            
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features"""
        try:
            # Process each symbol separately
            all_data = []
            for symbol in df['symbol'].unique():
                symbol_data = df[df['symbol'] == symbol].copy()
                symbol_data = symbol_data.sort_values('timestamp')
                
                # Store non-feature columns
                timestamp = symbol_data['timestamp']
                symbol_col = symbol_data['symbol']
                
                # Price changes
                symbol_data['price_change'] = symbol_data['close'].pct_change()
                symbol_data['price_change_1h'] = symbol_data['close'].pct_change(periods=1)
                symbol_data['price_change_4h'] = symbol_data['close'].pct_change(periods=4)
                symbol_data['price_change_24h'] = symbol_data['close'].pct_change(periods=24)
                
                # Price ratios
                symbol_data['high_low_ratio'] = symbol_data['high'] / symbol_data['low']
                symbol_data['close_open_ratio'] = symbol_data['close'] / symbol_data['open']
                
                # Price volatility
                symbol_data['volatility_1h'] = symbol_data['price_change_1h'].rolling(window=1).std()
                symbol_data['volatility_4h'] = symbol_data['price_change_4h'].rolling(window=4).std()
                symbol_data['volatility_24h'] = symbol_data['price_change_24h'].rolling(window=24).std()
                
                # Handle NaN values
                symbol_data = self._handle_nan_values(symbol_data, method='both')
                
                # Restore non-feature columns
                symbol_data['timestamp'] = timestamp
                symbol_data['symbol'] = symbol_col
                
                all_data.append(symbol_data)
            
            result = pd.concat(all_data)
            logger.info(f"Price features shape: {result.shape}")
            return result
            
        except Exception as e:
            logger.error(f"Error adding price features: {str(e)}")
            raise
            
    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based features"""
        try:
            # Process each symbol separately
            all_data = []
            for symbol in df['symbol'].unique():
                symbol_data = df[df['symbol'] == symbol].copy()
                symbol_data = symbol_data.sort_values('timestamp')
                
                # Store non-feature columns
                timestamp = symbol_data['timestamp']
                symbol_col = symbol_data['symbol']
                
                # Volume changes
                symbol_data['volume_change'] = symbol_data['volume'].pct_change()
                symbol_data['volume_ma_20'] = symbol_data['volume'].rolling(window=20).mean()
                symbol_data['volume_ma_50'] = symbol_data['volume'].rolling(window=50).mean()
                
                # Volume indicators
                symbol_data['obv'] = OnBalanceVolumeIndicator(
                    close=symbol_data['close'],
                    volume=symbol_data['volume']
                ).on_balance_volume()
                
                # Volume ratios
                symbol_data['volume_price_ratio'] = symbol_data['volume'] / symbol_data['close']
                symbol_data['volume_volatility'] = symbol_data['volume'].rolling(window=20).std()
                
                # Handle NaN values
                symbol_data = self._handle_nan_values(symbol_data, method='both')
                
                # Restore non-feature columns
                symbol_data['timestamp'] = timestamp
                symbol_data['symbol'] = symbol_col
                
                all_data.append(symbol_data)
            
            result = pd.concat(all_data)
            logger.info(f"Volume features shape: {result.shape}")
            return result
            
        except Exception as e:
            logger.error(f"Error adding volume features: {str(e)}")
            raise
            
    def create_features(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Create features from market data
        
        Args:
            data: Dictionary containing market data DataFrame
            
        Returns:
            DataFrame with engineered features
        """
        try:
            df = data['market_data'].copy()
            logger.info(f"Input data shape: {df.shape}")
            logger.info(f"Input symbols: {df['symbol'].unique().tolist()}")
            
            # Sort by timestamp to ensure correct feature calculation
            df = df.sort_values(['symbol', 'timestamp'])
            
            # Add technical indicators
            df = self._add_technical_indicators(df)
            logger.info(f"After technical indicators shape: {df.shape}")
            
            # Add price features
            df = self._add_price_features(df)
            logger.info(f"After price features shape: {df.shape}")
            
            # Add volume features
            df = self._add_volume_features(df)
            logger.info(f"After volume features shape: {df.shape}")
            
            # Handle any remaining NaN values
            nan_count_before = df.isna().sum().sum()
            if nan_count_before > 0:
                logger.warning(f"Found {nan_count_before} NaN values before final cleaning")
                df = self._handle_nan_values(df, method='both')
                nan_count_after = df.isna().sum().sum()
                if nan_count_after > 0:
                    logger.warning(f"Still have {nan_count_after} NaN values after cleaning")
                    # Only drop rows if we really have to
                    df = df.dropna()
                logger.info(f"After final cleaning shape: {df.shape}")
            
            # Scale features
            feature_columns = df.columns.difference(['symbol', 'timestamp'])
            for symbol in df['symbol'].unique():
                symbol_mask = df['symbol'] == symbol
                
                if symbol not in self.scalers:
                    self.scalers[symbol] = StandardScaler()
                    df.loc[symbol_mask, feature_columns] = self.scalers[symbol].fit_transform(
                        df.loc[symbol_mask, feature_columns]
                    )
                else:
                    df.loc[symbol_mask, feature_columns] = self.scalers[symbol].transform(
                        df.loc[symbol_mask, feature_columns]
                    )
            
            logger.info(f"Created {len(feature_columns)} features")
            logger.info(f"Final output shape: {df.shape}")
            logger.info(f"Output symbols: {df['symbol'].unique().tolist()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error creating features: {str(e)}")
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
            # Create features
            df = self.create_features(data_dict)
            
            # Convert to tensor
            features = torch.tensor(df.values, dtype=torch.float32)
            
            return features
            
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            raise
            
    def inverse_transform_predictions(self, predictions: torch.Tensor, symbol: str) -> np.ndarray:
        """Transform predictions back to original scale"""
        if symbol in self.scalers:
            return self.scalers[symbol].inverse_transform(predictions.cpu().numpy())
        return predictions.cpu().numpy()
