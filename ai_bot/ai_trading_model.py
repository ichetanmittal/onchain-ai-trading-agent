import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import yfinance as yf
import subprocess
import sys
import os
from monitoring import TradingMonitor

# We'll keep your existing structure, but add a second asset (ETH) so we can
# store two predictions in the canister and then rebalance.

# Fetch real market data
def fetch_market_data(ticker="BTC-USD", start="2021-01-01", end="2022-01-01"):
    print(f"Fetching market data for {ticker} from {start} to {end}...")
    df = yf.download(ticker, start=start, end=end)
    print("Data fetched successfully.")
    print(df.head())
    df = df[['Close']]
    df.dropna(inplace=True)
    return df

# Preprocess data for LSTM
def preprocess_data(df, sequence_length=60):
    print("Preprocessing data...")
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(df['Close'].values.reshape(-1, 1))
    
    X, y = [], []
    for i in range(sequence_length, len(scaled_data)):
        X.append(scaled_data[i-sequence_length:i, 0])
        y.append(scaled_data[i, 0])
    
    X = np.array(X)
    y = np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    
    print(f"Processed {len(X)} samples.")
    return X, y, scaler

# Build the LSTM model
def build_lstm_model(input_shape):
    print("Building LSTM model...")
    model = Sequential([
        LSTM(units=50, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(units=50, return_sequences=False),
        Dropout(0.2),
        Dense(units=25),
        Dense(units=1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    print("Model built successfully.")
    return model

# Train model function
def train_model(model, X_train, y_train, epochs=10, batch_size=32):
    print("Training model...")
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size)
    print("Model training complete.")
    return model

# Predict future prices
def predict_prices(model, X_test, scaler):
    print("Making predictions...")
    predictions = model.predict(X_test)
    predictions = scaler.inverse_transform(predictions)
    print("Predictions generated.")
    return predictions


if __name__ == "__main__":
    # Initialize trading monitor
    monitor = TradingMonitor()

    # -----------------------------
    # 1. BTC Prediction
    # -----------------------------
    df_btc = fetch_market_data(
        ticker="BTC-USD", 
        start="2021-01-01", 
        end="2022-01-01"
    )
    X_btc, y_btc, scaler_btc = preprocess_data(df_btc, sequence_length=60)

    split_idx_btc = int(len(X_btc) * 0.8)
    X_btc_train, y_btc_train = X_btc[:split_idx_btc], y_btc[:split_idx_btc]
    X_btc_test, y_btc_test = X_btc[split_idx_btc:], y_btc[split_idx_btc:]

    model_btc = build_lstm_model((X_btc_train.shape[1], 1))
    model_btc = train_model(model_btc, X_btc_train, y_btc_train, epochs=10, batch_size=32)

    predictions_btc = predict_prices(model_btc, X_btc_test, scaler_btc)
    # We'll just print the final BTC predicted price (last test sample)
    final_btc_pred = float(predictions_btc[-1][0])
    print(f"Final BTC predicted price: {final_btc_pred}")

    # Validate and log BTC prediction
    current_btc_price = float(df_btc['Close'].iloc[-1])
    if monitor.log_prediction("BTC-USD", final_btc_pred, current_btc_price):
        print("BTC prediction validated and logged")
    else:
        print("Warning: BTC prediction seems unusual, proceeding with caution")

    # Evaluate BTC performance for reference
    actual_btc = df_btc['Close'].values[60:]
    actual_btc_test = actual_btc[split_idx_btc:]

    from sklearn.metrics import mean_squared_error, mean_absolute_error
    rmse_btc = np.sqrt(mean_squared_error(actual_btc_test, predictions_btc))
    mae_btc = mean_absolute_error(actual_btc_test, predictions_btc)
    print(f"BTC RMSE: {rmse_btc:.2f}")
    print(f"BTC MAE: {mae_btc:.2f}")

    # -----------------------------
    # 2. ETH Prediction
    # -----------------------------
    df_eth = fetch_market_data(
        ticker="ETH-USD", 
        start="2021-01-01", 
        end="2022-01-01"
    )
    X_eth, y_eth, scaler_eth = preprocess_data(df_eth, sequence_length=60)

    split_idx_eth = int(len(X_eth) * 0.8)
    X_eth_train, y_eth_train = X_eth[:split_idx_eth], y_eth[:split_idx_eth]
    X_eth_test, y_eth_test = X_eth[split_idx_eth:], y_eth[split_idx_eth:]

    model_eth = build_lstm_model((X_eth_train.shape[1], 1))
    model_eth = train_model(model_eth, X_eth_train, y_eth_train, epochs=10, batch_size=32)

    predictions_eth = predict_prices(model_eth, X_eth_test, scaler_eth)
    final_eth_pred = float(predictions_eth[-1][0])
    print(f"Final ETH predicted price: {final_eth_pred}")

    # Validate and log ETH prediction
    current_eth_price = float(df_eth['Close'].iloc[-1])
    if monitor.log_prediction("ETH-USD", final_eth_pred, current_eth_price):
        print("ETH prediction validated and logged")
    else:
        print("Warning: ETH prediction seems unusual, proceeding with caution")

    actual_eth = df_eth['Close'].values[60:]
    actual_eth_test = actual_eth[split_idx_eth:]

    rmse_eth = np.sqrt(mean_squared_error(actual_eth_test, predictions_eth))
    mae_eth = mean_absolute_error(actual_eth_test, predictions_eth)
    print(f"ETH RMSE: {rmse_eth:.2f}")
    print(f"ETH MAE: {mae_eth:.2f}")

    # -----------------------------
    # 3. Visualize (Optional)
    # -----------------------------
    plt.figure(figsize=(12,6))
    plt.plot(range(len(actual_btc_test)), actual_btc_test, label='BTC Actual', color='blue')
    plt.plot(range(len(predictions_btc)), predictions_btc, label='BTC Predicted', color='red')
    plt.title('BTC-USD Price Prediction')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    plt.show(block=False)

    plt.figure(figsize=(12,6))
    plt.plot(range(len(actual_eth_test)), actual_eth_test, label='ETH Actual', color='green')
    plt.plot(range(len(predictions_eth)), predictions_eth, label='ETH Predicted', color='orange')
    plt.title('ETH-USD Price Prediction')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

    print("All model testing complete.")

    # ---------------------------------------------------------------------
    # 4. Integration with Motoko canister
    # ---------------------------------------------------------------------
    # We'll store both final predictions and then call a rebalance function.

    print(f"Storing final BTC = {final_btc_pred}, ETH = {final_eth_pred}")

    canister_name = "motoko_contracts_backend"
    original_dir = os.getcwd()
    os.chdir("motoko_contracts")  # change to folder where dfx.json exists

    # setPredictions(btcPred, ethPred)
    cmd_set = [
        "dfx", "canister", "call", canister_name,
        "setPredictions",
        f"({final_btc_pred}, {final_eth_pred})"
    ]

    try:
        subprocess.run(cmd_set, check=True)
        print("Successfully stored predictions on-chain.")

        # Now call rebalance()
        cmd_rebalance = [
            "dfx", "canister", "call", canister_name,
            "rebalance"
        ]
        rebalance_res = subprocess.run(cmd_rebalance, check=True, capture_output=True, text=True)
        print("Rebalance result:", rebalance_res.stdout.strip())

        # Finally, get the updated portfolio
        cmd_portfolio = [
            "dfx", "canister", "call", canister_name,
            "getPortfolio"
        ]
        portfolio_res = subprocess.run(cmd_portfolio, check=True, capture_output=True, text=True)
        print("Updated portfolio:", portfolio_res.stdout.strip())

        # Parse and log portfolio update
        portfolio_str = portfolio_res.stdout.strip()
        # Extract numbers from (record { btc = X : float64; eth = Y : float64 })
        import re
        numbers = re.findall(r'(\d+\.?\d*)', portfolio_str)
        if len(numbers) == 2:
            portfolio = {'BTC': float(numbers[0]), 'ETH': float(numbers[1])}
            monitor.log_portfolio_update(
                portfolio,
                f"Rebalance based on predictions: BTC={final_btc_pred}, ETH={final_eth_pred}"
            )

        # Display performance metrics
        metrics = monitor.get_performance_metrics(days=30)
        if metrics:
            print("\nPerformance Metrics (Last 30 days):")
            print(f"Total Return: {metrics['total_return_pct']:.2f}%")
            print(f"Volatility: {metrics['volatility']:.2f}%")
            print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
            print(f"Prediction Accuracy: {metrics['prediction_accuracy']:.2f}%")
    except subprocess.CalledProcessError as e:
        print("Error calling canister:", e)
        sys.exit(1)
    finally:
        os.chdir(original_dir)
