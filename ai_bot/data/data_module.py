import logging
import asyncio
from typing import Dict, Optional, List, Tuple
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader, TensorDataset
import pytorch_lightning as pl
from ..data_collectors.crypto_collector import CryptoDataCollector
from ..features.feature_engineer import FeatureEngineer

logger = logging.getLogger(__name__)

class CryptoDataModule(pl.LightningDataModule):
    """Module for handling cryptocurrency data"""
    
    def __init__(self, config: Dict):
        """
        Initialize data module
        
        Args:
            config: Configuration dictionary
        """
        super().__init__()
        self.config = config
        self.symbols = config.get('symbols', ['BTC/USDT', 'ETH/USDT'])
        self.timeframe = config.get('timeframe', '1h')
        self.sequence_length = config.get('sequence_length', 60)
        self.prediction_horizon = config.get('prediction_horizon', 12)
        self.batch_size = config.get('training', {}).get('batch_size', 32)
        
        # Initialize components
        self.data_collector = CryptoDataCollector(
            symbols=self.symbols,
            timeframe=self.timeframe
        )
        self.feature_engineer = FeatureEngineer(config)
        
        # Data storage
        self.raw_data = None
        self.features = None
        self.train_data = None
        self.val_data = None
        
    async def prepare_data(self):
        """Prepare data for model training"""
        try:
            # Collect data
            self.raw_data = await self.data_collector.collect_all_data()
            logger.info("Data collection completed")
            
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            raise
            
    def setup(self, stage: Optional[str] = None):
        """Set up data for training"""
        try:
            # Format data as expected by feature engineer
            data_dict = {'market_data': self.raw_data}
            
            # Prepare features
            features_df = self.feature_engineer.prepare_features(data_dict)
            
            # Create sequences for each symbol
            sequences = []
            for symbol in self.raw_data['symbol'].unique():
                # Get data for this symbol
                symbol_mask = self.raw_data['symbol'] == symbol
                symbol_features = features_df[symbol_mask]
                
                # Create sequences
                X, y = self._create_sequences(symbol_features)
                sequences.append((X, y))
            
            # Combine sequences from all symbols
            if sequences:
                X = torch.cat([seq[0] for seq in sequences])
                y = torch.cat([seq[1] for seq in sequences])
                
                # Split into train/val
                train_size = int(0.8 * len(X))
                self.train_data = TensorDataset(X[:train_size], y[:train_size])
                self.val_data = TensorDataset(X[train_size:], y[train_size:])
                
                logger.info(f"Created {len(X)} sequences from {len(sequences)} symbols")
            else:
                raise ValueError("No sequences could be created from the data")
            
        except Exception as e:
            logger.error(f"Error setting up data: {str(e)}")
            raise
            
    def _create_sequences(self, features: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Create sequences for training"""
        try:
            sequences = []
            targets = []
            
            # Convert features to numpy for easier slicing
            features_np = features.numpy()
            
            # Create sequences
            for i in range(len(features_np) - self.sequence_length - self.prediction_horizon + 1):
                seq = features_np[i:i + self.sequence_length]
                target = features_np[i + self.sequence_length:i + self.sequence_length + self.prediction_horizon, 3]  # Use close price as target
                sequences.append(seq)
                targets.append(target)
            
            # Convert back to tensors
            X = torch.tensor(sequences, dtype=torch.float32)
            y = torch.tensor(targets, dtype=torch.float32)
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error creating sequences: {str(e)}")
            raise
            
    def train_dataloader(self):
        """Get training dataloader"""
        return DataLoader(
            self.train_data,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=0
        )
        
    def val_dataloader(self):
        """Get validation dataloader"""
        return DataLoader(
            self.val_data,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=0
        )
