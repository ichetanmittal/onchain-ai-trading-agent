import { html, render } from 'lit-html';
import { motoko_contracts_backend } from 'declarations/motoko_contracts_backend';
import './App.css';

class App {
  constructor() {
    this.state = {
      btcPrediction: null,
      ethPrediction: null,
      portfolio: null,
      rebalanceResult: null
    };
    this.#render();
    this.#fetchData();
  }

  #fetchData = async () => {
    try {
      // Fetch predictions and portfolio data from backend
      const predictions = await motoko_contracts_backend.getPredictions();
      const portfolio = await motoko_contracts_backend.getPortfolio();
      const rebalanceResult = await motoko_contracts_backend.getRebalanceResult();
      
      this.state = {
        btcPrediction: predictions?.btc,
        ethPrediction: predictions?.eth,
        portfolio,
        rebalanceResult
      };
      this.#render();
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  #render() {
    const { btcPrediction, ethPrediction, portfolio, rebalanceResult } = this.state;
    
    let body = html`
      <main class="container">
        <h1>AI Trading Bot Dashboard</h1>
        
        <section class="predictions-section">
          <h2>Price Predictions</h2>
          <div class="predictions-grid">
            <div class="prediction-card">
              <h3>BTC Prediction</h3>
              <p class="price">${btcPrediction ? `$${btcPrediction.toLocaleString()}` : 'Loading...'}</p>
            </div>
            <div class="prediction-card">
              <h3>ETH Prediction</h3>
              <p class="price">${ethPrediction ? `$${ethPrediction.toLocaleString()}` : 'Loading...'}</p>
            </div>
          </div>
        </section>

        <section class="portfolio-section">
          <h2>Current Portfolio</h2>
          ${portfolio ? html`
            <div class="portfolio-grid">
              <div class="portfolio-card">
                <h3>BTC Holdings</h3>
                <p class="amount">${portfolio.btc.toFixed(2)} BTC</p>
              </div>
              <div class="portfolio-card">
                <h3>ETH Holdings</h3>
                <p class="amount">${portfolio.eth.toFixed(2)} ETH</p>
              </div>
            </div>
          ` : html`<p>Loading portfolio data...</p>`}
        </section>

        <section class="rebalance-section">
          <h2>Latest Rebalance</h2>
          <p class="rebalance-result">${rebalanceResult || 'No rebalance data available'}</p>
        </section>

        <button class="refresh-btn" @click=${this.#fetchData}>
          Refresh Data
        </button>
      </main>
    `;
    
    render(body, document.getElementById('root'));
  }
}

export default App;
