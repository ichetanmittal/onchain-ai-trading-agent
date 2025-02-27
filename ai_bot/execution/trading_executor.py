import asyncio
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import os
import json
import logging
import torch
import subprocess
try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False

from ..strategies.portfolio_optimizer import ModernPortfolioOptimizer, PortfolioMetrics
from ..models.transformer_model import CryptoTransformerLightning

logger = logging.getLogger(__name__)

class TradingExecutor:
    """Advanced trading execution system with ICP integration"""
    
    def __init__(self, config, model: CryptoTransformerLightning):
        self.config = config
        self.model = model
        self.portfolio_optimizer = ModernPortfolioOptimizer(config)
        self.current_positions: Dict[str, float] = {}
        self.trade_history: List[Dict] = []
        # Use mainnet by default, can be overridden in config
        self.use_mainnet = config.get('icp', {}).get('use_mainnet', True)
        self.canister_id = config.get('icp', {}).get('canister_id', 'motoko_contracts_backend')
        # If using mainnet and no specific canister ID is provided, use the known mainnet ID
        if self.use_mainnet and self.canister_id == 'motoko_contracts_backend':
            self.canister_id = 'uccih-hiaaa-aaaag-at43q-cai'
        
    async def execute_trading_cycle(self):
        """Execute one trading cycle"""
        try:
            # Get predictions from model
            predictions, uncertainties = await self._get_predictions()
            logger.info(f"Predictions shape: {predictions.shape}")
            logger.info(f"Uncertainties shape: {uncertainties.shape}")
            
            # Convert predictions to dict for optimizer
            pred_dict = {}
            uncert_dict = {}
            symbols = self.config.get('data', {}).get('symbols', ['BTC/USDT', 'ETH/USDT'])
            for i, symbol in enumerate(symbols):
                pred_dict[symbol] = predictions[i].item()  # Each prediction is a scalar
                uncert_dict[symbol] = uncertainties[i].item()
            
            # Get current portfolio from ICP canister
            current_portfolio = await self._get_portfolio_from_icp()
            
            # Get market data for risk calculations
            market_data = await self._fetch_market_data()
            
            # Optimize portfolio allocation
            optimizer = ModernPortfolioOptimizer(self.config)
            target_portfolio, metrics = await optimizer.optimize_portfolio(
                predictions=pred_dict,
                uncertainties=uncert_dict,
                current_weights=current_portfolio,
                market_data=market_data
            )
            
            # Store metrics for ICP canister update
            self.latest_metrics = metrics
            
            # Validate risk metrics
            if not self._validate_risk_metrics(metrics):
                logger.warning("Risk validation failed, skipping trade execution")
                return
            
            # Generate trades to reach target allocation
            trades = self._generate_trades(current_portfolio, target_portfolio)
            
            # Execute trades through ICP canister
            await self._execute_trades_on_icp(trades)
            
            # Update trade history
            self._update_trade_history(trades, predictions, metrics)
            
            # Log execution metrics
            self._log_execution_metrics(predictions, metrics, trades)
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {str(e)}")
            raise
            
    async def _get_predictions(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get predictions from the model"""
        try:
            data_module = self.model.trainer.datamodule
            latest_data = await data_module.get_latest_data()
            
            # Move to same device as model
            latest_data = latest_data.to(self.model.device)
            
            with torch.no_grad():
                predictions, uncertainties = self.model(latest_data)
            return predictions, uncertainties
            
        except Exception as e:
            logger.error(f"Error in getting predictions: {str(e)}")
            raise
            
    async def _get_portfolio_from_icp(self) -> Dict[str, float]:
        """Get current portfolio state from ICP canister"""
        try:
            # Build command with network parameter if using mainnet
            cmd = ["dfx", "canister"]
            if self.use_mainnet:
                cmd.extend(["--network", "ic"])
            cmd.extend(["call", self.canister_id, "getPortfolio"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd="/Users/chetanmittal/Desktop/icp-ai-trading-bot/motoko_contracts"
            )
            
            # Log raw response for debugging
            logger.debug(f"Raw ICP response: {result.stdout}")
            
            # Parse canister response format: (record { btc = 1000.0 : float64; eth = 1000.0 : float64 })
            portfolio_str = result.stdout.strip()
            btc_val = float(portfolio_str.split('btc = ')[1].split(' :')[0])
            eth_val = float(portfolio_str.split('eth = ')[1].split(' :')[0])
            
            logger.info(f"Parsed portfolio values - BTC: {btc_val}, ETH: {eth_val}")
            
            return {
                'BTC/USDT': btc_val,
                'ETH/USDT': eth_val
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio from ICP: {str(e)}")
            # Return dummy portfolio for now
            return {
                'BTC/USDT': 1000.0,
                'ETH/USDT': 1000.0
            }

    async def _fetch_market_data(self) -> pd.DataFrame:
        """Fetch recent market data for analysis"""
        try:
            data_module = self.model.trainer.datamodule
            raw_data = await data_module.data_collector.collect_data()
            return raw_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            raise
            
    def _validate_risk_metrics(self, metrics: PortfolioMetrics) -> bool:
        """Validate portfolio risk metrics against thresholds"""
        # Check volatility
        if metrics.volatility > self.config['trading']['max_volatility']:
            logger.warning(f"Portfolio volatility {metrics.volatility:.2f} exceeds threshold {self.config['trading']['max_volatility']:.2f}")
            return False
            
        # Check Value at Risk
        if abs(metrics.var_95) > self.config['trading']['max_var']:
            logger.warning(f"Portfolio VaR {abs(metrics.var_95):.2f} exceeds threshold {self.config['trading']['max_var']:.2f}")
            return False
            
        # Check maximum drawdown
        if metrics.max_drawdown > self.config['trading']['max_drawdown']:
            logger.warning(f"Portfolio drawdown {metrics.max_drawdown:.2f} exceeds threshold {self.config['trading']['max_drawdown']:.2f}")
            return False
            
        # Check Sharpe ratio
        if metrics.sharpe_ratio < self.config['trading']['min_sharpe_ratio']:
            logger.warning(f"Portfolio Sharpe ratio {metrics.sharpe_ratio:.2f} below threshold {self.config['trading']['min_sharpe_ratio']:.2f}")
            return False
            
        return True
        
    def _generate_trades(
        self,
        current_portfolio: Dict[str, float],
        target_portfolio: Dict[str, float]
    ) -> List[Dict]:
        """Generate trades to move from current to target portfolio"""
        trades = []
        total_value = sum(current_portfolio.values())
        
        for symbol in current_portfolio:
            current_weight = current_portfolio[symbol] / total_value
            target_weight = target_portfolio[symbol] / total_value
            weight_diff = target_weight - current_weight
            
            # Only trade if difference exceeds minimum size
            if abs(weight_diff) > self.config['trading']['min_trade_size']:
                trades.append({
                    'symbol': symbol,
                    'action': 'buy' if weight_diff > 0 else 'sell',
                    'amount': abs(weight_diff) * total_value,
                    'prediction': target_weight
                })
                
        return trades
        
    async def _execute_trades_on_icp(self, trades: List[Dict]) -> None:
        """Execute trades through ICP canister"""
        try:
            # First set the predictions on the canister
            predictions = {t['symbol']: t['prediction'] for t in trades}
            
            # Build command with network parameter if using mainnet
            cmd = ["dfx", "canister"]
            if self.use_mainnet:
                cmd.extend(["--network", "ic"])
            cmd.extend(["call", self.canister_id, "setPredictions", 
                     f"({predictions.get('BTC/USDT', 0.0)}, {predictions.get('ETH/USDT', 0.0)})"])
            
            # Run dfx from the motoko_contracts directory
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd="/Users/chetanmittal/Desktop/icp-ai-trading-bot/motoko_contracts"
            )
            logger.info("Set predictions on ICP canister")

            # Trigger rebalance
            cmd = ["dfx", "canister"]
            if self.use_mainnet:
                cmd.extend(["--network", "ic"])
            cmd.extend(["call", self.canister_id, "rebalance"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd="/Users/chetanmittal/Desktop/icp-ai-trading-bot/motoko_contracts"
            )
            logger.info(f"Rebalance result: {result.stdout}")
            
            # Update metrics on the canister
            if hasattr(self, 'latest_metrics') and self.latest_metrics:
                cmd = ["dfx", "canister"]
                if self.use_mainnet:
                    cmd.extend(["--network", "ic"])
                cmd.extend(["call", self.canister_id, "updateMetrics", 
                         f"({self.latest_metrics.sharpe_ratio}, {self.latest_metrics.volatility}, {self.latest_metrics.var_95}, {self.latest_metrics.max_drawdown})"])
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd="/Users/chetanmittal/Desktop/icp-ai-trading-bot/motoko_contracts"
                )
                logger.info("Updated metrics on ICP canister")

        except Exception as e:
            logger.error(f"Error executing trades on ICP: {str(e)}")
            raise

    def _update_trade_history(
        self,
        trades: List[Dict],
        predictions: torch.Tensor,
        metrics: PortfolioMetrics
    ) -> None:
        """Update trade history with execution details"""
        try:
            # Convert predictions to dictionary
            pred_dict = {
                self.config['data']['symbols'][i]: pred.item()
                for i, pred in enumerate(predictions)
            }
            
            for trade in trades:
                trade_record = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': trade['symbol'],
                    'action': trade['action'],
                    'amount': trade['amount'],
                    'predicted_price': pred_dict[trade['symbol']],
                    'portfolio_metrics': {
                        'sharpe_ratio': metrics.sharpe_ratio,
                        'volatility': metrics.volatility,
                        'var_95': metrics.var_95,
                        'max_drawdown': metrics.max_drawdown
                    }
                }
                
                self.trade_history.append(trade_record)
                logger.info(f"Trade recorded: {trade_record}")
                
        except Exception as e:
            logger.error(f"Error updating trade history: {str(e)}")
            
    def _log_execution_metrics(
        self,
        predictions: torch.Tensor,
        metrics: PortfolioMetrics,
        trades: List[Dict]
    ):
        """Log execution metrics to wandb if available"""
        try:
            if not WANDB_AVAILABLE:
                return
                
            wandb.log({
                'sharpe_ratio': metrics.sharpe_ratio,
                'volatility': metrics.volatility,
                'var_95': metrics.var_95,
                'max_drawdown': metrics.max_drawdown,
                'trade_count': len(trades),
                'total_trade_volume': sum(trade['amount'] for trade in trades)
            })
        except Exception as e:
            logger.error(f"Error logging execution metrics: {str(e)}")
            
    async def run(self):
        """Run continuous trading execution"""
        try:
            logger.info("Starting trading execution...")
            await self.execute_trading_cycle()
            
        except Exception as e:
            logger.error(f"Error in trading execution: {str(e)}")
            raise
