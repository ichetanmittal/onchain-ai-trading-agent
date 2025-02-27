import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping
from .data.data_module import CryptoDataModule
from .models.transformer_model import CryptoTransformerLightning
from .training.trainer import ModelTrainer
from .execution.trading_executor import TradingExecutor

logger = logging.getLogger(__name__)

class TradingBotController:
    """Main controller for the trading bot"""
    
    def __init__(self, config_path: str):
        """
        Initialize the controller
        
        Args:
            config_path: Path to config file
        """
        with open(config_path) as f:
            self.config = json.load(f)
            
        self.data_module: Optional[CryptoDataModule] = None
        self.model: Optional[CryptoTransformerLightning] = None
        self.trainer: Optional[ModelTrainer] = None
        self.executor: Optional[TradingExecutor] = None
        
    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("Initializing trading bot components...")
            
            # Initialize data module
            self.data_module = CryptoDataModule(self.config)
            await self.data_module.prepare_data()
            self.data_module.setup()
            
            # Initialize or load model
            self.model = self._load_or_train_model()
            
            # Initialize trading executor
            self.executor = TradingExecutor(
                model=self.model,
                config=self.config
            )
            
        except Exception as e:
            logger.error(f"Error initializing trading bot: {str(e)}")
            raise
            
    def _load_or_train_model(self) -> CryptoTransformerLightning:
        """Load existing model or train a new one"""
        try:
            # Initialize trainer
            self.trainer = ModelTrainer(self.config)
            
            # Create model
            model = None
            
            # Check for existing checkpoint
            checkpoint_dir = os.path.join(os.getcwd(), "checkpoints")
            if os.path.exists(checkpoint_dir):
                checkpoints = [f for f in os.listdir(checkpoint_dir) if f.endswith(".ckpt")]
                if checkpoints:
                    # Load latest checkpoint
                    latest_checkpoint = max(checkpoints, key=lambda x: os.path.getctime(os.path.join(checkpoint_dir, x)))
                    checkpoint_path = os.path.join(checkpoint_dir, latest_checkpoint)
                    logger.info(f"Loading model from checkpoint: {checkpoint_path}")
                    model = CryptoTransformerLightning.load_from_checkpoint(checkpoint_path)
            
            # Train new model if no checkpoint found
            if model is None:
                logger.info("No checkpoint found, training new model...")
                model = CryptoTransformerLightning(self.config)
                self.trainer.train(model, self.data_module)
            else:
                # Attach trainer and data module to loaded model
                self.trainer.setup_model(model)
                model.trainer.datamodule = self.data_module
                
            return model
            
        except Exception as e:
            logger.error(f"Error loading/training model: {str(e)}")
            raise
            
    async def run_trading(self):
        """Run the trading loop"""
        try:
            if not self.executor:
                raise ValueError("Trading executor not initialized")
                
            await self.executor.run()
            
        except Exception as e:
            logger.error(f"Error in trading loop: {str(e)}")
            raise
            
    async def start_continuous_trading(self, interval_seconds: int = 3600):
        """Start continuous trading with specified interval.
        
        Args:
            interval_seconds: Interval between trading iterations in seconds
        """
        try:
            while True:
                await self.run_trading()
                await asyncio.sleep(interval_seconds)
                
        except Exception as e:
            logger.error(f"Error in continuous trading: {str(e)}")
            raise
            
    def optimize_hyperparameters(self):  
        """Run hyperparameter optimization"""
        try:
            if not self.trainer:
                self.trainer = ModelTrainer(self.config)
                
            self.trainer.hyperparameter_optimization(self.data_module)  
            
        except Exception as e:
            logger.error(f"Error in hyperparameter optimization: {str(e)}")
            raise
