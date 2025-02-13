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

# Fetch real market data
def fetch_market_data(ticker="BTC-USD", start="2021-01-01", end="2022-01-01"):
    print(f"Fetching market data for {ticker} from {start} to {end}...")
    df = yf.download(ticker, start=start, end=end)
    print("Data fetched successfully.")
    print(df.head())
    df = df[['Close']]
    df.dropna(inplace=True)
    return df

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

def train_model(model, X_train, y_train, epochs=10, batch_size=32):
    print("Training model...")
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size)
    print("Model training complete.")
    return model

def predict_prices(model, X_test, scaler):
    print("Making predictions...")
    predictions = model.predict(X_test)
    predictions = scaler.inverse_transform(predictions)
    print("Predictions generated.")
    return predictions

if __name__ == "__main__":
    df = fetch_market_data(
        ticker="BTC-USD", 
        start="2021-01-01", 
        end="2022-01-01"
    )
    
    X, y, scaler = preprocess_data(df, sequence_length=60)
    
    split_idx = int(len(X) * 0.8)
    X_train, y_train = X[:split_idx], y[:split_idx]
    X_test, y_test = X[split_idx:], y[split_idx:]
    
    model = build_lstm_model((X_train.shape[1], 1))
    model = train_model(model, X_train, y_train, epochs=10, batch_size=32)
    
    predictions = predict_prices(model, X_test, scaler)
    
    actual = df['Close'].values[60:]
    actual_test = actual[split_idx:]
    
    plt.figure(figsize=(12,6))
    plt.plot(range(len(actual_test)), actual_test, label='Actual Price', color='blue')
    plt.plot(range(len(predictions)), predictions, label='Predicted Price', color='red')
    plt.title('BTC-USD Price Prediction')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    plt.show()
    
    # Calculate performance metrics
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    rmse = np.sqrt(mean_squared_error(actual_test, predictions))
    mae = mean_absolute_error(actual_test, predictions)
    print(f"RMSE: {rmse:.2f}")
    print(f"MAE: {mae:.2f}")
    print("Model testing complete.")

    # ---------------------------------------------------------------------
    # Integration with Motoko canister
    # ---------------------------------------------------------------------
    # 1. Extract the final predicted price:
    final_prediction = float(predictions[-1][0])  # e.g., 42000.1234

    print(f"Final predicted price: {final_prediction}")

    # 2. Call the 'setPrediction' method on your deployed canister:
    canister_name = "motoko_contracts_backend"
    
    # Change directory to where dfx.json exists
    original_dir = os.getcwd()
    os.chdir("motoko_contracts")
    
    # Build the dfx command to store the float on-chain
    cmd_set = [
        "dfx", "canister", "call", canister_name,
        "setPrediction",
        f"({final_prediction})"
    ]
    
    try:
        subprocess.run(cmd_set, check=True)
        print("Successfully stored prediction on-chain.")

        cmd_get = [
            "dfx", "canister", "call", canister_name,
            "getPrediction"
        ]
        result = subprocess.run(cmd_get, check=True, capture_output=True, text=True)
        print("On-chain prediction:", result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print("Error calling canister:", e)
        sys.exit(1)
    finally:
        os.chdir(original_dir)