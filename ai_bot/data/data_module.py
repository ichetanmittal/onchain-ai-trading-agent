import logging
from typing import Optional, Dict, Any
import pytorch_lightning as pl
import torch
from torch.utils.data import DataLoader, TensorDataset
from ..data_collectors.crypto_collector import CryptoDataCollector
from ..features.feature_engineer import FeatureEngineer

logger = logging.getLogger(__name__)

class CryptoDataModule(pl.LightningDataModule):
    """PyTorch Lightning data module for cryptocurrency data"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the data module
        
        Args:
            config: Configuration dictionary
        """
        super().__init__()
        self.config = config
        self.data_collector = CryptoDataCollector(
            symbols=config['trading']['symbols'],
            timeframe='1h'
        )
        self.feature_engineer = FeatureEngineer()
        
    async def prepare_data(self):
        """Download and prepare the data"""
        try:
            # Collect all types of data
            self.raw_data = await self.data_collector.collect_all_data()
            logger.info("Data collection completed")
            
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            raise
            
    def setup(self, stage: Optional[str] = None):
        """Process data and create train/val splits"""
        try:
            # Engineer features
            features = self.feature_engineer.prepare_features(self.raw_data)
            
            # Create sequences
            X, y = self._create_sequences(features)
            
            # Train/val split
            train_size = int(len(X) * self.config['training']['train_val_split'])
            
            if stage == 'fit' or stage is None:
                self.X_train = X[:train_size]
                self.y_train = y[:train_size]
                self.X_val = X[train_size:]
                self.y_val = y[train_size:]
                
            if stage == 'test' or stage is None:
                self.X_test = X[train_size:]
                self.y_test = y[train_size:]
                
        except Exception as e:
            logger.error(f"Error setting up data: {str(e)}")
            raise
            
    def _create_sequences(self, data):
        """Create sequences for training"""
        try:
            sequence_length = self.config['model']['sequence_length']
            prediction_horizon = self.config['model']['prediction_horizon']
            
            X, y = [], []
            
            for symbol in self.config['trading']['symbols']:
                symbol_data = data[data['symbol'] == symbol]
                values = symbol_data.values
                
                for i in range(len(values) - sequence_length - prediction_horizon + 1):
                    X.append(values[i:i+sequence_length])
                    y.append(values[i+sequence_length:i+sequence_length+prediction_horizon, 3])  # Close price
                    
            return torch.FloatTensor(X), torch.FloatTensor(y)
            
        except Exception as e:
            logger.error(f"Error creating sequences: {str(e)}")
            raise
            
    def train_dataloader(self):
        return DataLoader(
            TensorDataset(self.X_train, self.y_train),
            batch_size=self.config['training']['batch_size'],
            shuffle=True,
            num_workers=4
        )
        
    def val_dataloader(self):
        return DataLoader(
            TensorDataset(self.X_val, self.y_val),
            batch_size=self.config['training']['batch_size'],
            num_workers=4
        )
        
    def test_dataloader(self):
        return DataLoader(
            TensorDataset(self.X_test, self.y_test),
            batch_size=self.config['training']['batch_size'],
            num_workers=4
        )
