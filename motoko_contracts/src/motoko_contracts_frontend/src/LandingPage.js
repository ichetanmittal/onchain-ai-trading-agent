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
            <h1>OnChain<span class="accent">AI</span></h1>
          </div>
          <div class="nav-links">
            <a href="#features">Features</a>
            <a href="#about">About</a>
            <a href="https://github.com/ichetanmittal/onchain-ai-trading-agent" target="_blank">GitHub</a>
            <button class="login-btn" @click=${this.onLogin}>Login</button>
          </div>
          <button class="mobile-menu-btn">
            <span></span>
            <span></span>
            <span></span>
          </button>
        </nav>

        <section class="hero">
          <div class="hero-content">
            <div class="badge">Powered by Internet Computer</div>
            <h1>AI-Powered <span class="gradient-text">Crypto Trading</span> for the Future</h1>
            <p>Harness the power of artificial intelligence and blockchain technology for smarter, more transparent cryptocurrency trading decisions</p>
            <div class="cta-buttons">
              <button class="cta-btn primary" @click=${this.onLogin}>Get Started</button>
              <button class="cta-btn secondary" @click=${() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}>Learn More</button>
            </div>
            <div class="hero-stats">
              <div class="stat">
                <span class="stat-value">99.8%</span>
                <span class="stat-label">Uptime</span>
              </div>
              <div class="stat">
                <span class="stat-value">100%</span>
                <span class="stat-label">On-Chain</span>
              </div>
              <div class="stat">
                <span class="stat-value">24/7</span>
                <span class="stat-label">Monitoring</span>
              </div>
            </div>
          </div>
          <div class="hero-image">
            <div class="blob-bg"></div>
            <img src="hero-image.svg" alt="Trading visualization" />
          </div>
        </section>

        <section id="features" class="features">
          <div class="section-header">
            <div class="section-tag">Features</div>
            <h2>Cutting-Edge <span class="gradient-text">AI Technology</span></h2>
            <p class="section-description">Our platform combines state-of-the-art machine learning with blockchain security</p>
          </div>
          <div class="feature-grid">
            <div class="feature-card">
              <div class="feature-icon ai-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M9 9H9.01M15 9H15.01M10 14C10 14 11 16 12 16C13 16 14 14 14 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <h3>AI Predictions</h3>
              <p>Advanced transformer models predict cryptocurrency price movements with uncertainty estimation</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon blockchain-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M7 10L12 4L17 10L12 16L7 10Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M12 16L7 20L12 24L17 20L12 16Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M12 4L7 0L12 4L17 0L12 4Z" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <h3>On-Chain Execution</h3>
              <p>Fully decentralized trading execution through Internet Computer smart contracts</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon risk-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M12 8V12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <path d="M12 16H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <h3>Risk Management</h3>
              <p>Portfolio optimization with volatility controls and drawdown protection</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon security-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 22C12 22 20 18 20 12V5L12 2L4 5V12C4 18 12 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M9 12L11 14L15 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <h3>Secure & Transparent</h3>
              <p>All trading decisions and portfolio allocations are verifiable on-chain</p>
            </div>
          </div>
        </section>

        <section class="how-it-works">
          <div class="section-header">
            <div class="section-tag">Process</div>
            <h2>How <span class="gradient-text">It Works</span></h2>
            <p class="section-description">A simple three-step process to start trading with AI</p>
          </div>
          <div class="steps">
            <div class="step">
              <div class="step-number">01</div>
              <h3>Connect Wallet</h3>
              <p>Securely connect your Internet Computer wallet to our platform</p>
            </div>
            <div class="step">
              <div class="step-number">02</div>
              <h3>Set Parameters</h3>
              <p>Define your risk tolerance and investment goals</p>
            </div>
            <div class="step">
              <div class="step-number">03</div>
              <h3>Start Trading</h3>
              <p>Let our AI models handle the rest with full transparency</p>
            </div>
          </div>
        </section>

        <section id="about" class="about">
          <div class="section-header">
            <div class="section-tag">About</div>
            <h2>The <span class="gradient-text">Project</span></h2>
          </div>
          <div class="about-content">
            <div class="about-text">
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
              <button class="cta-btn primary" @click=${this.onLogin}>Access Dashboard</button>
            </div>
            <div class="about-image">
              <div class="tech-stack">
                <div class="tech">Neural Networks</div>
                <div class="tech">Blockchain</div>
                <div class="tech">Internet Computer</div>
                <div class="tech">Motoko</div>
                <div class="tech">Transformers</div>
              </div>
            </div>
          </div>
        </section>

        <footer class="landing-footer">
          <div class="footer-top">
            <div class="footer-brand">
              <h2>OnChain<span class="accent">AI</span></h2>
              <p>AI-powered cryptocurrency trading on the Internet Computer</p>
            </div>
            <div class="footer-links-container">
              <div class="footer-links-column">
                <h3>Product</h3>
                <a href="#features">Features</a>
                <a href="#about">About</a>
                <a href="#">Roadmap</a>
              </div>
              <div class="footer-links-column">
                <h3>Resources</h3>
                <a href="#">Documentation</a>
                <a href="#">API</a>
                <a href="https://github.com/ichetanmittal/onchain-ai-trading-agent" target="_blank">GitHub</a>
              </div>
              <div class="footer-links-column">
                <h3>Legal</h3>
                <a href="#">Privacy Policy</a>
                <a href="#">Terms of Service</a>
                <a href="#">Cookie Policy</a>
              </div>
            </div>
          </div>
          <div class="footer-bottom">
            <p>&copy; 2025 OnChain AI Trading. All rights reserved.</p>
            <div class="social-links">
              <a href="#" aria-label="Twitter">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M23 3.01006C22.0424 3.68553 20.9821 4.20217 19.86 4.54006C19.2577 3.84757 18.4573 3.35675 17.567 3.13398C16.6767 2.91122 15.7395 2.96725 14.8821 3.29451C14.0247 3.62177 13.2884 4.20446 12.773 4.96377C12.2575 5.72309 11.9877 6.62239 12 7.54006V8.54006C10.2426 8.58562 8.50127 8.19587 6.93101 7.4055C5.36074 6.61513 4.01032 5.44869 3 4.01006C3 4.01006 -1 13.0101 8 17.0101C5.94053 18.408 3.48716 19.109 1 19.0101C10 24.0101 21 19.0101 21 7.51006C20.9991 7.23151 20.9723 6.95365 20.92 6.68006C21.9406 5.67355 22.6608 4.40277 23 3.01006Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </a>
              <a href="#" aria-label="GitHub">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 19C4.7 20.4 4.7 16.5 3 16M15 21V17.5C15 16.5 15.1 16.1 14.5 15.5C17.3 15.2 20 14.1 20 9.49995C19.9988 8.30492 19.5325 7.15726 18.7 6.29995C19.0905 5.26192 19.0545 4.11158 18.6 3.09995C18.6 3.09995 17.5 2.79995 15.1 4.39995C13.0672 3.87054 10.9328 3.87054 8.9 4.39995C6.5 2.79995 5.4 3.09995 5.4 3.09995C4.94548 4.11158 4.90953 5.26192 5.3 6.29995C4.46745 7.15726 4.00122 8.30492 4 9.49995C4 14.1 6.7 15.2 9.5 15.5C8.9 16.1 8.9 16.7 9 17.5V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </a>
              <a href="#" aria-label="Discord">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 11.5C9 12.3284 8.55228 13 8 13C7.44772 13 7 12.3284 7 11.5C7 10.6716 7.44772 10 8 10C8.55228 10 9 10.6716 9 11.5Z" fill="currentColor"/>
                  <path d="M17 11.5C17 12.3284 16.5523 13 16 13C15.4477 13 15 12.3284 15 11.5C15 10.6716 15.4477 10 16 10C16.5523 10 17 10.6716 17 11.5Z" fill="currentColor"/>
                  <path d="M20.6179 5.97C18.6996 5.01 16.6763 4.38 14.5596 4C14.2929 4.48 14.0263 4.96 13.7596 5.44C11.4929 5.08 9.17961 5.08 6.91294 5.44C6.64627 4.96 6.37961 4.48 6.11294 4C3.99627 4.38 1.97294 5.01 0.0546046 5.97C0.0546046 5.97 -1.33873 10.88 0.916271 15.76C2.65627 17.04 4.91294 18.1 7.16961 18.76C7.70294 18.08 8.17961 17.36 8.59294 16.6C7.83294 16.32 7.10627 15.96 6.41294 15.52C6.67961 15.32 6.93294 15.12 7.17294 14.92C9.77294 16.12 12.7063 16.12 15.2729 14.92C15.5129 15.12 15.7663 15.32 16.0329 15.52C15.3396 15.96 14.6129 16.32 13.8529 16.6C14.2663 17.36 14.7429 18.08 15.2763 18.76C17.5329 18.1 19.7896 17.04 21.5296 15.76C24.1063 10.04 22.1729 6.04 20.6179 5.97ZM7.44627 13.6C6.41294 13.6 5.57294 12.64 5.57294 11.48C5.57294 10.32 6.39294 9.36 7.44627 9.36C8.49961 9.36 9.33961 10.32 9.31961 11.48C9.31961 12.64 8.49961 13.6 7.44627 13.6ZM14.2129 13.6C13.1796 13.6 12.3396 12.64 12.3396 11.48C12.3396 10.32 13.1596 9.36 14.2129 9.36C15.2663 9.36 16.1063 10.32 16.0863 11.48C16.0863 12.64 15.2663 13.6 14.2129 13.6Z" fill="currentColor"/>
                </svg>
              </a>
            </div>
          </div>
        </footer>
      </div>
    `;
  }
}

export default LandingPage;
