// Polyfills for browser compatibility
import { Buffer } from 'buffer';

// Add Buffer to the global scope
window.Buffer = Buffer;
window.global = window;

// Add process.env if it doesn't exist
if (!window.process) {
  window.process = { env: {} };
}

console.log("[Polyfills] Loaded polyfills for Buffer and process.env");
