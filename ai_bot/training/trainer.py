import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping, LearningRateMonitor
from pytorch_lightning.loggers import WandbLogger
import wandb
import mlflow
import optuna
from optuna.integration import PyTorchLightningPruningCallback
from typing import Dict, Any, Optional
import os
import logging
from ..models.transformer_model import CryptoTransformerLightning
from ..data.data_module import CryptoDataModule

logger = logging.getLogger(__name__)

class ModelTrainer:
    """Advanced model training with MLOps integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.setup_tracking()
        self.trainer = None
        
    def setup_tracking(self):
        """Setup MLOps tracking tools"""
        try:
            # Initialize W&B if configured
            if self.config.get('wandb', {}).get('enabled', False):
                wandb.init(
                    project=self.config['wandb']['project'],
                    config=self.config,
                    name=f"crypto_transformer_{wandb.util.generate_id()}"
                )
            
            # Initialize MLflow if configured
            if self.config.get('mlflow', {}).get('enabled', False):
                mlflow.set_tracking_uri(self.config['mlflow']['tracking_uri'])
                mlflow.set_experiment(self.config['mlflow']['experiment_name'])
            
        except Exception as e:
            logger.warning(f"Error setting up tracking: {str(e)}")
            logger.info("Continuing without MLOps tracking")
            
    def create_callbacks(self) -> list:
        """Create training callbacks"""
        try:
            callbacks = [
                # Model checkpointing
                ModelCheckpoint(
                    dirpath='checkpoints',
                    filename='crypto_transformer-{epoch:02d}-{val_loss:.4f}',
                    save_top_k=3,
                    monitor='val_loss',
                    mode='min'
                ),
                
                # Early stopping
                EarlyStopping(
                    monitor='val_loss',
                    patience=self.config.get('training', {}).get('early_stopping_patience', 10),
                    mode='min'
                ),
                
                # Learning rate monitoring
                LearningRateMonitor(logging_interval='step')
            ]
            
            # Add custom callbacks
            if self.config.get('training', {}).get('monitor_uncertainty', False):
                callbacks.append(UncertaintyMonitorCallback())
                
            if self.config.get('training', {}).get('monitor_trading_metrics', False):
                callbacks.append(TradingMetricsCallback())
                
            return callbacks
            
        except Exception as e:
            logger.error(f"Error creating callbacks: {str(e)}")
            raise
            
    def train(self, model: pl.LightningModule, data_module: CryptoDataModule):
        """Train the model"""
        try:
            # Create trainer
            self.trainer = pl.Trainer(
                max_epochs=self.config.get('training', {}).get('max_epochs', 100),
                callbacks=self.create_callbacks(),
                accelerator='auto',
                devices='auto',
                precision=self.config.get('training', {}).get('precision', 32),
                gradient_clip_val=self.config.get('training', {}).get('gradient_clip_val', 0.5)
            )
            
            # Start MLflow run if configured
            if self.config.get('mlflow', {}).get('enabled', False):
                with mlflow.start_run() as run:
                    # Log parameters
                    mlflow.log_params(self.config)
                    
                    # Train model
                    self.trainer.fit(model, data_module)
            else:
                # Train model without MLflow
                self.trainer.fit(model, data_module)
                
            return model
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
            
    def setup_model(self, model: pl.LightningModule):
        """Setup model for inference"""
        try:
            if self.trainer is None:
                # Create trainer for inference
                self.trainer = pl.Trainer(
                    accelerator='auto',
                    devices='auto',
                    precision=self.config.get('training', {}).get('precision', 32)
                )
                
            # Attach trainer to model
            model.trainer = self.trainer
            
        except Exception as e:
            logger.error(f"Error setting up model: {str(e)}")
            raise
            
    def hyperparameter_optimization(self, data_module: CryptoDataModule):
        """Run hyperparameter optimization using Optuna"""
        try:
            study = optuna.create_study(
                direction="minimize",
                pruner=optuna.pruners.MedianPruner()
            )
            
            def objective(trial):
                # Define hyperparameters to optimize
                config = {
                    'd_model': trial.suggest_int('d_model', 32, 512),
                    'nhead': trial.suggest_int('nhead', 2, 16),
                    'num_encoder_layers': trial.suggest_int('num_encoder_layers', 2, 12),
                    'dim_feedforward': trial.suggest_int('dim_feedforward', 128, 2048),
                    'dropout': trial.suggest_float('dropout', 0.1, 0.5),
                    'learning_rate': trial.suggest_loguniform('learning_rate', 1e-5, 1e-2)
                }
                
                # Create model with trial params
                model = CryptoTransformerLightning({**self.config, **config})
                
                # Create trainer with pruning callback
                trainer = pl.Trainer(
                    max_epochs=self.config.get('training', {}).get('max_epochs', 100),
                    callbacks=[
                        PyTorchLightningPruningCallback(trial, monitor="val_loss"),
                        *self.create_callbacks()
                    ],
                    accelerator='auto',
                    devices='auto'
                )
                
                # Train and return validation loss
                trainer.fit(model, data_module)
                return trainer.callback_metrics["val_loss"].item()
                
            study.optimize(objective, n_trials=100)
            
            # Log best parameters
            logger.info(f"Best hyperparameters: {study.best_params}")
            return study.best_params
            
        except Exception as e:
            logger.error(f"Error in hyperparameter optimization: {str(e)}")
            raise
            
class UncertaintyMonitorCallback(pl.Callback):
    """Monitor prediction uncertainty during training"""
    
    def on_validation_batch_end(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule,
        outputs: Any,
        batch: Any,
        batch_idx: int,
        dataloader_idx: int
    ):
        if batch_idx == 0:  # Log only first batch
            predictions, uncertainty = outputs
            
            # Log uncertainty distribution
            wandb.log({
                'uncertainty_mean': uncertainty.mean().item(),
                'uncertainty_std': uncertainty.std().item(),
                'uncertainty_hist': wandb.Histogram(uncertainty.cpu().numpy())
            })
            
class TradingMetricsCallback(pl.Callback):
    """Monitor trading-specific metrics during training"""
    
    def on_validation_epoch_end(
        self,
        trainer: pl.Trainer,
        pl_module: pl.LightningModule
    ):
        # Calculate and log trading metrics
        metrics = self.calculate_trading_metrics(pl_module)
        wandb.log(metrics)
        
    def calculate_trading_metrics(self, pl_module: pl.LightningModule) -> Dict[str, float]:
        """Calculate trading-specific metrics"""
        # Get predictions and targets
        val_predictions = []
        val_targets = []
        
        # Collect predictions from validation set
        val_dataloader = pl_module.trainer.datamodule.val_dataloader()
        for batch in val_dataloader:
            x, y = batch
            y_hat, _ = pl_module(x)
            val_predictions.extend(y_hat.detach().cpu().numpy())
            val_targets.extend(y.cpu().numpy())
            
        # Calculate metrics
        metrics = {
            'directional_accuracy': self.calculate_directional_accuracy(val_predictions, val_targets),
            'profit_factor': self.calculate_profit_factor(val_predictions, val_targets),
            'sharpe_ratio': self.calculate_sharpe_ratio(val_predictions, val_targets)
        }
        
        return metrics
        
    @staticmethod
    def calculate_directional_accuracy(predictions, targets):
        """Calculate accuracy of predicted price direction"""
        pred_direction = np.diff(predictions) > 0
        true_direction = np.diff(targets) > 0
        return np.mean(pred_direction == true_direction)
        
    @staticmethod
    def calculate_profit_factor(predictions, targets):
        """Calculate ratio of winning trades to losing trades"""
        returns = np.diff(predictions) * np.sign(np.diff(targets))
        winning_trades = returns[returns > 0].sum()
        losing_trades = abs(returns[returns < 0].sum())
        return winning_trades / losing_trades if losing_trades != 0 else float('inf')
        
    @staticmethod
    def calculate_sharpe_ratio(predictions, targets):
        """Calculate Sharpe ratio of predictions"""
        returns = np.diff(predictions)
        return np.mean(returns) / np.std(returns) if np.std(returns) != 0 else 0
