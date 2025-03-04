// Import polyfills first
import './polyfills';

// Then import the rest of the app
import App from './App';
import './index.scss';

console.log("[Main] Starting application");
const app = new App();
