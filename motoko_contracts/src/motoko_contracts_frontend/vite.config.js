import { defineConfig } from 'vite';
import { fileURLToPath, URL } from 'url';
import environment from 'vite-plugin-environment';
import dotenv from 'dotenv';
import { nodePolyfills } from 'vite-plugin-node-polyfills';

dotenv.config({ path: '../../.env' });

// Define canister IDs based on environment
const DFX_NETWORK = process.env.DFX_NETWORK || 'ic';
const INTERNET_IDENTITY_CANISTER_ID = 'rdmx6-jaaaa-aaaaa-aaadq-cai'; // Production II canister ID

const MOTOKO_CONTRACTS_BACKEND_CANISTER_ID = 
  DFX_NETWORK === 'ic'
    ? process.env.MOTOKO_CONTRACTS_BACKEND_CANISTER_ID || 'uccih-hiaaa-aaaag-at43q-cai' // Production canister ID from canister_ids.json
    : process.env.MOTOKO_CONTRACTS_BACKEND_CANISTER_ID || 'bkyz2-fmaaa-aaaaa-qaaaq-cai'; // Local canister ID

// Add these to process.env so they're available to the application
process.env.INTERNET_IDENTITY_CANISTER_ID = INTERNET_IDENTITY_CANISTER_ID;
process.env.MOTOKO_CONTRACTS_BACKEND_CANISTER_ID = MOTOKO_CONTRACTS_BACKEND_CANISTER_ID;

// Log the environment configuration
console.log("Vite config environment:", {
  DFX_NETWORK,
  INTERNET_IDENTITY_CANISTER_ID,
  MOTOKO_CONTRACTS_BACKEND_CANISTER_ID
});

export default defineConfig({
  build: {
    emptyOutDir: true,
    rollupOptions: {
      external: [],
    },
  },
  optimizeDeps: {
    esbuildOptions: {
      define: {
        global: "globalThis",
      },
    },
  },
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:4943",
        changeOrigin: true,
      },
    },
  },
  publicDir: "assets",
  plugins: [
    environment("all", { prefix: "CANISTER_" }),
    environment("all", { prefix: "DFX_" }),
    environment({
      INTERNET_IDENTITY_CANISTER_ID,
      MOTOKO_CONTRACTS_BACKEND_CANISTER_ID,
      DFX_NETWORK,
    }),
    nodePolyfills({
      // To exclude specific polyfills, add them to this list
      exclude: [],
      // Whether to polyfill specific globals
      globals: {
        Buffer: true,
        global: true,
        process: true,
      },
      // Whether to polyfill node: protocol imports
      protocolImports: true,
    }),
  ],
  resolve: {
    alias: [
      {
        find: "declarations",
        replacement: fileURLToPath(
          new URL("../declarations", import.meta.url)
        ),
      },
      {
        find: 'buffer',
        replacement: 'buffer',
      },
    ],
    dedupe: ['@dfinity/agent', '@dfinity/auth-client', '@dfinity/identity', '@dfinity/principal'],
  },
  define: {
    // Make environment variables available to the client-side code
    'process.env.DFX_NETWORK': JSON.stringify(DFX_NETWORK),
    'process.env.INTERNET_IDENTITY_CANISTER_ID': JSON.stringify(INTERNET_IDENTITY_CANISTER_ID),
    'process.env.MOTOKO_CONTRACTS_BACKEND_CANISTER_ID': JSON.stringify(MOTOKO_CONTRACTS_BACKEND_CANISTER_ID),
    'global': 'window',
  },
});
