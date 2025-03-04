import { html } from 'lit-html';
import './ProcessModal.css';

const ProcessModal = (props) => {
  const { show, onClose, updates = [], steps = {} } = props;
  
  if (!show) {
    return html``;
  }
  
  const renderStepStatus = (steps) => {
    return html`
      <div class="process-steps">
        <div class="process-step ${steps.initializing ? 'completed' : ''}">
          <div class="step-indicator">
            ${steps.initializing ? '✓' : '○'}
          </div>
          <div class="step-label">Initializing</div>
        </div>
        <div class="process-step ${steps.loading_model ? 'completed' : ''}">
          <div class="step-indicator">
            ${steps.loading_model ? '✓' : '○'}
          </div>
          <div class="step-label">Loading Model</div>
        </div>
        <div class="process-step ${steps.collecting_data ? 'completed' : ''}">
          <div class="step-indicator">
            ${steps.collecting_data ? '✓' : '○'}
          </div>
          <div class="step-label">Collecting Data</div>
        </div>
        <div class="process-step ${steps.generating_predictions ? 'completed' : ''}">
          <div class="step-indicator">
            ${steps.generating_predictions ? '✓' : '○'}
          </div>
          <div class="step-label">Generating Predictions</div>
        </div>
        <div class="process-step ${steps.retrieving_portfolio ? 'completed' : ''}">
          <div class="step-indicator">
            ${steps.retrieving_portfolio ? '✓' : '○'}
          </div>
          <div class="step-label">Retrieving Portfolio</div>
        </div>
        <div class="process-step ${steps.executing_trades ? 'completed' : ''}">
          <div class="step-indicator">
            ${steps.executing_trades ? '✓' : '○'}
          </div>
          <div class="step-label">Executing Trades</div>
        </div>
        <div class="process-step ${steps.completed ? 'completed' : ''}">
          <div class="step-indicator">
            ${steps.completed ? '✓' : '○'}
          </div>
          <div class="step-label">Completed</div>
        </div>
      </div>
    `;
  };
  
  const renderUpdates = (updates) => {
    return html`
      <div class="process-updates">
        ${updates.map(update => html`
          <div class="update-item">
            <span class="update-timestamp">${update.timestamp}</span>
            <span class="update-message">${update.message}</span>
          </div>
        `)}
      </div>
    `;
  };
  
  return html`
    <div class="modal-overlay">
      <div class="modal-container">
        <div class="modal-header">
          <h2>Trading Bot Progress</h2>
          <button class="close-button" @click=${onClose}>×</button>
        </div>
        <div class="modal-body">
          ${renderStepStatus(steps)}
          <h3>Process Log</h3>
          ${renderUpdates(updates)}
        </div>
        <div class="modal-footer">
          <button class="close-button-text" @click=${onClose}>Close</button>
        </div>
      </div>
    </div>
  `;
};

export default ProcessModal;
