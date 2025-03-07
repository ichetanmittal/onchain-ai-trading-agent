import { html, render } from 'lit-html';
import { motoko_contracts_backend } from 'declarations/motoko_contracts_backend';
import authService from './auth';
import './App.css';

class Dashboard {
  constructor(onLogout) {
    console.log("[Dashboard] Initializing Dashboard component");
    this.onLogout = onLogout;
    this.principal = null;
    this.state = {
      btcPrediction: null,
      ethPrediction: null,
      portfolio: null,
      rebalanceResult: null,
      metrics: null,
      randomnessEnabled: false,
      monteCarloSimulationDays: 30,
      btcAddress: null,
      ckbtcBalance: 0,
      btcNetwork: 'regtest'
    };
    console.log("[Dashboard] Initializing state:", this.state);
    
    // Only fetch data if already authenticated
    if (authService.getIsAuthenticated()) {
      this.fetchData();
    }
  }

  toggleRandomness = () => {
    console.log("[Dashboard] Toggling randomness");
    this.setState({ randomnessEnabled: !this.state.randomnessEnabled });
  };
  
  setState = (newState) => {
    console.log("[Dashboard] Updating state:", newState);
    this.state = { ...this.state, ...newState };
    this.render();
  };
  
  updateMonteCarloSimulationDays = (event) => {
    console.log("[Dashboard] Updating Monte Carlo simulation days:", event.target.value);
    const days = parseInt(event.target.value, 10);
    if (!isNaN(days) && days > 0 && days <= 365) {
      this.setState({ monteCarloSimulationDays: days });
    }
  };
  
  getRandomness = async () => {
    console.log("[Dashboard] Getting randomness");
    try {
      const actor = authService.getActor();
      if (!actor) {
        throw new Error("Not authenticated");
      }
      const random = await actor.getRandomness();
      console.log("[Dashboard] Received randomness:", random);
      alert("Randomness received from Internet Computer!");
    } catch (error) {
      console.error("[Dashboard] Error getting randomness:", error);
      alert("Error getting randomness: " + error.message);
    }
  };
  
  runMonteCarloSimulation = async () => {
    console.log("[Dashboard] Running Monte Carlo simulation");
    try {
      const days = this.state.monteCarloSimulationDays;
      console.log("[Dashboard] Running simulation for", days, "days");
      
      const actor = authService.getActor();
      if (!actor) {
        throw new Error("Not authenticated");
      }
      const simulationResults = await actor.runMonteCarloSimulation(days);
      console.log("[Dashboard] Simulation results:", simulationResults);
      
      alert(`Monte Carlo simulation completed for ${days} days!\n\nResults:\n` +
            `Simulated Sharpe Ratio: ${simulationResults.simulatedSharpeRatio.toFixed(2)}\n` +
            `Simulated Volatility: ${(simulationResults.simulatedVolatility * 100).toFixed(2)}%\n` +
            `Simulated VaR (95%): ${(simulationResults.simulatedVar95 * 100).toFixed(2)}%\n` +
            `Simulated Max Drawdown: ${(simulationResults.simulatedMaxDrawdown * 100).toFixed(2)}%`);
      
      this.fetchData(); // Refresh data to show updated metrics
    } catch (error) {
      console.error("[Dashboard] Error running Monte Carlo simulation:", error);
      alert("Error running Monte Carlo simulation: " + error.message);
    }
  };
  
  rebalanceWithRandomness = async () => {
    console.log("[Dashboard] Rebalancing with randomness");
    try {
      console.log("[Dashboard] Rebalancing portfolio with randomness...");
      const actor = authService.getActor();
      if (!actor) {
        throw new Error("Not authenticated");
      }
      const result = await actor.rebalanceWithRandomness();
      console.log("[Dashboard] Rebalance with randomness result:", result);
      alert("Portfolio rebalanced with randomness!\n\n" + result);
      this.fetchData(); // Refresh data to show updated portfolio
    } catch (error) {
      console.error("[Dashboard] Error rebalancing with randomness:", error);
      alert("Error rebalancing with randomness: " + error.message);
    }
  };
  
  rebalanceStandard = async () => {
    console.log("[Dashboard] Rebalancing standard");
    try {
      console.log("[Dashboard] Rebalancing portfolio (standard)...");
      const actor = authService.getActor();
      if (!actor) {
        throw new Error("Not authenticated");
      }
      const result = await actor.rebalance();
      console.log("[Dashboard] Standard rebalance result:", result);
      alert("Portfolio rebalanced!\n\n" + result);
      this.fetchData(); // Refresh data to show updated portfolio
    } catch (error) {
      console.error("[Dashboard] Error rebalancing:", error);
      alert("Error rebalancing: " + error.message);
    }
  };
  
  // Generate a Bitcoin address using Chain Key Cryptography
  generateBitcoinAddress = async () => {
    console.log("[Dashboard] Generating Bitcoin address");
    try {
      const actor = authService.getActor();
      if (!actor) {
        throw new Error("Not authenticated");
      }
      
      // Convert network string to variant
      const network = { [this.state.btcNetwork]: null };
      const address = await actor.get_p2pkh_address(network);
      console.log("[Dashboard] Generated Bitcoin address:", address);
      
      this.setState({ btcAddress: address });
      alert(`Bitcoin address generated: ${address}\n\nYou can use this address to deposit Bitcoin that will be converted to ckBTC.`);
      
      // Refresh data to show updated portfolio
      this.fetchData();
    } catch (error) {
      console.error("[Dashboard] Error generating Bitcoin address:", error);
      alert("Error generating Bitcoin address: " + error.message);
    }
  };
  
  // Get Bitcoin balance
  getBitcoinBalance = async () => {
    console.log("[Dashboard] Getting Bitcoin balance");
    try {
      const actor = authService.getActor();
      if (!actor) {
        throw new Error("Not authenticated");
      }
      
      // Convert network string to variant
      const network = { [this.state.btcNetwork]: null };
      const balance = await actor.get_bitcoin_balance(network, 0);
      console.log("[Dashboard] Bitcoin balance:", balance);
      
      // Convert satoshis to BTC (1 BTC = 100,000,000 satoshis)
      const btcBalance = Number(balance) / 100000000;
      
      // Update ckBTC balance in the portfolio
      await actor.update_ckbtc_balance(btcBalance);
      
      alert(`Bitcoin balance: ${btcBalance} BTC\n\nThis balance has been converted to ckBTC in your portfolio.`);
      
      // Refresh data to show updated portfolio
      this.fetchData();
    } catch (error) {
      console.error("[Dashboard] Error getting Bitcoin balance:", error);
      alert("Error getting Bitcoin balance: " + error.message);
    }
  };
  
  // Change Bitcoin network
  changeBitcoinNetwork = (event) => {
    console.log("[Dashboard] Changing Bitcoin network to:", event.target.value);
    this.setState({ btcNetwork: event.target.value });
  };
  
  fetchData = async () => {
    console.log("[Dashboard] Fetching data");
    try {
      // Fetch predictions and portfolio data from backend
      console.log("[Dashboard] Fetching data from backend...");
      const actor = authService.getActor();
      
      if (!actor) {
        console.log("[Dashboard] Not authenticated yet, skipping data fetch");
        return;
      }
      
      const predictions = await actor.getPredictions();
      console.log("[Dashboard] Predictions:", predictions);
      
      const portfolio = await actor.getPortfolio();
      console.log("[Dashboard] Portfolio:", portfolio);
      
      const rebalanceResult = await actor.getRebalanceResult();
      console.log("[Dashboard] Rebalance result:", rebalanceResult);
      
      const metrics = await actor.getMetrics();
      console.log("[Dashboard] Metrics:", metrics);
      
      // Fetch Bitcoin address if available
      const btcAddress = await actor.get_bitcoin_address();
      console.log("[Dashboard] Bitcoin address:", btcAddress);
      
      // Convert values to JavaScript numbers to avoid type conversion issues
      const btcPrediction = typeof predictions.btc === 'number' ? predictions.btc : Number(predictions.btc);
      const ethPrediction = typeof predictions.eth === 'number' ? predictions.eth : Number(predictions.eth);
      
      const processedPortfolio = {
        btc: typeof portfolio.btc === 'number' ? portfolio.btc : Number(portfolio.btc),
        eth: typeof portfolio.eth === 'number' ? portfolio.eth : Number(portfolio.eth),
        ckbtc: typeof portfolio.ckbtc === 'number' ? portfolio.ckbtc : Number(portfolio.ckbtc),
        cketh: typeof portfolio.cketh === 'number' ? portfolio.cketh : Number(portfolio.cketh),
        totalValue: typeof portfolio.totalValue === 'number' ? portfolio.totalValue : Number(portfolio.totalValue),
        performance: typeof portfolio.performance === 'number' ? portfolio.performance : Number(portfolio.performance),
        lastRebalanceTime: portfolio.lastRebalanceTime,
        btcAddress: portfolio.btcAddress,
        ethAddress: portfolio.ethAddress
      };
      
      const processedMetrics = {
        sharpeRatio: typeof metrics.sharpeRatio === 'number' ? metrics.sharpeRatio : Number(metrics.sharpeRatio),
        volatility: typeof metrics.volatility === 'number' ? metrics.volatility : Number(metrics.volatility),
        var95: typeof metrics.var95 === 'number' ? metrics.var95 : Number(metrics.var95),
        maxDrawdown: typeof metrics.maxDrawdown === 'number' ? metrics.maxDrawdown : Number(metrics.maxDrawdown),
        updated: typeof metrics.updated === 'boolean' ? metrics.updated : Boolean(metrics.updated),
        monteCarloSimulated: typeof metrics.monteCarloSimulated === 'boolean' ? metrics.monteCarloSimulated : Boolean(metrics.monteCarloSimulated)
      };
      
      this.setState({
        btcPrediction,
        ethPrediction,
        portfolio: processedPortfolio,
        rebalanceResult,
        metrics: processedMetrics,
        btcAddress: btcAddress && btcAddress.length > 0 ? btcAddress[0] : null,
        ckbtcBalance: processedPortfolio.ckbtc
      });
    } catch (error) {
      console.error("[Dashboard] Error fetching data:", error);
    }
  };

  render() {
    console.log("[Dashboard] Rendering Dashboard component");
    const { btcPrediction, ethPrediction, portfolio, rebalanceResult, metrics, randomnessEnabled, monteCarloSimulationDays, btcAddress, ckbtcBalance, btcNetwork } = this.state;
    
    const dashboardTemplate = html`
      <main class="dashboard-container">
        <nav class="landing-nav dashboard-nav">
          <div class="logo">
            <h1>IC<span class="accent">INDEX</span></h1>
          </div>
          <div class="nav-links">
            <a href="#predictions">Predictions</a>
            <a href="#portfolio">Portfolio</a>
            <a href="#metrics">Metrics</a>
            <a href="#randomness">Actions</a>
            ${this.principal ? html`<span class="principal-id">Principal: ${this.principal.substring(0, 5)}...${this.principal.substring(this.principal.length - 5)}</span>` : ''}
            <button class="login-btn logout-btn" @click=${this.onLogout}>Logout</button>
          </div>
        </nav>
        
        <section id="predictions" class="predictions-section">
          <div class="section-header">
            <div class="section-tag">AI Analysis</div>
            <h2>Price <span class="gradient-text">Predictions</span></h2>
          </div>
          <div class="predictions-grid">
            <div class="prediction-card">
              <div class="feature-icon ai-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M7 14.5L10 11.5L13 14.5L17 10.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <h3>BTC Prediction</h3>
              <p class="price">${btcPrediction !== null && btcPrediction !== undefined ? btcPrediction.toFixed(6) : 'Loading...'}</p>
              <p class="card-description">AI-powered price prediction for Bitcoin</p>
            </div>
            <div class="prediction-card">
              <div class="feature-icon ai-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M7 14.5L10 11.5L13 14.5L17 10.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <h3>ETH Prediction</h3>
              <p class="price">${ethPrediction !== null && ethPrediction !== undefined ? ethPrediction.toFixed(6) : 'Loading...'}</p>
              <p class="card-description">AI-powered price prediction for Ethereum</p>
            </div>
          </div>
        </section>

        <section id="portfolio" class="portfolio-section">
          <div class="section-header">
            <div class="section-tag">Portfolio</div>
            <h2>Current <span class="gradient-text">Portfolio</span></h2>
          </div>
          ${portfolio ? html`
            <div class="portfolio-grid">
              <div class="portfolio-card">
                <div class="feature-icon blockchain-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M7 10L12 4L17 10L12 16L7 10Z" stroke="currentColor" stroke-width="2"/>
                    <path d="M12 16L7 20L12 24L17 20L12 16Z" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
                <h3>BTC Holdings</h3>
                <p class="amount">${portfolio.btc ? portfolio.btc.toFixed(2) : '0.00'} USDT</p>
                <p class="allocation">${portfolio.totalValue ? ((portfolio.btc / portfolio.totalValue) * 100).toFixed(2) : '0.00'}%</p>
                <p class="card-description">Your current Bitcoin allocation</p>
              </div>
              <div class="portfolio-card">
                <div class="feature-icon blockchain-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M7 10L12 4L17 10L12 16L7 10Z" stroke="currentColor" stroke-width="2"/>
                    <path d="M12 16L7 20L12 24L17 20L12 16Z" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
                <h3>ETH Holdings</h3>
                <p class="amount">${portfolio.eth ? portfolio.eth.toFixed(2) : '0.00'} USDT</p>
                <p class="allocation">${portfolio.totalValue ? ((portfolio.eth / portfolio.totalValue) * 100).toFixed(2) : '0.00'}%</p>
                <p class="card-description">Your current Ethereum allocation</p>
              </div>
            </div>
            <div class="portfolio-metrics">
              <div class="section-tag">Summary</div>
              <h3>Portfolio Overview</h3>
              <div class="hero-stats">
                <div class="stat">
                  <span class="stat-value">${portfolio.totalValue ? portfolio.totalValue.toFixed(2) : '0.00'}</span>
                  <span class="stat-label">Total Value (USDT)</span>
                </div>
                <div class="stat">
                  <span class="stat-value">${portfolio.performance ? (portfolio.performance * 100).toFixed(2) : '0.00'}%</span>
                  <span class="stat-label">Performance</span>
                </div>
                <div class="stat">
                  <span class="stat-value">${portfolio.lastRebalanceTime ? new Date(Number(portfolio.lastRebalanceTime) / 1000000).toLocaleString() : 'Never'}</span>
                  <span class="stat-label">Last Rebalance</span>
                </div>
              </div>
            </div>
          ` : html`<p>Loading portfolio data...</p>`}
        </section>

        <section id="chainkey" class="chainkey-section">
          <div class="section-header">
            <div class="section-tag">Chain Key</div>
            <h2>ckBTC <span class="gradient-text">Integration</span></h2>
          </div>
          <div class="chainkey-grid">
            <div class="chainkey-card">
              <div class="feature-icon blockchain-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 4H5C4.44772 4 4 4.44772 4 5V9C4 9.55228 4.44772 10 5 10H9C9.55228 10 10 9.55228 10 9V5C10 4.44772 9.55228 4 9 4Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M19 4H15C14.4477 4 14 4.44772 14 5V9C14 9.55228 14.4477 10 15 10H19C19.5523 10 20 9.55228 20 9V5C20 4.44772 19.5523 4 19 4Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M9 14H5C4.44772 14 4 14.4477 4 15V19C4 19.5523 4.44772 20 5 20H9C9.55228 20 10 19.5523 10 19V15C10 14.4477 9.55228 14 9 14Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M19 14H15C14.4477 14 14 14.4477 14 15V19C14 19.5523 14.4477 20 15 20H19C19.5523 20 20 19.5523 20 19V15C20 14.4477 19.5523 14 19 14Z" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <h3>Bitcoin Address</h3>
              ${btcAddress ? html`
                <p class="address">${btcAddress}</p>
                <p class="card-description">Your Bitcoin address for deposits</p>
              ` : html`
                <p class="card-description">Generate a Bitcoin address to deposit BTC</p>
                <button class="action-btn" @click=${this.generateBitcoinAddress}>Generate Address</button>
              `}
            </div>
            <div class="chainkey-card">
              <div class="feature-icon blockchain-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M15 8.5C14.315 7.81501 13.1087 7.33855 12 7.30872M9 8.5C9.685 7.81501 10.8913 7.33855 12 7.30872M12 7.30872V7M12 17V12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <h3>ckBTC Balance</h3>
              <p class="amount">${ckbtcBalance ? ckbtcBalance.toFixed(8) : '0.00000000'} ckBTC</p>
              <p class="card-description">Your current ckBTC balance</p>
              <button class="action-btn" @click=${this.getBitcoinBalance}>Check Balance</button>
            </div>
          </div>
          <div class="chainkey-controls">
            <div class="section-tag">Network</div>
            <div class="network-selector">
              <label>
                <input type="radio" name="btcNetwork" value="regtest" ?checked=${btcNetwork === 'regtest'} @change=${this.changeBitcoinNetwork} />
                Regtest (Local)
              </label>
              <label>
                <input type="radio" name="btcNetwork" value="testnet" ?checked=${btcNetwork === 'testnet'} @change=${this.changeBitcoinNetwork} />
                Testnet
              </label>
              <label>
                <input type="radio" name="btcNetwork" value="mainnet" ?checked=${btcNetwork === 'mainnet'} @change=${this.changeBitcoinNetwork} />
                Mainnet
              </label>
            </div>
          </div>
        </section>

        <section id="rebalance" class="rebalance-section">
          <div class="section-header">
            <div class="section-tag">Rebalance</div>
            <h2>Latest <span class="gradient-text">Rebalance</span></h2>
          </div>
          ${rebalanceResult ? html`
            <div class="rebalance-content">
              <div class="feature-icon security-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 22C12 22 20 18 20 12V5L12 2L4 5V12C4 18 12 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M9 12L11 14L15 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <p class="rebalance-result">${rebalanceResult}</p>
            </div>
          ` : html`
            <div class="rebalance-content">
              <div class="feature-icon security-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 22C12 22 20 18 20 12V5L12 2L4 5V12C4 18 12 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                  <path d="M9 12L11 14L15 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <p>No rebalance data available yet. Use the actions below to rebalance your portfolio.</p>
            </div>
          `}
        </section>

        <section id="metrics" class="metrics-section">
          <div class="section-header">
            <div class="section-tag">Performance</div>
            <h2>Portfolio <span class="gradient-text">Metrics</span> ${metrics && metrics.monteCarloSimulated ? html`<span class="monte-carlo-badge">Monte Carlo Simulated</span>` : ''}</h2>
          </div>
          ${metrics ? html`
            <div class="metrics-grid">
              <div class="metric-card">
                <div class="feature-icon risk-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                    <path d="M12 8V12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    <path d="M12 16H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </div>
                <h3>Sharpe Ratio</h3>
                <p class="metric-value">${metrics.sharpeRatio.toFixed(2)}</p>
                <p class="card-description">Risk-adjusted return measure</p>
              </div>
              <div class="metric-card">
                <div class="feature-icon risk-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                    <path d="M8 12L12 16L16 12L12 8L8 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <h3>Volatility</h3>
                <p class="metric-value">${(metrics.volatility * 100).toFixed(2)}%</p>
                <p class="card-description">Portfolio price fluctuation</p>
              </div>
              <div class="metric-card">
                <div class="feature-icon risk-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                    <path d="M8 15L16 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M8 9H8.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M16 15H16.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <h3>Value at Risk (95%)</h3>
                <p class="metric-value">${(metrics.var95 * 100).toFixed(2)}%</p>
                <p class="card-description">Maximum expected loss</p>
              </div>
              <div class="metric-card">
                <div class="feature-icon risk-icon">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                    <path d="M8 12L12 8L16 12L12 16L8 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <h3>Max Drawdown</h3>
                <p class="metric-value">${(metrics.maxDrawdown * 100).toFixed(2)}%</p>
                <p class="card-description">Largest peak-to-trough decline</p>
              </div>
            </div>
          ` : html`<p>Loading metrics data...</p>`}
        </section>
        
        <section id="actions" class="actions-section">
          <div class="section-header">
            <div class="section-tag">Actions</div>
            <h2>Portfolio <span class="gradient-text">Actions</span></h2>
          </div>
          <div class="action-buttons">
            <button class="cta-btn primary" @click=${this.rebalanceStandard}>Standard Rebalance</button>
            <div class="randomness-controls">
              <button class="cta-btn ${randomnessEnabled ? 'primary' : 'secondary'}" @click=${this.toggleRandomness}>
                ${randomnessEnabled ? 'Randomness Enabled' : 'Enable Randomness'}
              </button>
              ${randomnessEnabled ? html`
                <button class="cta-btn secondary" @click=${this.getRandomness}>Get Randomness</button>
                <button class="cta-btn primary" @click=${this.rebalanceWithRandomness}>Rebalance with Randomness</button>
              ` : ''}
            </div>
          </div>
        </section>
        
        <section class="simulation-section">
          <div class="section-header">
            <div class="section-tag">Simulation</div>
            <h2>Monte Carlo <span class="gradient-text">Simulation</span></h2>
          </div>
          <div class="simulation-controls">
            <div class="days-input">
              <label for="simulation-days">Simulation Days:</label>
              <input 
                type="number" 
                id="simulation-days" 
                min="1" 
                max="365" 
                value="${monteCarloSimulationDays}"
                @input=${this.updateMonteCarloSimulationDays}
                class="simulation-input"
              />
            </div>
            <button class="cta-btn primary" @click=${this.runMonteCarloSimulation}>Run Simulation</button>
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
                <h3>Dashboard</h3>
                <a href="#predictions">Predictions</a>
                <a href="#portfolio">Portfolio</a>
                <a href="#metrics">Metrics</a>
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
      </main>
    `;
    
    // Render the template to the DOM
    const rootElement = document.getElementById('root');
    if (rootElement) {
      render(dashboardTemplate, rootElement);
    }
    
    return dashboardTemplate;
  }
}

export default Dashboard;
