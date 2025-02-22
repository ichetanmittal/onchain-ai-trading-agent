from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
import pandas as pd
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseDataCollector(ABC):
    """Base class for all data collectors"""
    
    def __init__(self, symbols: Optional[List[str]] = None):
        """
        Initialize the data collector
        
        Args:
            symbols: Optional list of trading pairs/symbols to collect data for
        """
        self.symbols = symbols or []
        
    @abstractmethod
    async def fetch_market_data(self) -> pd.DataFrame:
        """Fetch market data (OHLCV) for the specified symbols"""
        pass
    
    @abstractmethod
    async def fetch_onchain_data(self) -> pd.DataFrame:
        """Fetch on-chain metrics for the specified symbols"""
        pass
    
    async def fetch_sentiment_data(self) -> pd.DataFrame:
        """Fetch social sentiment data for the specified symbols"""
        return pd.DataFrame()  # Optional, return empty DataFrame by default
    
    async def fetch_defi_metrics(self) -> pd.DataFrame:
        """Fetch DeFi related metrics (TVL, yields, etc.)"""
        return pd.DataFrame()  # Optional, return empty DataFrame by default
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate the collected data
        
        Args:
            df: DataFrame to validate
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        if df.empty:
            logger.warning("Empty DataFrame detected")
            return False
            
        # Check for required columns
        required_columns = ['timestamp', 'symbol']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Missing required columns: {required_columns}")
            return False
            
        # Check for missing values
        if df.isnull().any().any():
            logger.warning("Missing values detected in data")
            return False
            
        return True
    
    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Basic preprocessing of collected data
        
        Args:
            df: Raw DataFrame
            
        Returns:
            pd.DataFrame: Preprocessed DataFrame
        """
        # Handle missing values
        df = df.ffill().bfill()
        
        # Convert timestamps
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Sort by timestamp if available
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp')
            
        return df
    
    async def collect_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        Collect all types of data asynchronously
        
        Returns:
            Dict containing different types of collected data
        """
        try:
            market_data = await self.fetch_market_data()
            onchain_data = await self.fetch_onchain_data()
            sentiment_data = await self.fetch_sentiment_data()
            defi_data = await self.fetch_defi_metrics()
            
            return {
                'market_data': self.preprocess_data(market_data),
                'onchain_data': self.preprocess_data(onchain_data),
                'sentiment_data': self.preprocess_data(sentiment_data),
                'defi_data': self.preprocess_data(defi_data)
            }
            
        except Exception as e:
            logger.error(f"Error collecting data: {str(e)}")
            raise
