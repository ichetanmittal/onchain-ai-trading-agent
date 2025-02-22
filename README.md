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
│   └── controller.py                # Main orchestrator
├── motoko_contracts/                # Internet Computer smart contracts
│   └── src/
│       └── motoko_contracts_backend/
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
- Advanced risk metrics (VaR, CVaR)
- Dynamic rebalancing

### Trading Execution
- ICP blockchain integration
- Real-time trade execution
- Performance monitoring
- Risk management checks

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
```

## Configuration

Create a `config.json` file to customize:
- Model architecture parameters
- Training settings
- Risk management thresholds
- Trading execution rules

Example:
```json
{
    "symbols": ["BTC/USDT", "ETH/USDT"],
    "sequence_length": 60,
    "prediction_horizon": 24,
    "max_position_size": 0.1,
    "risk_aversion": 0.5
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

## Performance Metrics

The system tracks:
- Prediction accuracy (RMSE, MAE)
- Trading metrics (Sharpe ratio, max drawdown)
- Portfolio performance
- Risk metrics (VaR, CVaR)

## License

MIT

## Author

Chetan Mittal