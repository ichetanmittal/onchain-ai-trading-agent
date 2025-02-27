import torch
import torch.nn as nn
import pytorch_lightning as pl
import torch.nn.functional as F
import math
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class PositionalEncoding(nn.Module):
    """Positional encoding for transformer"""
    
    def __init__(self, d_model: int, max_len: int = 5000):
        super().__init__()
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Tensor, shape [seq_len, batch_size, embedding_dim]
        """
        return x + self.pe[:x.size(0)]

class CryptoTransformer(nn.Module):
    """Advanced Transformer model for cryptocurrency price prediction"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        
        # Get model config
        model_config = config.get('model', {})
        
        # Input embedding
        self.input_embedding = nn.Linear(
            model_config.get('input_dim', 32),
            model_config.get('d_model', 256)
        )
        
        # Positional encoding
        self.pos_encoder = PositionalEncoding(model_config.get('d_model', 256))
        
        # Transformer encoder
        encoder_layers = nn.TransformerEncoderLayer(
            d_model=model_config.get('d_model', 256),
            nhead=model_config.get('nhead', 8),
            dim_feedforward=model_config.get('dim_feedforward', 1024),
            dropout=model_config.get('dropout', 0.1),
            batch_first=True,
            activation=model_config.get('activation', 'relu')
        )
        
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layers,
            num_layers=model_config.get('num_encoder_layers', 6)
        )
        
        # Output layers
        self.output_layer = nn.Linear(
            model_config.get('d_model', 256),
            model_config.get('output_dim', 1)
        )
        
        # Uncertainty estimation
        self.uncertainty_layer = nn.Linear(
            model_config.get('d_model', 256),
            model_config.get('output_dim', 1)
        )
        
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass"""
        # Input embedding
        x = self.input_embedding(x)
        
        # Add positional encoding
        x = self.pos_encoder(x)
        
        # Transformer encoder
        x = self.transformer_encoder(x)
        
        # Get predictions for last timestep
        last_hidden = x[:, -1, :]
        
        # Output and uncertainty
        pred = self.output_layer(last_hidden)
        uncertainty = torch.exp(self.uncertainty_layer(last_hidden))  # Ensure positive uncertainty
        
        return pred, uncertainty

class CryptoTransformerLightning(pl.LightningModule):
    """PyTorch Lightning wrapper for CryptoTransformer"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.save_hyperparameters()
        self.config = config
        self.model = CryptoTransformer(config)
        
    def forward(self, x: torch.Tensor):
        return self.model(x)
        
    def training_step(self, batch: Tuple[torch.Tensor, torch.Tensor], batch_idx: int):
        x, y = batch
        y_hat, uncertainty = self(x)
        loss = self._gaussian_nll_loss(y, y_hat, uncertainty)
        self.log('train_loss', loss)
        return loss
        
    def validation_step(self, batch: Tuple[torch.Tensor, torch.Tensor], batch_idx: int):
        x, y = batch
        y_hat, uncertainty = self(x)
        loss = self._gaussian_nll_loss(y, y_hat, uncertainty)
        self.log('val_loss', loss)
        return loss
        
    def configure_optimizers(self):
        optimizer = torch.optim.Adam(
            self.parameters(),
            lr=self.config.get('training', {}).get('learning_rate', 0.001)
        )
        return optimizer
        
    def _gaussian_nll_loss(self, y: torch.Tensor, y_hat: torch.Tensor, uncertainty: torch.Tensor):
        """
        Negative log likelihood loss for a Gaussian distribution with predicted mean and variance
        """
        return 0.5 * torch.mean(
            torch.log(uncertainty) + (y - y_hat)**2 / uncertainty
        )
