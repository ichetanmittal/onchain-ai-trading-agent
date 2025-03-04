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
      monteCarloSimulationDays: 30
    };
    console.log("[Dashboard] Initializing state:", this.state);
    this.fetchData();
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
      const result = await actor.rebalance();
      console.log("[Dashboard] Standard rebalance result:", result);
      alert("Portfolio rebalanced!\n\n" + result);
      this.fetchData(); // Refresh data to show updated portfolio
    } catch (error) {
      console.error("[Dashboard] Error rebalancing:", error);
      alert("Error rebalancing: " + error.message);
    }
  };
  
  fetchData = async () => {
    console.log("[Dashboard] Fetching data");
    try {
      // Fetch predictions and portfolio data from backend
      console.log("[Dashboard] Fetching data from backend...");
      const actor = authService.getActor();
      
      const predictions = await actor.getPredictions();
      console.log("[Dashboard] Predictions:", predictions);
      
      const portfolio = await actor.getPortfolio();
      console.log("[Dashboard] Portfolio:", portfolio);
      
      const rebalanceResult = await actor.getRebalanceResult();
      console.log("[Dashboard] Rebalance result:", rebalanceResult);
      
      const metrics = await actor.getMetrics();
      console.log("[Dashboard] Metrics:", metrics);
      
      // Convert values to JavaScript numbers to avoid type conversion issues
      const btcPrediction = typeof predictions.btc === 'number' ? predictions.btc : Number(predictions.btc);
      const ethPrediction = typeof predictions.eth === 'number' ? predictions.eth : Number(predictions.eth);
      
      const processedPortfolio = {
        btc: typeof portfolio.btc === 'number' ? portfolio.btc : Number(portfolio.btc),
        eth: typeof portfolio.eth === 'number' ? portfolio.eth : Number(portfolio.eth),
        totalValue: typeof portfolio.totalValue === 'number' ? portfolio.totalValue : Number(portfolio.totalValue),
        performance: typeof portfolio.performance === 'number' ? portfolio.performance : Number(portfolio.performance),
        lastRebalanceTime: portfolio.lastRebalanceTime
      };
      
      const processedMetrics = {
        sharpeRatio: typeof metrics.sharpeRatio === 'number' ? metrics.sharpeRatio : Number(metrics.sharpeRatio),
        volatility: typeof metrics.volatility === 'number' ? metrics.volatility : Number(metrics.volatility),
        var95: typeof metrics.var95 === 'number' ? metrics.var95 : Number(metrics.var95),
        maxDrawdown: typeof metrics.maxDrawdown === 'number' ? metrics.maxDrawdown : Number(metrics.maxDrawdown),
        updated: typeof metrics.updated === 'boolean' ? metrics.updated : Boolean(metrics.updated),
        monteCarloSimulated: typeof metrics.monteCarloSimulated === 'boolean' ? metrics.monteCarloSimulated : Boolean(metrics.monteCarloSimulated)
      };
      
      this.state = {
        btcPrediction,
        ethPrediction,
        portfolio: processedPortfolio,
        rebalanceResult,
        metrics: processedMetrics
      };
      console.log("[Dashboard] Updated state:", this.state);
      this.render();
    } catch (error) {
      console.error("[Dashboard] Error fetching data:", error);
    }
  };

  render() {
    console.log("[Dashboard] Rendering Dashboard component");
    const { btcPrediction, ethPrediction, portfolio, rebalanceResult, metrics, randomnessEnabled, monteCarloSimulationDays } = this.state;
    
    const dashboardTemplate = html`
      <main class="container">
        <header class="dashboard-header">
          <h1>AI Trading Bot Dashboard</h1>
          <div class="user-info">
            ${this.principal ? html`<span class="principal-id">Principal ID: ${this.principal.substring(0, 5)}...${this.principal.substring(this.principal.length - 5)}</span>` : ''}
            <button class="logout-btn" @click=${this.onLogout}>Logout</button>
          </div>
        </header>
        
        <section class="predictions-section">
          <h2>Price Predictions</h2>
          <div class="predictions-grid">
            <div class="prediction-card">
              <h3>BTC Prediction</h3>
              <p class="price">${btcPrediction !== null && btcPrediction !== undefined ? btcPrediction.toFixed(6) : 'Loading...'}</p>
            </div>
            <div class="prediction-card">
              <h3>ETH Prediction</h3>
              <p class="price">${ethPrediction !== null && ethPrediction !== undefined ? ethPrediction.toFixed(6) : 'Loading...'}</p>
            </div>
          </div>
        </section>

        <section class="portfolio-section">
          <h2>Current Portfolio</h2>
          ${portfolio ? html`
            <div class="portfolio-grid">
              <div class="portfolio-card">
                <h3>BTC Holdings</h3>
                <p class="amount">${portfolio.btc ? portfolio.btc.toFixed(2) : '0.00'} USDT</p>
                <p class="allocation">${portfolio.totalValue ? ((portfolio.btc / portfolio.totalValue) * 100).toFixed(2) : '0.00'}%</p>
              </div>
              <div class="portfolio-card">
                <h3>ETH Holdings</h3>
                <p class="amount">${portfolio.eth ? portfolio.eth.toFixed(2) : '0.00'} USDT</p>
                <p class="allocation">${portfolio.totalValue ? ((portfolio.eth / portfolio.totalValue) * 100).toFixed(2) : '0.00'}%</p>
              </div>
            </div>
            <div class="portfolio-metrics">
              <h3>Portfolio Metrics</h3>
              <p>Total Value: ${portfolio.totalValue ? portfolio.totalValue.toFixed(2) : '0.00'} USDT</p>
              <p>Performance: ${portfolio.performance ? (portfolio.performance * 100).toFixed(2) : '0.00'}%</p>
              <p>Last Rebalance: ${portfolio.lastRebalanceTime ? new Date(Number(portfolio.lastRebalanceTime) / 1000000).toLocaleString() : 'Never'}</p>
            </div>
          ` : html`<p>Loading portfolio data...</p>`}
        </section>

        <section class="rebalance-section">
          <h2>Latest Rebalance</h2>
          ${rebalanceResult ? html`<p>${rebalanceResult}</p>` : html`<p>No rebalance data available</p>`}
        </section>

        <section class="metrics-section">
          <h2>Performance Metrics ${metrics && metrics.monteCarloSimulated ? html`<span class="monte-carlo-badge">Monte Carlo Simulated</span>` : ''}</h2>
          ${metrics ? html`
            <div class="metrics-grid">
              <div class="metric-card">
                <h3>Sharpe Ratio</h3>
                <p class="metric-value">${metrics.sharpeRatio.toFixed(2)}</p>
              </div>
              <div class="metric-card">
                <h3>Volatility</h3>
                <p class="metric-value">${(metrics.volatility * 100).toFixed(2)}%</p>
              </div>
              <div class="metric-card">
                <h3>Value at Risk (95%)</h3>
                <p class="metric-value">${(metrics.var95 * 100).toFixed(2)}%</p>
              </div>
              <div class="metric-card">
                <h3>Max Drawdown</h3>
                <p class="metric-value">${(metrics.maxDrawdown * 100).toFixed(2)}%</p>
              </div>
            </div>
          ` : html`<p>Loading metrics data...</p>`}
        </section>
        
        <section class="actions-section">
          <h2>Portfolio Actions</h2>
          <div class="action-buttons">
            <button class="action-btn" @click=${this.rebalanceStandard}>Standard Rebalance</button>
            <div class="randomness-controls">
              <button class="action-btn ${randomnessEnabled ? 'active' : ''}" @click=${this.toggleRandomness}>
                ${randomnessEnabled ? 'Randomness Enabled' : 'Enable Randomness'}
              </button>
              ${randomnessEnabled ? html`
                <button class="action-btn randomness-btn" @click=${this.getRandomness}>Get Randomness</button>
                <button class="action-btn randomness-btn" @click=${this.rebalanceWithRandomness}>Rebalance with Randomness</button>
              ` : ''}
            </div>
          </div>
        </section>
        
        <section class="simulation-section">
          <h2>Monte Carlo Simulation</h2>
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
              />
            </div>
            <button class="action-btn" @click=${this.runMonteCarloSimulation}>Run Simulation</button>
          </div>
        </section>
      </main>
    `;
    
    return dashboardTemplate;
  }
}

export default Dashboard;
