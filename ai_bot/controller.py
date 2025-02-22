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
            self.model = await self._load_or_train_model()
            
            # Initialize trading executor
            self.executor = TradingExecutor(
                model=self.model,
                config=self.config
            )
            
        except Exception as e:
            logger.error(f"Error initializing trading bot: {str(e)}")
            raise
            
    async def _load_or_train_model(self) -> CryptoTransformerLightning:
        """Load existing model or train a new one"""
        try:
            # Initialize trainer
            self.trainer = ModelTrainer(self.config)
            
            # Create model
            model = CryptoTransformerLightning(self.config)
            
            # Train model
            await self.trainer.train(model, self.data_module)
            
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
            
    async def optimize_hyperparameters(self):
        """Run hyperparameter optimization"""
        try:
            if not self.trainer:
                self.trainer = ModelTrainer(self.config)
                
            await self.trainer.hyperparameter_optimization(self.data_module)
            
        except Exception as e:
            logger.error(f"Error in hyperparameter optimization: {str(e)}")
            raise
