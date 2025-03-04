// Configuration for the application

// Determine if we're running in production or development
export const DFX_NETWORK = process.env.DFX_NETWORK || 'ic';

// Canister IDs
export const BACKEND_CANISTER_ID = process.env.MOTOKO_CONTRACTS_BACKEND_CANISTER_ID || 
  (DFX_NETWORK === 'ic' ? 'uccih-hiaaa-aaaag-at43q-cai' : 'bkyz2-fmaaa-aaaaa-qaaaq-cai');

// Internet Identity is always the same on mainnet
export const INTERNET_IDENTITY_CANISTER_ID = 'rdmx6-jaaaa-aaaaa-aaadq-cai';

// Internet Identity URL
export const II_URL = DFX_NETWORK === 'ic' 
  ? 'https://identity.ic0.app' 
  : `http://127.0.0.1:4943/?canisterId=${INTERNET_IDENTITY_CANISTER_ID}`;

// Host URL - Using icp0.io instead of ic0.app for mainnet
export const HOST = DFX_NETWORK === 'ic' 
  ? 'https://icp0.io' 
  : 'http://127.0.0.1:4943';

console.log("[Config] Environment configuration:", {
  DFX_NETWORK,
  BACKEND_CANISTER_ID,
  INTERNET_IDENTITY_CANISTER_ID,
  II_URL,
  HOST
});
