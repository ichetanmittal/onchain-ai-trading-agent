import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional
import cvxopt
from dataclasses import dataclass
import logging
from ..data_collectors.crypto_collector import CryptoDataCollector

logger = logging.getLogger(__name__)

@dataclass
class PortfolioMetrics:
    """Container for portfolio metrics"""
    expected_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    var_95: float  # 95% Value at Risk
    cvar_95: float  # 95% Conditional Value at Risk
    asset_weights: Dict[str, float]

class ModernPortfolioOptimizer:
    """Advanced portfolio optimization with risk management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.symbols = config['data']['symbols']
        self.risk_free_rate = config['trading']['risk_free_rate']
        self.target_volatility = config['trading']['target_volatility']
        self.max_position_size = config['trading']['max_position_size']
        self.data_collector = CryptoDataCollector(self.symbols)
        
    async def optimize_portfolio(
        self,
        predictions: Dict[str, float],
        uncertainties: Dict[str, float],
        current_weights: Dict[str, float],
        market_data: pd.DataFrame
    ) -> Tuple[Dict[str, float], PortfolioMetrics]:
        """
        Optimize portfolio weights using modern portfolio theory and risk management
        """
        try:
            # Calculate returns and covariance first
            returns = self._calculate_returns(market_data)
            cov_matrix = self._calculate_covariance(returns)
            
            # Convert predictions and uncertainties to arrays
            pred_array = np.array([predictions[s] for s in self.symbols])
            uncert_array = np.array([uncertainties[s] for s in self.symbols])
            
            n_assets = len(self.symbols)
            x0 = np.ones(n_assets) / n_assets
            bounds = [(0.2, 0.8) for _ in range(n_assets)]
            
            constraints = [
                {
                    'type': 'eq',
                    'fun': lambda x: np.sum(x) - 1.0
                }
            ]
            
            def objective(weights):
                # Penalize deviation from predictions
                prediction_alignment = -np.sum(weights * pred_array)
                
                # Penalize high uncertainty
                uncertainty_penalty = np.sum(weights * uncert_array)
                
                # Add L2 regularization to prevent extreme allocations
                l2_reg = 0.1 * np.sum(weights ** 2)
                
                return prediction_alignment + uncertainty_penalty + l2_reg
            
            result = minimize(
                objective,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'ftol': 1e-6, 'maxiter': 1000}
            )
            
            if not result.success:
                logger.warning(f"Portfolio optimization warning: {result.message}")
                return current_weights, self._calculate_metrics(current_weights, returns, cov_matrix)
            
            # Ensure weights sum to 1 and respect bounds
            weights = np.clip(result.x, 0.2, 0.8)
            weights = weights / np.sum(weights)
            
            optimal_weights = {
                symbol: float(weight)
                for symbol, weight in zip(self.symbols, weights)
            }
            
            # Calculate portfolio metrics
            metrics = self._calculate_metrics(optimal_weights, returns, cov_matrix)
            
            return optimal_weights, metrics
            
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {str(e)}")
            # Fallback to equal weights
            weight = 1.0 / len(self.symbols)
            equal_weights = {symbol: weight for symbol in self.symbols}
            
            # Still need returns for metrics
            returns = self._calculate_returns(market_data)
            cov_matrix = self._calculate_covariance(returns)
            metrics = self._calculate_metrics(equal_weights, returns, cov_matrix)
            
            return equal_weights, metrics
            
    def _objective_function(
        self,
        weights: np.ndarray,
        returns: Dict[str, float],
        cov_matrix: pd.DataFrame
    ) -> float:
        """
        Portfolio optimization objective function
        Maximizes Sharpe ratio while respecting volatility target
        """
        portfolio_return = np.sum([returns[sym] * w for sym, w in zip(self.symbols, weights)])
        portfolio_vol = np.sqrt(weights.T @ cov_matrix.values @ weights)
        
        # Calculate Sharpe ratio
        sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
        
        # Add penalty for exceeding target volatility
        vol_penalty = max(0, portfolio_vol - self.target_volatility) * 100
        
        return -sharpe + vol_penalty  # Minimize negative Sharpe ratio
        
    def _calculate_metrics(
        self,
        weights: Dict[str, float],
        returns: pd.DataFrame,
        cov_matrix: pd.DataFrame
    ) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics"""
        w = np.array([weights[sym] for sym in self.symbols])
        
        # Expected return and volatility
        portfolio_return = np.sum([returns[sym].mean() * weights[sym] for sym in self.symbols])
        portfolio_vol = np.sqrt(w.T @ cov_matrix.values @ w)
        
        # Sharpe ratio
        sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
        
        # Calculate historical portfolio values
        portfolio_returns = pd.Series(0.0, index=returns.index)
        for t in returns.index:
            portfolio_returns[t] = sum(returns.loc[t, sym] * weights[sym] for sym in self.symbols)
            
        portfolio_values = (1 + portfolio_returns).cumprod()
        
        # Maximum drawdown
        rolling_max = portfolio_values.expanding().max()
        drawdowns = (portfolio_values - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()
        
        # Value at Risk (VaR) and Conditional VaR (CVaR)
        portfolio_returns = returns @ w
        var_95 = np.percentile(portfolio_returns, 5)
        cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
        
        return PortfolioMetrics(
            expected_return=portfolio_return,
            volatility=portfolio_vol,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            var_95=var_95,
            cvar_95=cvar_95,
            asset_weights=weights
        )
        
    def _calculate_returns(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate historical returns"""
        # Pivot data to get price series for each symbol
        prices = market_data.pivot(index='timestamp', columns='symbol', values='close')
        
        # Calculate returns
        returns = prices.pct_change().dropna()
        
        return returns
        
    def _calculate_covariance(
        self,
        returns: pd.DataFrame
    ) -> pd.DataFrame:
        """Calculate covariance matrix"""
        return returns.cov()
