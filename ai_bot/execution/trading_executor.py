import asyncio
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import subprocess
import os
import json
import logging
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
        
    async def execute_trading_cycle(self):
        """Execute one complete trading cycle"""
        try:
            # 1. Get latest market data and predictions
            predictions, uncertainties = await self._get_predictions()
            
            # 2. Get current portfolio state from ICP
            current_portfolio = await self._get_portfolio_from_icp()
            
            # 3. Optimize portfolio
            new_weights, metrics = await self.portfolio_optimizer.optimize_portfolio(
                predictions,
                uncertainties,
                current_portfolio,
                await self._fetch_market_data()
            )
            
            # 4. Apply risk management checks
            if not self._validate_risk_metrics(metrics):
                logger.warning("Risk metrics exceeded thresholds, maintaining current positions")
                return
            
            # 5. Calculate required trades
            trades = self._calculate_trades(current_portfolio, new_weights)
            
            # 6. Execute trades through ICP
            if trades:
                success = await self._execute_trades_on_icp(trades)
                if success:
                    self._update_trade_history(trades, predictions, metrics)
                    
            # 7. Log execution metrics
            self._log_execution_metrics(predictions, metrics, trades)
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {str(e)}")
            raise
            
    async def _get_predictions(self) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Get predictions and uncertainties from the model"""
        try:
            # Get latest data
            data_module = self.model.trainer.datamodule
            latest_data = await data_module.get_latest_data()
            
            # Make predictions
            with torch.no_grad():
                predictions, uncertainties = self.model(latest_data)
            
            # Convert to dictionaries
            pred_dict = {}
            uncert_dict = {}
            for i, symbol in enumerate(self.config.symbols):
                pred_dict[symbol] = predictions[0, -1, i].item()
                uncert_dict[symbol] = uncertainties[0, -1, i].item()
                
            return pred_dict, uncert_dict
            
        except Exception as e:
            logger.error(f"Error getting predictions: {str(e)}")
            raise
            
    async def _get_portfolio_from_icp(self) -> Dict[str, float]:
        """Get current portfolio state from ICP canister"""
        try:
            # Change to directory with dfx.json
            original_dir = os.getcwd()
            os.chdir("motoko_contracts")
            
            # Call canister
            result = subprocess.run(
                ["dfx", "canister", "call", "motoko_contracts_backend", "getPortfolio"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse result
            portfolio = json.loads(result.stdout)
            
            # Change back to original directory
            os.chdir(original_dir)
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error getting portfolio from ICP: {str(e)}")
            raise
            
    async def _fetch_market_data(self) -> pd.DataFrame:
        """Fetch recent market data for analysis"""
        try:
            data_module = self.model.trainer.datamodule
            raw_data = await data_module.data_collector.fetch_market_data()
            return raw_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            raise
            
    def _validate_risk_metrics(self, metrics: PortfolioMetrics) -> bool:
        """Validate portfolio risk metrics against thresholds"""
        # Check volatility
        if metrics.volatility > self.config.max_volatility:
            logger.warning(f"Portfolio volatility {metrics.volatility:.2f} exceeds threshold {self.config.max_volatility:.2f}")
            return False
            
        # Check Value at Risk
        if abs(metrics.var_95) > self.config.max_var:
            logger.warning(f"Portfolio VaR {abs(metrics.var_95):.2f} exceeds threshold {self.config.max_var:.2f}")
            return False
            
        # Check maximum drawdown
        if metrics.max_drawdown > self.config.max_drawdown:
            logger.warning(f"Portfolio drawdown {metrics.max_drawdown:.2f} exceeds threshold {self.config.max_drawdown:.2f}")
            return False
            
        # Check Sharpe ratio
        if metrics.sharpe_ratio < self.config.min_sharpe_ratio:
            logger.warning(f"Portfolio Sharpe ratio {metrics.sharpe_ratio:.2f} below threshold {self.config.min_sharpe_ratio:.2f}")
            return False
            
        return True
        
    def _calculate_trades(
        self,
        current_portfolio: Dict[str, float],
        target_weights: Dict[str, float]
    ) -> List[Dict]:
        """Calculate required trades to achieve target weights"""
        trades = []
        total_value = sum(current_portfolio.values())
        
        for symbol, target_weight in target_weights.items():
            current_weight = current_portfolio.get(symbol, 0) / total_value
            weight_diff = target_weight - current_weight
            
            if abs(weight_diff) > self.config.min_trade_size:
                trades.append({
                    'symbol': symbol,
                    'action': 'buy' if weight_diff > 0 else 'sell',
                    'amount': abs(weight_diff) * total_value
                })
                
        return trades
        
    async def _execute_trades_on_icp(self, trades: List[Dict]) -> bool:
        """Execute trades through ICP canister"""
        try:
            # Change to directory with dfx.json
            original_dir = os.getcwd()
            os.chdir("motoko_contracts")
            
            for trade in trades:
                # Prepare trade parameters
                params = json.dumps({
                    'symbol': trade['symbol'],
                    'action': trade['action'],
                    'amount': trade['amount']
                })
                
                # Execute trade through canister
                result = subprocess.run(
                    ["dfx", "canister", "call", "motoko_contracts_backend", "executeTrade", params],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                if "Error" in result.stdout:
                    logger.error(f"Trade execution failed: {result.stdout}")
                    return False
                    
            # Change back to original directory
            os.chdir(original_dir)
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing trades on ICP: {str(e)}")
            return False
            
    def _update_trade_history(
        self,
        trades: List[Dict],
        predictions: Dict[str, float],
        metrics: PortfolioMetrics
    ):
        """Update trade history with execution details"""
        for trade in trades:
            self.trade_history.append({
                'timestamp': datetime.now().isoformat(),
                'symbol': trade['symbol'],
                'action': trade['action'],
                'amount': trade['amount'],
                'predicted_price': predictions[trade['symbol']],
                'portfolio_metrics': {
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'volatility': metrics.volatility,
                    'var_95': metrics.var_95
                }
            })
            
    def _log_execution_metrics(
        self,
        predictions: Dict[str, float],
        metrics: PortfolioMetrics,
        trades: List[Dict]
    ):
        """Log execution metrics to monitoring system"""
        try:
            # Log to W&B
            wandb.log({
                'portfolio_value': sum(self.current_positions.values()),
                'portfolio_sharpe': metrics.sharpe_ratio,
                'portfolio_volatility': metrics.volatility,
                'portfolio_var': metrics.var_95,
                'portfolio_cvar': metrics.cvar_95,
                'trade_count': len(trades),
                'total_trade_value': sum(trade['amount'] for trade in trades)
            })
            
            # Log to MLflow
            with mlflow.start_run(nested=True):
                mlflow.log_metrics({
                    'portfolio_sharpe': metrics.sharpe_ratio,
                    'portfolio_volatility': metrics.volatility,
                    'trade_count': len(trades)
                })
                
        except Exception as e:
            logger.error(f"Error logging execution metrics: {str(e)}")
            raise
