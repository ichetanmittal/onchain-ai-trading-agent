import { html, render } from 'lit-html';
import LandingPage from './LandingPage';
import Dashboard from './Dashboard';
import './App.css';

class App {
  constructor() {
    this.state = {
      isAuthenticated: false
    };
    this.landingPage = new LandingPage(this.handleLogin);
    this.dashboard = new Dashboard(this.handleLogout);
    this.render();
  }

  handleLogin = () => {
    // In a real app, this would involve actual authentication
    console.log("Logging in...");
    this.state.isAuthenticated = true;
    this.render();
  };

  handleLogout = () => {
    console.log("Logging out...");
    this.state.isAuthenticated = false;
    this.render();
  };

  render() {
    const { isAuthenticated } = this.state;
    
    let content;
    if (isAuthenticated) {
      content = this.dashboard.render();
    } else {
      content = this.landingPage.render();
    }
    
    render(content, document.getElementById('root'));
  }
}

export default App;
