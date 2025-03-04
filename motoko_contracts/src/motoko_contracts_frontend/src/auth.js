import { AuthClient } from "@dfinity/auth-client";
import { Actor, HttpAgent } from "@dfinity/agent";
import { idlFactory as motoko_contracts_idl } from "declarations/motoko_contracts_backend/motoko_contracts_backend.did.js";
import { II_URL, BACKEND_CANISTER_ID, DFX_NETWORK, HOST } from "./config";

// The URL for the Internet Identity canister
// For local development, use the local II canister
// For production, use the production II canister

class AuthService {
  constructor() {
    console.log("[AuthService] Initializing with config:", {
      II_URL,
      BACKEND_CANISTER_ID,
      DFX_NETWORK,
      HOST
    });
    this.authClient = null;
    this.identity = null;
    this.agent = null;
    this.actor = null;
    this.isAuthenticated = false;
    this.principal = null;
    this.listeners = [];
  }

  // Initialize the auth client
  async init() {
    console.log("[AuthService] Starting initialization");
    try {
      this.authClient = await AuthClient.create();
      console.log("[AuthService] AuthClient created successfully");
      
      const isAuthenticated = await this.authClient.isAuthenticated();
      console.log("[AuthService] isAuthenticated:", isAuthenticated);
      
      if (isAuthenticated) {
        this.identity = this.authClient.getIdentity();
        this.principal = this.identity.getPrincipal();
        console.log("[AuthService] Principal:", this.principal.toString());
        
        this.agent = new HttpAgent({ 
          identity: this.identity,
          host: HOST
        });
        console.log("[AuthService] Agent created with host:", HOST);
        
        // For local development, we need to fetch the root key
        if (DFX_NETWORK !== 'ic') {
          console.log("[AuthService] Fetching root key for local development");
          await this.agent.fetchRootKey();
        }
        
        console.log("[AuthService] Creating actor with canisterId:", BACKEND_CANISTER_ID);
        this.actor = Actor.createActor(motoko_contracts_idl, {
          agent: this.agent,
          canisterId: BACKEND_CANISTER_ID,
        });
        
        this.isAuthenticated = true;
        this.notifyListeners();
        console.log("[AuthService] Initialization complete with authenticated user");
      } else {
        console.log("[AuthService] Initialization complete, user not authenticated");
      }
      
      return isAuthenticated;
    } catch (error) {
      console.error("[AuthService] Error during initialization:", error);
      return false;
    }
  }

  // Login with Internet Identity
  async login() {
    console.log("[AuthService] Starting login process with II_URL:", II_URL);
    return new Promise((resolve) => {
      try {
        this.authClient.login({
          identityProvider: II_URL,
          onSuccess: async () => {
            console.log("[AuthService] Login successful");
            this.identity = this.authClient.getIdentity();
            this.principal = this.identity.getPrincipal();
            console.log("[AuthService] Principal after login:", this.principal.toString());
            
            this.agent = new HttpAgent({ 
              identity: this.identity,
              host: HOST
            });
            console.log("[AuthService] Agent created after login with host:", HOST);
            
            // For local development, we need to fetch the root key
            if (DFX_NETWORK !== 'ic') {
              console.log("[AuthService] Fetching root key for local development after login");
              await this.agent.fetchRootKey();
            }
            
            console.log("[AuthService] Creating actor after login with canisterId:", BACKEND_CANISTER_ID);
            this.actor = Actor.createActor(motoko_contracts_idl, {
              agent: this.agent,
              canisterId: BACKEND_CANISTER_ID,
            });
            
            this.isAuthenticated = true;
            this.notifyListeners();
            console.log("[AuthService] Login process complete");
            resolve(true);
          },
          onError: (error) => {
            console.error("[AuthService] Login failed:", error);
            resolve(false);
          }
        });
      } catch (error) {
        console.error("[AuthService] Error during login process:", error);
        resolve(false);
      }
    });
  }

  // Logout
  async logout() {
    console.log("[AuthService] Starting logout process");
    try {
      await this.authClient.logout();
      console.log("[AuthService] Logout successful");
      this.identity = null;
      this.principal = null;
      this.agent = null;
      this.actor = null;
      this.isAuthenticated = false;
      this.notifyListeners();
      console.log("[AuthService] Logout process complete");
    } catch (error) {
      console.error("[AuthService] Error during logout process:", error);
    }
  }

  // Get the authenticated actor
  getActor() {
    if (!this.actor) {
      console.warn("[AuthService] getActor called but actor is null");
    }
    return this.actor;
  }

  // Get the user's principal
  getPrincipal() {
    if (!this.principal) {
      console.warn("[AuthService] getPrincipal called but principal is null");
    }
    return this.principal;
  }

  // Check if the user is authenticated
  getIsAuthenticated() {
    return this.isAuthenticated;
  }

  // Add a listener for authentication state changes
  addListener(listener) {
    console.log("[AuthService] Adding listener");
    this.listeners.push(listener);
  }

  // Remove a listener
  removeListener(listener) {
    console.log("[AuthService] Removing listener");
    this.listeners = this.listeners.filter(l => l !== listener);
  }

  // Notify all listeners of authentication state changes
  notifyListeners() {
    console.log("[AuthService] Notifying listeners of authentication state:", this.isAuthenticated);
    this.listeners.forEach(listener => listener(this.isAuthenticated));
  }
}

// Create a singleton instance
const authService = new AuthService();

export default authService;
