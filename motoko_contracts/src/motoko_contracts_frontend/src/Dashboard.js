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
      metrics: null
    };
    this.fetchData();
  }

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
        updated: typeof metrics.updated === 'boolean' ? metrics.updated : Boolean(metrics.updated)
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
    const { btcPrediction, ethPrediction, portfolio, rebalanceResult, metrics } = this.state;
    
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
          <h2>Performance Metrics</h2>
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

        <button class="refresh-btn" @click=${this.fetchData}>
          Refresh Data
        </button>
      </main>
    `;
    
    return dashboardTemplate;
  }
}

export default Dashboard;
