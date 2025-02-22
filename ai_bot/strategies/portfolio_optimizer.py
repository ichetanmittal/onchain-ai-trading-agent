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
        
        Args:
            predictions: Dictionary of predicted returns for each asset
            uncertainties: Dictionary of prediction uncertainties
            current_weights: Current portfolio weights
            market_data: Historical market data for risk calculations
            
        Returns:
            Tuple of (optimal weights, portfolio metrics)
        """
        try:
            # Calculate returns and covariance
            returns = self._calculate_returns(market_data)
            cov_matrix = self._calculate_covariance(returns)
            
            # Adjust expected returns based on uncertainties
            adjusted_returns = {
                symbol: pred * (1 - uncertainties[symbol])
                for symbol, pred in predictions.items()
            }
            
            # Setup optimization constraints
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # weights sum to 1
                {'type': 'ineq', 'fun': lambda x: self.max_position_size - np.abs(x)}  # position size limits
            ]
            
            bounds = [(0, self.max_position_size) for _ in self.symbols]
            
            # Initial guess (equal weights)
            x0 = np.array([1.0/len(self.symbols)] * len(self.symbols))
            
            # Optimize
            result = minimize(
                self._objective_function,
                x0,
                args=(adjusted_returns, cov_matrix),
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if not result.success:
                logger.warning(f"Portfolio optimization failed: {result.message}")
                return current_weights, self._calculate_metrics(current_weights, returns, cov_matrix)
            
            # Create weights dictionary
            optimal_weights = dict(zip(self.symbols, result.x))
            
            # Calculate portfolio metrics
            metrics = self._calculate_metrics(optimal_weights, returns, cov_matrix)
            
            return optimal_weights, metrics
            
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {str(e)}")
            return current_weights, self._calculate_metrics(current_weights, returns, cov_matrix)
            
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
        portfolio_values = pd.Series(1)
        for t in returns.index:
            daily_return = sum(returns.loc[t, sym] * weights[sym] for sym in self.symbols)
            portfolio_values[t] = portfolio_values[t-1] * (1 + daily_return)
            
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
        return market_data.pct_change().dropna()
        
    def _calculate_covariance(
        self,
        returns: pd.DataFrame
    ) -> pd.DataFrame:
        """Calculate covariance matrix"""
        return returns.cov()
