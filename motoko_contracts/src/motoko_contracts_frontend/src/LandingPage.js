import { html } from 'lit-html';
import './LandingPage.css';
import authService from './auth';

class LandingPage {
  constructor(onLogin) {
    console.log("[LandingPage] Initializing LandingPage component");
    this.onLogin = onLogin;
    this.isLoggingIn = false;
    this.error = null;
  }

  async handleLogin() {
    console.log("[LandingPage] Handling login with Internet Identity");
    this.isLoggingIn = true;
    this.error = null;
    this.render();
    
    try {
      console.log("[LandingPage] Calling authService.login()");
      const success = await authService.login();
      console.log("[LandingPage] Login result:", success);
      
      if (!success) {
        console.error("[LandingPage] Login failed");
        this.error = "Login failed. Please try again.";
      }
      
      this.isLoggingIn = false;
      this.render();
    } catch (error) {
      console.error("[LandingPage] Login error:", error);
      this.error = error.message || "An error occurred during login";
      this.isLoggingIn = false;
      this.render();
    }
  }

  render() {
    console.log("[LandingPage] Rendering LandingPage component");
    return html`
      <div class="landing-container">
        <nav class="landing-nav">
          <div class="logo">
            <h1>IC<span class="accent">INDEX</span></h1>
          </div>
          <div class="nav-links">
            <a href="#features">Features</a>
            <a href="#about">About</a>
            <a href="https://github.com/ichetanmittal/onchain-ai-trading-agent" target="_blank">GitHub</a>
            <button 
              @click=${() => this.handleLogin()} 
              ?disabled=${this.isLoggingIn}
              class="login-btn"
            >
              ${this.isLoggingIn ? 'Connecting to Internet Identity...' : 'Connect Identity'}
            </button>
          </div>
          <button class="mobile-menu-btn">
            <span></span>
            <span></span>
            <span></span>
          </button>
        </nav>

        ${this.error ? html`<div class="error-message">${this.error}</div>` : ''}

        <section class="hero">
          <div class="hero-content">
            <div class="badge">Powered by Internet Computer</div>
            <h1>AI-Powered <span class="gradient-text">Crypto Trading</span> for the Future</h1>
            <p>Harness the power of artificial intelligence and blockchain technology for smarter, more transparent cryptocurrency trading decisions</p>
            <div class="cta-buttons">
              <button 
                @click=${() => this.handleLogin()} 
                ?disabled=${this.isLoggingIn}
                class="cta-btn primary"
              >
                ${this.isLoggingIn ? 'Connecting to Internet Identity...' : 'Connect with Internet Identity'}
              </button>
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
              <h3>Connect Identity</h3>
              <p>Securely authenticate with Internet Identity on the Internet Computer</p>
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
              <button 
                @click=${() => this.handleLogin()} 
                ?disabled=${this.isLoggingIn}
                class="cta-btn primary"
              >
                ${this.isLoggingIn ? 'Connecting to Internet Identity...' : 'Connect with Internet Identity'}
              </button>
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
              <h2>IC<span class="accent">INDEX</span></h2>
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
                  <path d="M23 3.01006C22.0424 3.68553 20.9821 4.20217 19.86 4.54006C19.2577 3.84757 18.4573 3.35675 17.567 3.13398C16.6767 2.91122 15.7395 2.96725 14.8821 3.29451C14.0247 3.62177 13.2884 4.20446 12.773 4.96377C12.2575 5.72309 11.9877 6.62239 12 7.54006V8.54006C10.2426 8.58562 8.50127 8.19587 6.93101 7.4055C5.36074 6.61513 4.01032 5.44869 3 4.01006C3 4.01006 -1 13.0101 8 17.0101C5.94053 18.408 3.48716 19.109 1 19.0101C10 24.0101 21 19.0101 21 7.51006C20.9991 7.23151 20.9723 6.95365 20.92 6.68006C21.9406 5.67355 22.6608 4.40277 23 3.01006Z" stroke="currentColor" stroke-width="2"/>
                </svg>
              </a>
              <a href="#" aria-label="GitHub">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 19C4 20.5 4 16.5 2 16M16 22V18.13C16.0375 17.6532 15.9731 17.1738 15.811 16.7238C15.6489 16.2738 15.3929 15.8634 15.06 15.52C18.2 15.17 21.5 13.98 21.5 8.52C21.4997 7.12383 20.9627 5.7812 20 4.77C20.4559 3.54851 20.4236 2.19835 19.91 0.999999C19.91 0.999999 18.73 0.649999 16 2.48C13.708 1.85882 11.292 1.85882 9 2.48C6.27 0.649999 5.09 0.999999 5.09 0.999999C4.57638 2.19835 4.54414 3.54851 5 4.77C4.03013 5.7887 3.49252 7.14346 3.5 8.55C3.5 13.97 6.8 15.16 9.94 15.55C9.611 15.89 9.35726 16.2954 9.19531 16.7399C9.03335 17.1844 8.96681 17.6581 9 18.13V22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </a>
              <a href="#" aria-label="Discord">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 11.5C9 12.3284 8.32843 13 7.5 13C6.67157 13 6 12.3284 6 11.5C6 10.6716 6.67157 10 7.5 10C8.32843 10 9 10.6716 9 11.5Z" fill="currentColor"/>
                  <path d="M16.5 13C17.3284 13 18 12.3284 18 11.5C18 10.6716 17.3284 10 16.5 10C15.6716 10 15 10.6716 15 11.5C15 12.3284 15.6716 13 16.5 13Z" fill="currentColor"/>
                  <path d="M18 6C15.5 4 12 4 9 6M9 6C6.5 8 6.5 11 6 16C6 16 7 18 12 18C17 18 18 16 18 16C17.5 11 17.5 8 15 6M9 6L10 4M15 6L14 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
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
