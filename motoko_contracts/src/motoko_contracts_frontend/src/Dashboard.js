import { html, render } from 'lit-html';
import { motoko_contracts_backend } from 'declarations/motoko_contracts_backend';
import './App.css';
import ProcessModal from './components/ProcessModal';

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
      monteCarloSimulationDays: 30,
      botStatus: 'unknown',
      showProcessModal: false,
      processUpdates: [],
      processSteps: {
        initializing: false,
        loading_model: false,
        collecting_data: false,
        generating_predictions: false,
        retrieving_portfolio: false,
        executing_trades: false,
        completed: false
      },
      updateInterval: null
    };
    this.fetchData();
    this.checkBotStatus();
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

  startTradingBot = async () => {
    try {
      console.log("Starting trading bot...");
      this.setState({ 
        botStatus: 'starting',
        showProcessModal: true,
        processUpdates: [],
        processSteps: {
          initializing: false,
          loading_model: false,
          collecting_data: false,
          generating_predictions: false,
          retrieving_portfolio: false,
          executing_trades: false,
          completed: false
        }
      });
      
      // Start polling for process updates
      const updateInterval = setInterval(() => {
        this.fetchProcessUpdates();
      }, 1000); // Check every second
      
      this.setState({ updateInterval });
      
      // Make API call to start the trading bot
      const response = await fetch('http://localhost:8080/api/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mode: 'trade', interval: 3600 }),
      });
      
      const result = await response.json();
      console.log("Trading bot start result:", result);
      
      if (result.status === 'started') {
        this.setState({ botStatus: 'running' });
        // Don't show alert, the modal will show progress
      } else {
        this.setState({ botStatus: 'error' });
        alert("Error starting trading bot!");
        this.closeProcessModal();
      }
    } catch (error) {
      console.error('Error starting trading bot:', error);
      this.setState({ botStatus: 'error' });
      alert("Error starting trading bot: " + error.message);
      this.closeProcessModal();
    }
  };

  stopTradingBot = async () => {
    try {
      console.log("Stopping trading bot...");
      this.setState({ botStatus: 'stopping' });
      
      // Make API call to stop the trading bot
      const response = await fetch('http://localhost:8080/api/stop', {
        method: 'POST',
      });
      
      const result = await response.json();
      console.log("Trading bot stop result:", result);
      
      if (result.status === 'stopped' || result.status === 'already_stopped') {
        this.setState({ botStatus: 'stopped' });
        alert("Trading bot stopped successfully!");
      } else {
        this.setState({ botStatus: 'error' });
        alert("Error stopping trading bot!");
      }
    } catch (error) {
      console.error('Error stopping trading bot:', error);
      this.setState({ botStatus: 'error' });
      alert("Error stopping trading bot: " + error.message);
    }
  };
  
  checkBotStatus = async () => {
    try {
      // Make API call to check the trading bot status
      const response = await fetch('http://localhost:8080/api/status');
      const result = await response.json();
      console.log("Trading bot status:", result);
      
      this.setState({ botStatus: result.status });
    } catch (error) {
      console.error('Error checking trading bot status:', error);
      this.setState({ botStatus: 'unknown' });
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
      
      this.setState({
        btcPrediction,
        ethPrediction,
        portfolio: processedPortfolio,
        rebalanceResult,
        metrics: processedMetrics
      });
      console.log("Updated state:", this.state);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  fetchProcessUpdates = async () => {
    try {
      const response = await fetch('http://localhost:8080/api/process-updates');
      const data = await response.json();
      
      this.setState({
        processUpdates: data.updates,
        processSteps: data.steps
      });
      
      // If process is completed, stop polling
      if (data.steps.completed) {
        this.clearProcessUpdatesInterval();
      }
    } catch (error) {
      console.error('Error fetching process updates:', error);
    }
  }

  clearProcessUpdatesInterval() {
    if (this.state.updateInterval) {
      clearInterval(this.state.updateInterval);
      this.setState({ updateInterval: null });
    }
  }

  closeProcessModal = () => {
    this.setState({ showProcessModal: false });
    this.clearProcessUpdatesInterval();
  };

  render() {
    const { btcPrediction, ethPrediction, portfolio, rebalanceResult, metrics, randomnessEnabled, monteCarloSimulationDays, botStatus, showProcessModal, processUpdates, processSteps } = this.state;
    
    const dashboardTemplate = html`
      <main class="container">
        <header class="dashboard-header">
          <h1>AI Trading Bot Dashboard</h1>
          <div class="header-buttons">
            <button class="trading-bot-btn ${botStatus === 'running' ? 'running' : botStatus === 'stopped' ? 'stopped' : 'unknown'}" 
                    @click=${botStatus === 'running' ? this.stopTradingBot : this.startTradingBot}
                    ?disabled=${botStatus === 'starting' || botStatus === 'stopping'}>
              ${botStatus === 'running' ? 'Stop Trading Bot' : 
                botStatus === 'stopped' ? 'Start Trading Bot' : 
                botStatus === 'starting' ? 'Starting...' :
                botStatus === 'stopping' ? 'Stopping...' : 'Start Trading Bot'}
            </button>
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
        
        ${showProcessModal ? html`
          <ProcessModal 
            show=${showProcessModal} 
            onClose=${this.closeProcessModal}
            updates=${processUpdates}
            steps=${processSteps}
          />
        ` : ''}
      </main>
    `;
    
    return dashboardTemplate;
  }
}

export default Dashboard;
