#!/bin/bash

# Script to build and deploy frontend updates to the mainnet
echo "Building and deploying frontend updates to the mainnet..."

# Navigate to the motoko_contracts directory
cd "$(dirname "$0")/motoko_contracts"

# Build the frontend
echo "Building frontend..."
npm run --prefix src/motoko_contracts_frontend build

# Deploy to mainnet
echo "Deploying to mainnet..."
dfx deploy --network ic motoko_contracts_frontend

echo "Deployment complete!"
