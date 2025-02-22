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
    
    def __init__(self, config):
        self.config = config
        self.data_collector = CryptoDataCollector(config.symbols)
        
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
            cov_matrix = self._calculate_covariance(returns, uncertainties)
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(returns, current_weights)
            
            # Define optimization constraints
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
                {'type': 'ineq', 'fun': lambda x: x - self.config.min_position_size},  # Minimum position size
                {'type': 'ineq', 'fun': lambda x: self.config.max_position_size - x}  # Maximum position size
            ]
            
            # Add maximum drawdown constraint
            constraints.append({
                'type': 'ineq',
                'fun': lambda x: self.config.max_drawdown - self._calculate_drawdown(x, returns)
            })
            
            # Add correlation constraint
            constraints.append({
                'type': 'ineq',
                'fun': lambda x: self.config.max_correlation_threshold - self._calculate_portfolio_correlation(x, returns)
            })
            
            # Initial guess (current weights)
            initial_weights = np.array(list(current_weights.values()))
            
            # Optimize
            result = minimize(
                self._objective_function,
                initial_weights,
                args=(predictions, cov_matrix, risk_metrics),
                method='SLSQP',
                constraints=constraints,
                bounds=[(0, 1) for _ in range(len(predictions))]
            )
            
            if not result.success:
                logger.warning(f"Portfolio optimization failed: {result.message}")
                return current_weights, self._calculate_portfolio_metrics(
                    current_weights, predictions, cov_matrix, returns
                )
            
            # Create optimal weights dictionary
            optimal_weights = dict(zip(predictions.keys(), result.x))
            
            # Calculate portfolio metrics
            metrics = self._calculate_portfolio_metrics(
                optimal_weights, predictions, cov_matrix, returns
            )
            
            return optimal_weights, metrics
            
        except Exception as e:
            logger.error(f"Error optimizing portfolio: {str(e)}")
            raise
            
    def _objective_function(
        self,
        weights: np.ndarray,
        predictions: Dict[str, float],
        cov_matrix: np.ndarray,
        risk_metrics: Dict[str, float]
    ) -> float:
        """
        Multi-objective function combining return and risk
        
        Maximize: expected_return - lambda * risk
        where risk includes volatility, VaR, and other risk metrics
        """
        # Expected return
        exp_return = np.sum(weights * np.array(list(predictions.values())))
        
        # Portfolio volatility
        volatility = np.sqrt(weights.T @ cov_matrix @ weights)
        
        # Risk-adjusted return (negative because we're minimizing)
        risk_adjusted_return = -(exp_return - self.config.risk_aversion * volatility)
        
        # Add penalty for concentration risk
        concentration_penalty = self._calculate_concentration_penalty(weights)
        
        # Add penalty for high correlation
        correlation_penalty = self._calculate_correlation_penalty(weights)
        
        return risk_adjusted_return + concentration_penalty + correlation_penalty
        
    def _calculate_returns(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate historical returns"""
        return market_data.pct_change().dropna()
        
    def _calculate_covariance(
        self,
        returns: pd.DataFrame,
        uncertainties: Dict[str, float]
    ) -> np.ndarray:
        """Calculate covariance matrix with uncertainty adjustment"""
        # Base covariance
        cov_matrix = returns.cov().values
        
        # Add prediction uncertainty to diagonal
        uncertainty_array = np.array(list(uncertainties.values()))
        np.fill_diagonal(cov_matrix, cov_matrix.diagonal() + uncertainty_array**2)
        
        return cov_matrix
        
    def _calculate_risk_metrics(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate various risk metrics"""
        portfolio_returns = returns.dot(np.array(list(weights.values())))
        
        return {
            'volatility': portfolio_returns.std(),
            'var_95': portfolio_returns.quantile(0.05),
            'cvar_95': portfolio_returns[portfolio_returns <= portfolio_returns.quantile(0.05)].mean(),
            'max_drawdown': self._calculate_drawdown(np.array(list(weights.values())), returns)
        }
        
    def _calculate_drawdown(self, weights: np.ndarray, returns: pd.DataFrame) -> float:
        """Calculate maximum drawdown"""
        portfolio_returns = returns.dot(weights)
        cumulative_returns = (1 + portfolio_returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdowns = cumulative_returns / rolling_max - 1
        return abs(drawdowns.min())
        
    def _calculate_portfolio_correlation(self, weights: np.ndarray, returns: pd.DataFrame) -> float:
        """Calculate average pairwise correlation of assets in portfolio"""
        corr_matrix = returns.corr().values
        weighted_corr = weights.reshape(-1, 1) @ weights.reshape(1, -1) * corr_matrix
        return weighted_corr.mean()
        
    def _calculate_concentration_penalty(self, weights: np.ndarray) -> float:
        """Calculate penalty for concentrated positions"""
        return self.config.concentration_penalty * np.sum(weights**2)
        
    def _calculate_correlation_penalty(self, weights: np.ndarray) -> float:
        """Calculate penalty for high correlations"""
        return self.config.correlation_penalty * (weights.std() / weights.mean() if weights.mean() != 0 else 0)
        
    def _calculate_portfolio_metrics(
        self,
        weights: Dict[str, float],
        predictions: Dict[str, float],
        cov_matrix: np.ndarray,
        returns: pd.DataFrame
    ) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics"""
        weights_array = np.array(list(weights.values()))
        
        # Expected return
        expected_return = np.sum(weights_array * np.array(list(predictions.values())))
        
        # Volatility
        volatility = np.sqrt(weights_array.T @ cov_matrix @ weights_array)
        
        # Sharpe ratio
        risk_free_rate = 0.02  # Assumed risk-free rate
        sharpe_ratio = (expected_return - risk_free_rate) / volatility if volatility != 0 else 0
        
        # Calculate portfolio returns
        portfolio_returns = returns.dot(weights_array)
        
        # Max drawdown
        max_drawdown = self._calculate_drawdown(weights_array, returns)
        
        # VaR and CVaR
        var_95 = portfolio_returns.quantile(0.05)
        cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
        
        return PortfolioMetrics(
            expected_return=expected_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            var_95=var_95,
            cvar_95=cvar_95,
            asset_weights=weights
        )
