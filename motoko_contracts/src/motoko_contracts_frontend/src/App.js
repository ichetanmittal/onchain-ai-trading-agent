import { html, render } from 'lit-html';
import LandingPage from './LandingPage';
import Dashboard from './Dashboard';
import authService from './auth';
import './App.css';

class App {
  constructor() {
    console.log("[App] Initializing App component");
    this.state = {
      isAuthenticated: false,
      isInitializing: true,
      principal: null
    };
    
    this.landingPage = new LandingPage(this.handleLogin);
    this.dashboard = new Dashboard(this.handleLogout);
    
    // Initialize auth service
    this.initAuth();
  }

  initAuth = async () => {
    console.log("[App] Starting initialization");
    try {
      const isAuthenticated = await authService.init();
      console.log("[App] Auth initialization complete, isAuthenticated:", isAuthenticated);
      if (isAuthenticated) {
        const principal = authService.getPrincipal();
        this.state = {
          isAuthenticated: true,
          isInitializing: false,
          principal: principal.toString()
        };
      } else {
        this.state = {
          isAuthenticated: false,
          isInitializing: false,
          principal: null
        };
      }
      console.log("[App] Rendering after initialization with state:", this.state);
      this.render();
    } catch (error) {
      console.error("[App] Error during initialization:", error);
      this.state = {
        isAuthenticated: false,
        isInitializing: false,
        principal: null
      };
      console.log("[App] Rendering after initialization error with state:", this.state);
      this.render();
    }
    
    // Add listener for auth state changes
    authService.addListener(this.handleAuthChange);
  };

  handleAuthChange = (isAuthenticated) => {
    console.log("[App] Auth state changed to:", isAuthenticated);
    const principal = isAuthenticated ? authService.getPrincipal().toString() : null;
    this.state = {
      ...this.state,
      isAuthenticated,
      principal
    };
    console.log("[App] Rendering after auth state change with state:", this.state);
    this.render();
  };

  handleLogin = async () => {
    console.log("[App] Logging in with Internet Identity...");
    try {
      await authService.login();
    } catch (error) {
      console.error("[App] Login error:", error);
    }
  };

  handleLogout = async () => {
    console.log("[App] Logging out...");
    try {
      await authService.logout();
    } catch (error) {
      console.error("[App] Logout error:", error);
    }
  };

  render() {
    console.log("[App] Rendering App component");
    const { isAuthenticated, isInitializing, principal } = this.state;
    
    let content;
    if (isInitializing) {
      console.log("[App] Rendering loading template");
      content = html`
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <p>Initializing application...</p>
        </div>
      `;
    } else if (isAuthenticated) {
      console.log("[App] Rendering dashboard template");
      this.dashboard.principal = principal;
      content = this.dashboard.render();
    } else {
      console.log("[App] Rendering landing page template");
      content = this.landingPage.render();
    }
    
    render(content, document.getElementById('root'));
  }
}

export default App;
