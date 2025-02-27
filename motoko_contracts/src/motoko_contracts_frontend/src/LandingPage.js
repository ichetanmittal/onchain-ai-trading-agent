import { html } from 'lit-html';
import './LandingPage.css';

class LandingPage {
  constructor(onLogin) {
    this.onLogin = onLogin;
  }

  render() {
    return html`
      <div class="landing-container">
        <nav class="landing-nav">
          <div class="logo">
            <h1>OnChain AI Trading</h1>
          </div>
          <div class="nav-links">
            <a href="#features">Features</a>
            <a href="#about">About</a>
            <button class="login-btn" @click=${this.onLogin}>Login</button>
          </div>
        </nav>

        <section class="hero">
          <div class="hero-content">
            <h1>AI-Powered Crypto Trading on the Internet Computer</h1>
            <p>Harness the power of artificial intelligence and blockchain technology for smarter cryptocurrency trading</p>
            <button class="cta-btn" @click=${this.onLogin}>Access Dashboard</button>
          </div>
          <div class="hero-image">
            <img src="/assets/hero-image.svg" alt="Trading visualization" />
          </div>
        </section>

        <section id="features" class="features">
          <h2>Key Features</h2>
          <div class="feature-grid">
            <div class="feature-card">
              <div class="feature-icon">🤖</div>
              <h3>AI Predictions</h3>
              <p>Advanced transformer models predict cryptocurrency price movements with uncertainty estimation</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">⛓️</div>
              <h3>On-Chain Execution</h3>
              <p>Fully decentralized trading execution through Internet Computer smart contracts</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">📊</div>
              <h3>Risk Management</h3>
              <p>Portfolio optimization with volatility controls and drawdown protection</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">🔒</div>
              <h3>Secure & Transparent</h3>
              <p>All trading decisions and portfolio allocations are verifiable on-chain</p>
            </div>
          </div>
        </section>

        <section id="about" class="about">
          <h2>About the Project</h2>
          <p>
            OnChain AI Trading is a revolutionary platform that combines state-of-the-art AI models with
            the security and transparency of blockchain technology. Our system uses transformer-based neural networks
            to analyze market data and make predictions, while executing trades through smart contracts on the
            Internet Computer blockchain.
          </p>
          <p>
            The platform features modern portfolio optimization techniques, risk management controls,
            and full transparency of all trading decisions.
          </p>
        </section>

        <footer class="landing-footer">
          <p>&copy; 2025 OnChain AI Trading. All rights reserved.</p>
          <div class="footer-links">
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
            <a href="https://github.com/ichetanmittal/onchain-ai-trading-agent" target="_blank">GitHub</a>
          </div>
        </footer>
      </div>
    `;
  }
}

export default LandingPage;
