import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import os

class TradingMonitor:
    def __init__(self, log_dir="logs"):
        """Initialize the trading monitor."""
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.prediction_history_file = os.path.join(log_dir, "prediction_history.json")
        self.portfolio_history_file = os.path.join(log_dir, "portfolio_history.json")
        self._load_history()

    def _load_history(self):
        """Load existing history from files."""
        try:
            with open(self.prediction_history_file, 'r') as f:
                self.prediction_history = json.load(f)
        except FileNotFoundError:
            self.prediction_history = []

        try:
            with open(self.portfolio_history_file, 'r') as f:
                self.portfolio_history = json.load(f)
        except FileNotFoundError:
            self.portfolio_history = []

    def validate_prediction(self, ticker: str, predicted_price: float, current_price: float) -> bool:
        """
        Validate if a prediction is reasonable based on historical volatility.
        Returns True if prediction seems valid, False otherwise.
        """
        # Get recent predictions for this ticker
        recent_predictions = [p for p in self.prediction_history 
                            if p['ticker'] == ticker 
                            and (datetime.now() - datetime.fromisoformat(p['timestamp'])).days < 30]
        
        if len(recent_predictions) > 0:
            # Calculate historical prediction volatility
            pred_prices = [p['predicted_price'] for p in recent_predictions]
            pred_std = np.std(pred_prices)
            pred_mean = np.mean(pred_prices)
            
            # Check if current prediction is within 3 standard deviations
            if abs(predicted_price - pred_mean) > 3 * pred_std:
                return False

        # Check if prediction implies unreasonable price movement
        price_change_pct = abs(predicted_price - current_price) / current_price * 100
        if price_change_pct > 50:  # Flag if predicted change is more than 50%
            return False

        return True

    def log_prediction(self, ticker: str, predicted_price: float, current_price: float):
        """Log a new prediction with validation."""
        timestamp = datetime.now().isoformat()
        is_valid = self.validate_prediction(ticker, predicted_price, current_price)
        
        prediction_data = {
            'timestamp': timestamp,
            'ticker': ticker,
            'predicted_price': predicted_price,
            'current_price': current_price,
            'is_valid': is_valid
        }
        
        self.prediction_history.append(prediction_data)
        
        # Save to file
        with open(self.prediction_history_file, 'w') as f:
            json.dump(self.prediction_history, f, indent=2)
        
        return is_valid

    def log_portfolio_update(self, portfolio: dict, rebalance_reason: str):
        """Log portfolio updates with performance metrics."""
        timestamp = datetime.now().isoformat()
        
        # Calculate portfolio value and other metrics
        total_value = sum(portfolio.values())
        portfolio_data = {
            'timestamp': timestamp,
            'portfolio': portfolio,
            'total_value': total_value,
            'rebalance_reason': rebalance_reason
        }
        
        # Add historical performance if available
        if self.portfolio_history:
            last_portfolio = self.portfolio_history[-1]
            value_change = total_value - last_portfolio['total_value']
            pct_change = (value_change / last_portfolio['total_value']) * 100
            portfolio_data['value_change'] = value_change
            portfolio_data['pct_change'] = pct_change
        
        self.portfolio_history.append(portfolio_data)
        
        # Save to file
        with open(self.portfolio_history_file, 'w') as f:
            json.dump(self.portfolio_history, f, indent=2)

    def get_performance_metrics(self, days=30):
        """Calculate performance metrics for the specified time period."""
        if not self.portfolio_history:
            return None

        cutoff_date = datetime.now() - timedelta(days=days)
        relevant_history = [
            p for p in self.portfolio_history 
            if datetime.fromisoformat(p['timestamp']) >= cutoff_date
        ]

        if not relevant_history:
            return None

        initial_value = relevant_history[0]['total_value']
        final_value = relevant_history[-1]['total_value']
        
        # Calculate metrics
        total_return = ((final_value - initial_value) / initial_value) * 100
        daily_returns = [
            (h['total_value'] - prev['total_value']) / prev['total_value']
            for prev, h in zip(relevant_history[:-1], relevant_history[1:])
        ]

        metrics = {
            'period_days': days,
            'total_return_pct': total_return,
            'volatility': np.std(daily_returns) * np.sqrt(252) if daily_returns else None,  # Annualized
            'sharpe_ratio': np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if daily_returns else None,
            'max_drawdown': self._calculate_max_drawdown(relevant_history),
            'prediction_accuracy': self._calculate_prediction_accuracy(days)
        }

        return metrics

    def _calculate_max_drawdown(self, portfolio_history):
        """Calculate the maximum drawdown over a period."""
        values = [p['total_value'] for p in portfolio_history]
        peak = values[0]
        max_drawdown = 0

        for value in values[1:]:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown * 100  # Convert to percentage

    def _calculate_prediction_accuracy(self, days=30):
        """Calculate the accuracy of predictions over a period."""
        cutoff_date = datetime.now() - timedelta(days=days)
        relevant_predictions = [
            p for p in self.prediction_history 
            if datetime.fromisoformat(p['timestamp']) >= cutoff_date
        ]

        if not relevant_predictions:
            return None

        # Count how many predictions were valid
        valid_predictions = sum(1 for p in relevant_predictions if p['is_valid'])
        return (valid_predictions / len(relevant_predictions)) * 100
