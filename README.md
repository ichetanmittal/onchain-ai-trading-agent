# On-Chain AI Trading Agent

An AI-powered trading bot that makes Bitcoin price predictions and stores them on the Internet Computer blockchain.

## Project Structure

```
.
├── ai_bot/
│   └── ai_trading_model.py    # LSTM model for BTC price prediction
└── motoko_contracts/          # Internet Computer smart contracts
    ├── src/
    │   ├── motoko_contracts_backend/    # Motoko backend
    │   └── motoko_contracts_frontend/   # Frontend interface
    └── dfx.json
```

## Features

- LSTM-based Bitcoin price prediction
- Real-time data fetching using yfinance
- On-chain storage of predictions using Internet Computer
- Performance metrics (RMSE, MAE)

## Requirements

```
yfinance
pandas
numpy
tensorflow
scikit-learn
matplotlib
```

## Setup

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

3. Run the AI model:
```bash
python ai_bot/ai_trading_model.py
```

## How it Works

1. The AI model fetches historical BTC-USD data
2. Processes and trains an LSTM model
3. Makes price predictions
4. Stores the final prediction on the Internet Computer blockchain
5. Retrieves the stored prediction to verify

## License

MIT

## Author

Chetan Mittal 