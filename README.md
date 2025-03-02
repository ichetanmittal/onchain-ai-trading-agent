# Advanced On-Chain AI Trading Agent

A state-of-the-art AI-powered trading bot that leverages transformer models, multi-modal data, and the Internet Computer blockchain for cryptocurrency trading.

## Modern Architecture

```
.
├── ai_bot/
│   ├── config/
│   │   └── model_config.py          # Configuration management
│   ├── data/
│   │   └── data_module.py           # PyTorch Lightning data module
│   ├── data_collectors/
│   │   ├── base_collector.py        # Abstract data collector
│   │   └── crypto_collector.py      # Crypto-specific collector
│   ├── features/
│   │   └── feature_engineer.py      # Advanced feature engineering
│   ├── models/
│   │   └── transformer_model.py     # Transformer architecture
│   ├── training/
│   │   └── trainer.py               # MLOps-integrated training
│   ├── strategies/
│   │   └── portfolio_optimizer.py   # Modern portfolio optimization
│   ├── execution/
│   │   └── trading_executor.py      # Trading execution system
│   ├── monitoring/
│   │   └── metrics_tracker.py       # Performance and risk metrics
│   └── controller.py                # Main orchestrator
├── motoko_contracts/                # Internet Computer smart contracts
│   └── src/
│       ├── motoko_contracts_backend/
│       └── motoko_contracts_frontend/ # Modern React-based UI
└── main.py                         # Entry point
```

## Key Features

### Data Collection
- Real-time market data (OHLCV and order book metrics)
- On-chain metrics (transactions, gas prices)
- Social sentiment analysis
- DeFi metrics (TVL, yields)

### Advanced ML Architecture
- Transformer-based model with self-attention
- Uncertainty quantification
- Multi-modal data integration
- Real-time adaptation

### MLOps Integration
- Experiment tracking with Weights & Biases
- Model versioning with MLflow
- Hyperparameter optimization with Optuna
- Automated retraining pipeline

### Portfolio Management
- Modern portfolio theory implementation
- Risk-adjusted optimization
- Advanced risk metrics (VaR, CVaR, Sharpe ratio)
- Dynamic rebalancing
- **NEW**: Randomness-based portfolio diversification

### Trading Execution
- ICP blockchain integration
- Real-time trade execution
- Performance monitoring
- Risk management checks
- Automated portfolio rebalancing

### Modern UI
- Responsive design for all devices
- Real-time portfolio visualization
- Interactive trading metrics dashboard
- Randomness controls for portfolio diversification
- Monte Carlo simulation visualization

## Requirements

See `requirements.txt` for full dependencies. Key packages:

```
tensorflow>=2.15.0
torch>=2.2.0
transformers>=4.37.0
pytorch-lightning>=2.1.0
wandb>=0.16.0
mlflow>=2.10.0
optuna>=3.5.0
```

## Setup and Usage

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Deploy the Internet Computer canister:
```bash
cd motoko_contracts
dfx start --background
dfx deploy
```

3. Run the trading bot:
```bash
# Training mode
python main.py --mode train

# Hyperparameter optimization
python main.py --mode optimize --trials 100

# Trading mode
python main.py --mode trade --interval 3600

# Continuous trading mode (default)
python main.py
```

## Mainnet Deployment

The application is deployed on the Internet Computer mainnet with the following canisters:

### Backend Canister
- **Canister ID**: `uccih-hiaaa-aaaag-at43q-cai`
- **Candid Interface**: [https://a4gq6-oaaaa-aaaab-qaa4q-cai.raw.icp0.io/?id=uccih-hiaaa-aaaag-at43q-cai](https://a4gq6-oaaaa-aaaab-qaa4q-cai.raw.icp0.io/?id=uccih-hiaaa-aaaag-at43q-cai)

### Frontend Canister
- **Canister ID**: `vpmmj-iaaaa-aaaag-at44a-cai`
- **Frontend URL**: [https://vpmmj-iaaaa-aaaag-at44a-cai.icp0.io/](https://vpmmj-iaaaa-aaaag-at44a-cai.icp0.io/)

### Updating the Canisters
To update the deployed canisters with new predictions:
```bash
# Run the trading bot to generate new predictions
python main.py --mode trade --interval 3600

# The bot will automatically update the canister with new predictions
```

## Configuration

Create a `config.json` file to customize:
- Model architecture parameters
- Training settings
- Risk management thresholds
- Trading execution rules
- Randomness parameters

Example:
```json
{
    "symbols": ["BTC/USDT", "ETH/USDT"],
    "sequence_length": 60,
    "prediction_horizon": 24,
    "max_position_size": 0.1,
    "risk_aversion": 0.5,
    "randomness": {
        "enabled": false,
        "factor": 0.2,
        "monte_carlo": {
            "enabled": false,
            "simulations": 1000,
            "confidence_level": 0.95
        }
    }
}
```

## Monitoring

1. Access MLflow UI:
```bash
mlflow ui
```

2. View experiments in W&B:
```bash
wandb login
```

3. View real-time metrics on the frontend dashboard:
   - Portfolio allocation
   - Prediction accuracy
   - Risk metrics (Sharpe ratio, VaR, Max Drawdown)
   - Performance history

## Performance Metrics

The system tracks:
- Prediction accuracy (RMSE, MAE)
- Trading metrics (Sharpe ratio, max drawdown)
- Portfolio performance
- Risk metrics (VaR, CVaR, Volatility)
- Monte Carlo simulation results (when enabled)

## New Features

### Randomness Implementation
The system now supports adding controlled randomness to portfolio allocations, which can help:
- Reduce overfitting to historical patterns
- Explore alternative allocation strategies
- Increase portfolio diversification
- Mitigate model uncertainty

### Monte Carlo Simulation
- Simulates thousands of potential market scenarios
- Calculates confidence intervals for returns
- Estimates Value at Risk (VaR) with higher accuracy
- Provides more robust risk assessment

### Modern UI
- Completely redesigned frontend with modern aesthetics
- Responsive design for mobile, tablet, and desktop
- Interactive charts and visualizations
- Real-time updates from the blockchain
- User-friendly controls for randomness parameters

## License

MIT

## Author

Chetan Mittal