import torch
import torch.nn as nn
import pytorch_lightning as pl
import torch.nn.functional as F
import math
from typing import Dict, Any, Optional, Tuple
from ..config.model_config import ModelConfig
import logging
import math

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
    
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        
        # Input embedding
        self.input_embedding = nn.Linear(config.input_dim, config.d_model)
        
        # Positional encoding
        self.pos_encoder = PositionalEncoding(config.d_model)
        
        # Transformer encoder
        encoder_layers = nn.TransformerEncoderLayer(
            d_model=config.d_model,
            nhead=config.nhead,
            dim_feedforward=config.d_model * 4,
            dropout=config.dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layers,
            num_layers=config.num_encoder_layers
        )
        
        # Transformer decoder
        decoder_layers = nn.TransformerDecoderLayer(
            d_model=config.d_model,
            nhead=config.nhead,
            dim_feedforward=config.d_model * 4,
            dropout=config.dropout,
            batch_first=True
        )
        self.transformer_decoder = nn.TransformerDecoder(
            decoder_layers,
            num_layers=config.num_decoder_layers
        )
        
        # Output layers
        self.fc1 = nn.Linear(config.d_model, config.d_model // 2)
        self.dropout = nn.Dropout(config.dropout)
        self.fc2 = nn.Linear(config.d_model // 2, config.output_dim)
        
        # Uncertainty estimation
        self.uncertainty_fc = nn.Linear(config.d_model // 2, config.output_dim)
        
        # Attention weights for interpretability
        self.attention_weights = None
        
    def generate_square_subsequent_mask(self, sz: int) -> torch.Tensor:
        """Generate mask for decoder self-attention"""
        mask = (torch.triu(torch.ones(sz, sz)) == 1).transpose(0, 1)
        mask = mask.float().masked_fill(mask == 0, float('-inf')).masked_fill(mask == 1, float(0.0))
        return mask
        
    def forward(
        self,
        src: torch.Tensor,
        tgt: Optional[torch.Tensor] = None,
        src_mask: Optional[torch.Tensor] = None,
        tgt_mask: Optional[torch.Tensor] = None,
        memory_mask: Optional[torch.Tensor] = None,
        src_key_padding_mask: Optional[torch.Tensor] = None,
        tgt_key_padding_mask: Optional[torch.Tensor] = None,
        memory_key_padding_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass of the model
        
        Args:
            src: Source sequence [batch_size, seq_len, input_dim]
            tgt: Target sequence for teacher forcing
            *_mask: Various attention masks
            *_key_padding_mask: Masks for padding tokens
            
        Returns:
            predictions: Predicted values
            uncertainty: Uncertainty estimates
        """
        try:
            # Embed input
            src = self.input_embedding(src)
            src = self.pos_encoder(src)
            
            # Generate target sequence if not provided (inference time)
            if tgt is None:
                tgt = src[:, -1:, :]  # Use last input token as initial target
                tgt_mask = self.generate_square_subsequent_mask(tgt.size(1)).to(src.device)
            
            # Encode source sequence
            memory = self.transformer_encoder(
                src,
                mask=src_mask,
                src_key_padding_mask=src_key_padding_mask
            )
            
            # Decode
            output = self.transformer_decoder(
                tgt,
                memory,
                tgt_mask=tgt_mask,
                memory_mask=memory_mask,
                tgt_key_padding_mask=tgt_key_padding_mask,
                memory_key_padding_mask=memory_key_padding_mask
            )
            
            # Store attention weights for interpretability
            if self.training:
                self.attention_weights = self.transformer_decoder.layers[-1].multihead_attn.attention_weights
            
            # Output processing
            features = self.fc1(output)
            features = F.relu(features)
            features = self.dropout(features)
            
            # Predictions and uncertainty
            predictions = self.fc2(features)
            uncertainty = torch.exp(self.uncertainty_fc(features))  # Log variance to ensure positive uncertainty
            
            return predictions, uncertainty
            
        except Exception as e:
            logger.error(f"Error in transformer forward pass: {str(e)}")
            raise
            
    def get_attention_weights(self) -> Optional[torch.Tensor]:
        """Return attention weights for interpretability"""
        return self.attention_weights
        
class CryptoTransformerLightning(pl.LightningModule):
    """PyTorch Lightning wrapper for CryptoTransformer"""
    
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.save_hyperparameters()
        self.config = config
        self.model = CryptoTransformer(config)
        
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.model(x)
        
    def training_step(self, batch: Tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> torch.Tensor:
        x, y = batch
        y_hat, uncertainty = self(x)
        
        # Negative log likelihood loss with uncertainty
        loss = self._gaussian_nll_loss(y, y_hat, uncertainty)
        
        # Log metrics
        self.log('train_loss', loss, on_step=True, on_epoch=True, prog_bar=True)
        return loss
        
    def validation_step(self, batch: Tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> Dict[str, torch.Tensor]:
        x, y = batch
        y_hat, uncertainty = self(x)
        
        # Calculate metrics
        val_loss = self._gaussian_nll_loss(y, y_hat, uncertainty)
        mse_loss = F.mse_loss(y_hat, y)
        
        # Log metrics
        self.log('val_loss', val_loss, on_epoch=True, prog_bar=True)
        self.log('val_mse', mse_loss, on_epoch=True)
        
        return {'val_loss': val_loss, 'val_mse': mse_loss}
        
    def configure_optimizers(self):
        optimizer = torch.optim.Adam(
            self.parameters(),
            lr=self.config.learning_rate
        )
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode='min',
            factor=0.5,
            patience=5,
            verbose=True
        )
        
        return {
            'optimizer': optimizer,
            'lr_scheduler': {
                'scheduler': scheduler,
                'monitor': 'val_loss'
            }
        }
        
    def _gaussian_nll_loss(self, y: torch.Tensor, y_hat: torch.Tensor, uncertainty: torch.Tensor) -> torch.Tensor:
        """
        Negative log likelihood loss for a Gaussian distribution with predicted mean and variance
        """
        loss = 0.5 * (torch.log(uncertainty) + (y - y_hat)**2 / uncertainty)
        return loss.mean()
