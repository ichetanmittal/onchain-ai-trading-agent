#!/bin/bash

# Start API server for the AI Trading Bot
echo "Starting API server for the AI Trading Bot..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 is required but not installed. Please install Python3 and try again."
    exit 1
fi

# Check if Flask is installed
python3 -c "import flask" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Flask is not installed. Installing Flask..."
    pip install flask cors
fi

# Create a temporary API server file if it doesn't exist
API_SERVER_FILE="/Users/chetanmittal/Desktop/icp-ai-trading-bot/api_server.py"

if [ ! -f "$API_SERVER_FILE" ]; then
    echo "Creating API server file..."
    cat > "$API_SERVER_FILE" << 'EOF'
#!/usr/bin/env python3

import os
import json
import subprocess
import threading
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='api_server.log'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables
trading_process = None
config_path = "/Users/chetanmittal/Desktop/icp-ai-trading-bot/config.json"
project_root = "/Users/chetanmittal/Desktop/icp-ai-trading-bot"

def load_config():
    """Load the trading bot configuration."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return {}

def start_trading_bot(mode="trade", interval=3600):
    """Start the trading bot as a subprocess."""
    global trading_process
    
    # Kill any existing process
    if trading_process and trading_process.poll() is None:
        trading_process.terminate()
        trading_process = None
    
    # Start the trading bot
    cmd = [
        "python", 
        os.path.join(project_root, "main.py"),
        "--mode", mode,
        "--interval", str(interval),
        "--config", config_path
    ]
    
    logger.info(f"Starting trading bot with command: {' '.join(cmd)}")
    trading_process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Start a thread to log the output
    def log_output():
        for line in trading_process.stdout:
            logger.info(f"Bot: {line.strip()}")
    
    threading.Thread(target=log_output, daemon=True).start()
    return trading_process.pid

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the status of the trading bot."""
    global trading_process
    
    if trading_process is None:
        return jsonify({"status": "stopped", "pid": None})
    
    # Check if the process is still running
    if trading_process.poll() is None:
        return jsonify({"status": "running", "pid": trading_process.pid})
    else:
        return jsonify({"status": "stopped", "pid": None, "exit_code": trading_process.returncode})

@app.route('/api/start', methods=['POST'])
def start_bot():
    """Start the trading bot."""
    data = request.json or {}
    mode = data.get('mode', 'trade')
    interval = int(data.get('interval', 3600))
    
    pid = start_trading_bot(mode, interval)
    return jsonify({"status": "started", "pid": pid})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    """Stop the trading bot."""
    global trading_process
    
    if trading_process is None:
        return jsonify({"status": "already_stopped"})
    
    if trading_process.poll() is None:
        trading_process.terminate()
        return jsonify({"status": "stopped"})
    else:
        return jsonify({"status": "already_stopped"})

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get the current configuration."""
    return jsonify(load_config())

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update the configuration."""
    data = request.json
    
    try:
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=4)
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get the last N lines of the log file."""
    lines = request.args.get('lines', 100, type=int)
    
    try:
        with open('api_server.log', 'r') as f:
            log_lines = f.readlines()
        return jsonify({"logs": log_lines[-lines:]})
    except Exception as e:
        logger.error(f"Error reading logs: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
EOF

    chmod +x "$API_SERVER_FILE"
fi

# Start the API server
echo "Starting API server on http://localhost:8080"
python3 "$API_SERVER_FILE"
