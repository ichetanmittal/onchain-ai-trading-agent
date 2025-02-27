from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import torch

@dataclass
class ModelConfig:
    # Data Configuration
    symbols: List[str] = None
    sequence_length: int = 60
    prediction_horizon: int = 24  # Hours to predict ahead
    batch_size: int = 32
    train_val_split: float = 0.8
    
    # Model Architecture
    model_type: str = "transformer"  # Options: "transformer", "temporal_fusion", "deep_ar"
    d_model: int = 512  # Transformer dimension
    nhead: int = 8  # Number of attention heads
    num_encoder_layers: int = 6
    num_decoder_layers: int = 6
    dim_feedforward: int = 2048
    dropout: float = 0.1
    
    # Training Parameters
    learning_rate: float = 1e-4
    weight_decay: float = 1e-6
    max_epochs: int = 100
    early_stopping_patience: int = 10
    gradient_clip_val: float = 1.0
    
    # Feature Groups
    use_market_data: bool = True
    use_onchain_data: bool = True
    use_sentiment_data: bool = True
    use_defi_metrics: bool = True
    
    # Device Configuration
    device: torch.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Optimization
    use_mixed_precision: bool = True
    num_workers: int = 4
    
    # Monitoring
    log_every_n_steps: int = 50
    wandb_project: str = "crypto-trading-bot"
    
    # Risk Management
    max_position_size: float = 0.1  # Maximum position size as fraction of portfolio
    stop_loss_threshold: float = 0.02  # 2% stop loss
    take_profit_threshold: float = 0.05  # 5% take profit
    
    # Portfolio Optimization
    rebalancing_frequency: str = "1h"  # How often to rebalance
    max_correlation_threshold: float = 0.7  # Maximum allowed correlation between assets
    
    # Feature Engineering
    technical_indicators: List[str] = None
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["BTC/USDT", "ETH/USDT"]
            
        if self.technical_indicators is None:
            self.technical_indicators = [
                "RSI", "MACD", "BB_UPPER", "BB_LOWER", 
                "EMA_12", "EMA_26", "ATR", "OBV"
            ]
            
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ModelConfig':
        """Create a ModelConfig instance from a dictionary"""
        return cls(**{
            k: v for k, v in config_dict.items() 
            if k in cls.__dataclass_fields__
        })
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the config to a dictionary"""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
        
    def validate(self) -> bool:
        """Validate the configuration"""
        assert self.sequence_length > 0, "sequence_length must be positive"
        assert 0 < self.train_val_split < 1, "train_val_split must be between 0 and 1"
        assert self.batch_size > 0, "batch_size must be positive"
        assert self.learning_rate > 0, "learning_rate must be positive"
        assert self.max_epochs > 0, "max_epochs must be positive"
        return True
