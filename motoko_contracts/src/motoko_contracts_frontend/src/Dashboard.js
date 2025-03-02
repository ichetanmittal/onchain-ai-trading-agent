import { html, render } from 'lit-html';
import { motoko_contracts_backend } from 'declarations/motoko_contracts_backend';
import './App.css';

class Dashboard {
  constructor(onLogout) {
    this.onLogout = onLogout;
    this.state = {
      btcPrediction: null,
      ethPrediction: null,
      portfolio: null,
      rebalanceResult: null,
      metrics: null,
      randomnessEnabled: false,
      monteCarloSimulationDays: 30
    };
    this.fetchData();
  }

  toggleRandomness = () => {
    this.setState({ randomnessEnabled: !this.state.randomnessEnabled });
  };
  
  setState = (newState) => {
    this.state = { ...this.state, ...newState };
    this.render();
  };
  
  updateMonteCarloSimulationDays = (event) => {
    const days = parseInt(event.target.value, 10);
    if (!isNaN(days) && days > 0 && days <= 365) {
      this.setState({ monteCarloSimulationDays: days });
    }
  };
  
  getRandomness = async () => {
    try {
      const random = await motoko_contracts_backend.getRandomness();
      console.log("Received randomness:", random);
      alert("Randomness received from Internet Computer!");
    } catch (error) {
      console.error('Error getting randomness:', error);
      alert("Error getting randomness: " + error.message);
    }
  };
  
  runMonteCarloSimulation = async () => {
    try {
      const days = this.state.monteCarloSimulationDays;
      console.log(`Running Monte Carlo simulation for ${days} days...`);
      
      const simulationResults = await motoko_contracts_backend.runMonteCarloSimulation(days);
      console.log("Simulation results:", simulationResults);
      
      alert(`Monte Carlo simulation completed for ${days} days!\n\nResults:\n` +
            `Simulated Sharpe Ratio: ${simulationResults.simulatedSharpeRatio.toFixed(2)}\n` +
            `Simulated Volatility: ${(simulationResults.simulatedVolatility * 100).toFixed(2)}%\n` +
            `Simulated VaR (95%): ${(simulationResults.simulatedVar95 * 100).toFixed(2)}%\n` +
            `Simulated Max Drawdown: ${(simulationResults.simulatedMaxDrawdown * 100).toFixed(2)}%`);
      
      this.fetchData(); // Refresh data to show updated metrics
    } catch (error) {
      console.error('Error running Monte Carlo simulation:', error);
      alert("Error running Monte Carlo simulation: " + error.message);
    }
  };
  
  rebalanceWithRandomness = async () => {
    try {
      console.log("Rebalancing portfolio with randomness...");
      const result = await motoko_contracts_backend.rebalanceWithRandomness();
      console.log("Rebalance with randomness result:", result);
      alert("Portfolio rebalanced with randomness!\n\n" + result);
      this.fetchData(); // Refresh data to show updated portfolio
    } catch (error) {
      console.error('Error rebalancing with randomness:', error);
      alert("Error rebalancing with randomness: " + error.message);
    }
  };
  
  rebalanceStandard = async () => {
    try {
      console.log("Rebalancing portfolio (standard)...");
      const result = await motoko_contracts_backend.rebalance();
      console.log("Standard rebalance result:", result);
      alert("Portfolio rebalanced!\n\n" + result);
      this.fetchData(); // Refresh data to show updated portfolio
    } catch (error) {
      console.error('Error rebalancing:', error);
      alert("Error rebalancing: " + error.message);
    }
  };
  
  fetchData = async () => {
    try {
      // Fetch predictions and portfolio data from backend
      console.log("Fetching data from backend...");
      const predictions = await motoko_contracts_backend.getPredictions();
      console.log("Predictions:", predictions);
      
      const portfolio = await motoko_contracts_backend.getPortfolio();
      console.log("Portfolio:", portfolio);
      
      const rebalanceResult = await motoko_contracts_backend.getRebalanceResult();
      console.log("Rebalance result:", rebalanceResult);
      
      const metrics = await motoko_contracts_backend.getMetrics();
      console.log("Metrics:", metrics);
      
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
      console.log("Updated state:", this.state);
      this.render();
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  render() {
    const { btcPrediction, ethPrediction, portfolio, rebalanceResult, metrics, randomnessEnabled, monteCarloSimulationDays } = this.state;
    
    const dashboardTemplate = html`
      <main class="container">
        <header class="dashboard-header">
          <h1>AI Trading Bot Dashboard</h1>
          <button class="logout-btn" @click=${this.onLogout}>Logout</button>
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
                <p class="value">${metrics.updated ? metrics.sharpeRatio.toFixed(2) : 'Not Available'}</p>
              </div>
              <div class="metric-card">
                <h3>Volatility</h3>
                <p class="value">${metrics.updated ? (metrics.volatility * 100).toFixed(2) + '%' : 'Not Available'}</p>
              </div>
              <div class="metric-card">
                <h3>VaR (95%)</h3>
                <p class="value">${metrics.updated ? (metrics.var95 * 100).toFixed(2) + '%' : 'Not Available'}</p>
              </div>
              <div class="metric-card">
                <h3>Max Drawdown</h3>
                <p class="value">${metrics.updated ? (metrics.maxDrawdown * 100).toFixed(2) + '%' : 'Not Available'}</p>
              </div>
            </div>
          ` : html`<p>Loading metrics data...</p>`}
        </section>
        
        <section class="randomness-section">
          <h2>Randomness Features</h2>
          <div class="randomness-controls">
            <div class="toggle-container">
              <label class="toggle-label">
                <span>Enable Randomness</span>
                <input type="checkbox" 
                       ?checked=${randomnessEnabled} 
                       @change=${this.toggleRandomness} />
                <span class="toggle-slider"></span>
              </label>
            </div>
            
            <button class="randomness-btn" @click=${this.getRandomness}>
              Get IC Randomness
            </button>
            
            <div class="monte-carlo-controls">
              <label for="simulation-days">Monte Carlo Simulation Days:</label>
              <input type="number" 
                     id="simulation-days" 
                     min="1" 
                     max="365" 
                     value=${monteCarloSimulationDays} 
                     @change=${this.updateMonteCarloSimulationDays} />
              <button class="monte-carlo-btn" @click=${this.runMonteCarloSimulation}>
                Run Monte Carlo Simulation
              </button>
            </div>
            
            <div class="rebalance-controls">
              <button class="rebalance-btn ${randomnessEnabled ? 'random' : 'standard'}" 
                      @click=${randomnessEnabled ? this.rebalanceWithRandomness : this.rebalanceStandard}>
                ${randomnessEnabled ? 'Rebalance with Randomness' : 'Standard Rebalance'}
              </button>
            </div>
          </div>
        </section>

        <div class="action-buttons">
          <button class="refresh-btn" @click=${this.fetchData}>
            Refresh Data
          </button>
        </div>
      </main>
    `;
    
    return dashboardTemplate;
  }
}

export default Dashboard;
