import pytorch_lightning as pl
from torch.utils.data import DataLoader, TensorDataset
import torch
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from ..data_collectors.crypto_collector import CryptoDataCollector
from ..features.feature_engineer import FeatureEngineer

logger = logging.getLogger(__name__)

class CryptoDataModule(pl.LightningDataModule):
    """PyTorch Lightning data module for cryptocurrency data"""
    
    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.symbols = config.get('data', {}).get('symbols', ['BTC/USDT', 'ETH/USDT'])
        self.timeframe = config.get('data', {}).get('timeframe', '1h')
        self.sequence_length = config.get('data', {}).get('sequence_length', 60)
        self.prediction_horizon = config.get('data', {}).get('prediction_horizon', 12)
        self.batch_size = config.get('training', {}).get('batch_size', 32)
        
        self.data_collector = CryptoDataCollector(
            symbols=self.symbols,
            timeframe=self.timeframe
        )
        self.feature_engineer = FeatureEngineer()
        
        self.train_data: Optional[TensorDataset] = None
        self.val_data: Optional[TensorDataset] = None
        self.market_data: Optional[pd.DataFrame] = None
        
    async def prepare_data(self):
        """Collect and prepare data"""
        try:
            logger.info("Collecting market data...")
            self.market_data = await self.data_collector.collect_data()
            logger.info(f"Market data shape: {self.market_data.shape}")
            logger.info(f"Market data columns: {self.market_data.columns.tolist()}")
            logger.info(f"Unique symbols in market data: {self.market_data['symbol'].unique().tolist()}")
            
            logger.info("Engineering features...")
            features = self.feature_engineer.create_features({
                'market_data': self.market_data
            })
            logger.info(f"Features shape: {features.shape}")
            logger.info(f"Features columns: {features.columns.tolist()}")
            logger.info(f"Unique symbols in features: {features['symbol'].unique().tolist()}")
            
            # Create sequences for each symbol
            sequences = []
            targets = []
            
            for symbol in self.symbols:
                logger.info(f"Processing symbol: {symbol}")
                symbol_mask = features['symbol'] == symbol
                logger.info(f"Number of rows for {symbol}: {symbol_mask.sum()}")
                
                symbol_features = features[symbol_mask].sort_values('timestamp')
                logger.info(f"Symbol features shape for {symbol}: {symbol_features.shape}")
                
                if symbol_features.empty:
                    logger.warning(f"No data found for symbol {symbol}")
                    continue
                
                # Convert to numpy for faster processing
                feature_array = symbol_features.drop(['symbol', 'timestamp'], axis=1).values
                logger.info(f"Feature array shape for {symbol}: {feature_array.shape}")
                
                # Create sequences
                seq_count = 0
                for i in range(len(feature_array) - self.sequence_length - self.prediction_horizon + 1):
                    x = feature_array[i:i + self.sequence_length]
                    y = feature_array[i + self.sequence_length + self.prediction_horizon - 1, 0]  # Price is first column
                    sequences.append(x)
                    targets.append(y)
                    seq_count += 1
                
                logger.info(f"Created {seq_count} sequences for {symbol}")
            
            if not sequences:
                raise ValueError(f"No sequences could be created. Check the logs for details.")
            
            # Convert to tensors
            X = torch.tensor(sequences, dtype=torch.float32)
            y = torch.tensor(targets, dtype=torch.float32).reshape(-1, 1)
            
            logger.info(f"Final tensor shapes - X: {X.shape}, y: {y.shape}")
            
            # Split into train/val
            train_size = int(0.8 * len(X))
            indices = torch.randperm(len(X))
            
            train_indices = indices[:train_size]
            val_indices = indices[train_size:]
            
            # Create datasets
            self.train_data = TensorDataset(
                X[train_indices],
                y[train_indices]
            )
            
            self.val_data = TensorDataset(
                X[val_indices],
                y[val_indices]
            )
            
            logger.info(f"Created {len(sequences)} sequences from {len(self.symbols)} symbols")
            logger.info(f"Train dataset size: {len(self.train_data)}, Val dataset size: {len(self.val_data)}")
            
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            raise
            
    async def get_latest_data(self) -> torch.Tensor:
        """Get latest market data for prediction"""
        try:
            # Collect latest data
            latest_market_data = await self.data_collector.collect_data()
            
            # Engineer features
            features = self.feature_engineer.create_features({
                'market_data': latest_market_data
            })
            
            # Create sequences for each symbol
            sequences = []
            for symbol in self.symbols:
                symbol_mask = features['symbol'] == symbol
                symbol_features = features[symbol_mask].sort_values('timestamp')
                
                if symbol_features.empty:
                    logger.warning(f"No data found for symbol {symbol}")
                    continue
                
                # Convert to numpy for faster processing
                feature_array = symbol_features.drop(['symbol', 'timestamp'], axis=1).values
                
                # Take the latest sequence
                if len(feature_array) >= self.sequence_length:
                    x = feature_array[-self.sequence_length:]
                    sequences.append(x)
                else:
                    logger.warning(f"Not enough data for a full sequence for {symbol}")
                    
            if not sequences:
                raise ValueError("No sequences could be created from latest data")
                
            # Convert to tensor and reshape for transformer (batch_size, seq_len, input_dim)
            X = torch.tensor(sequences, dtype=torch.float32)
            return X  # Shape: (num_symbols, seq_len, input_dim)
            
        except Exception as e:
            logger.error(f"Error getting latest data: {str(e)}")
            raise
            
    def setup(self, stage: Optional[str] = None):
        """Setup data for training/validation"""
        pass  # Data is already prepared in prepare_data
        
    def train_dataloader(self):
        """Get training data loader"""
        return DataLoader(
            self.train_data,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=4,
            pin_memory=True
        )
        
    def val_dataloader(self):
        """Get validation data loader"""
        return DataLoader(
            self.val_data,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=4,
            pin_memory=True
        )
