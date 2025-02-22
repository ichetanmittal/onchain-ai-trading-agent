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
    
    def __init__(self, config):
        self.config = config
        self.setup_tracking()
        
    def setup_tracking(self):
        """Setup MLOps tracking tools"""
        try:
            # Initialize W&B
            wandb.init(
                project=self.config.wandb_project,
                config=self.config.to_dict(),
                name=f"crypto_transformer_{wandb.util.generate_id()}"
            )
            
            # Initialize MLflow
            mlflow.set_tracking_uri("http://localhost:5000")
            mlflow.set_experiment("crypto_trading_bot")
            
        except Exception as e:
            logger.error(f"Error setting up tracking: {str(e)}")
            raise
            
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
                    patience=self.config.early_stopping_patience,
                    mode='min'
                ),
                
                # Learning rate monitoring
                LearningRateMonitor(logging_interval='step'),
                
                # Custom callback for uncertainty monitoring
                UncertaintyMonitorCallback(),
                
                # Custom callback for trading metrics
                TradingMetricsCallback()
            ]
            
            return callbacks
            
        except Exception as e:
            logger.error(f"Error creating callbacks: {str(e)}")
            raise
            
    async def train(self, data_module: CryptoDataModule) -> CryptoTransformerLightning:
        """Train the model"""
        try:
            # Create model
            model = CryptoTransformerLightning(self.config)
            
            # Setup logger
            wandb_logger = WandbLogger(project=self.config.wandb_project)
            
            # Create trainer
            trainer = pl.Trainer(
                max_epochs=self.config.max_epochs,
                callbacks=self.create_callbacks(),
                logger=wandb_logger,
                accelerator='auto',
                devices='auto',
                precision=16 if self.config.use_mixed_precision else 32,
                gradient_clip_val=self.config.gradient_clip_val
            )
            
            # Start MLflow run
            with mlflow.start_run() as run:
                # Log parameters
                mlflow.log_params(self.config.to_dict())
                
                # Train model
                await trainer.fit(model, data_module)
                
                # Log metrics
                mlflow.log_metrics(trainer.callback_metrics)
                
                # Log model
                mlflow.pytorch.log_model(model, "model")
                
            return model
            
        except Exception as e:
            logger.error(f"Error during training: {str(e)}")
            raise
            
    async def hyperparameter_optimization(
        self,
        data_module: CryptoDataModule,
        n_trials: int = 100
    ) -> Dict[str, Any]:
        """Perform hyperparameter optimization using Optuna"""
        try:
            async def objective(trial: optuna.Trial) -> float:
                # Define hyperparameter search space
                config = self.config
                config.learning_rate = trial.suggest_loguniform('learning_rate', 1e-5, 1e-3)
                config.dropout = trial.suggest_uniform('dropout', 0.1, 0.5)
                config.nhead = trial.suggest_categorical('nhead', [4, 8, 16])
                config.num_encoder_layers = trial.suggest_int('num_encoder_layers', 2, 8)
                config.num_decoder_layers = trial.suggest_int('num_decoder_layers', 2, 8)
                
                # Create model and trainer
                model = CryptoTransformerLightning(config)
                trainer = pl.Trainer(
                    max_epochs=10,  # Use fewer epochs for HPO
                    callbacks=[PyTorchLightningPruningCallback(trial, monitor='val_loss')],
                    logger=False,
                    accelerator='auto',
                    devices='auto'
                )
                
                # Train and validate
                await trainer.fit(model, data_module)
                
                return trainer.callback_metrics['val_loss'].item()
                
            # Create study
            study = optuna.create_study(
                direction='minimize',
                pruner=optuna.pruners.MedianPruner()
            )
            
            # Optimize
            await study.optimize(objective, n_trials=n_trials)
            
            # Log best parameters
            mlflow.log_params(study.best_params)
            
            return study.best_params
            
        except Exception as e:
            logger.error(f"Error during hyperparameter optimization: {str(e)}")
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
