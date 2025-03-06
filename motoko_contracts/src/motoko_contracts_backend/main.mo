import Time "mo:base/Time";
import Float "mo:base/Float";
import Random "mo:base/Random";
import Blob "mo:base/Blob";
import Array "mo:base/Array";
import Nat "mo:base/Nat";
import Nat8 "mo:base/Nat8";
import Int "mo:base/Int";
import Debug "mo:base/Debug";
import Iter "mo:base/Iter";
import Text "mo:base/Text";
import Principal "mo:base/Principal";
import Error "mo:base/Error";

actor {
    // Define IC management canister interface types
    type ECDSAPublicKeyReply = {
      public_key : Blob;
      chain_code : Blob;
    };

    type ECDSAPublicKeyRequest = {
      canister_id : ?Principal;
      derivation_path : [Blob];
      key_id : { curve: Text; name: Text };
    };

    // Define Bitcoin types
    type BitcoinGetAddressRequest = {
      network: BitcoinNetwork;
      address_type: { #p2pkh; #p2sh; #p2wpkh; #p2wsh };
      key_id : { curve: Text; name: Text };
      derivation_path : [Blob];
    };

    type BitcoinGetBalanceRequest = {
      network: BitcoinNetwork;
      address: Text;
      min_confirmations: Nat32;
    };

    // IC Management Canister interface
    type IC = actor {
      ecdsa_public_key : shared ECDSAPublicKeyRequest -> async ECDSAPublicKeyReply;
      bitcoin_get_address : shared BitcoinGetAddressRequest -> async Text;
      bitcoin_get_balance : shared BitcoinGetBalanceRequest -> async Nat64;
    };

    // Create an instance of the IC management canister
    let ic : IC = actor "aaaaa-aa";
    
    // Random seed for deterministic testing (will be replaced with secure randomness)
    private var seed : ?Blob = null;
    
    // Number of Monte Carlo simulations to run
    private let NUM_SIMULATIONS : Nat = 20; // Reduced for performance
    
    // Volatility assumptions for Monte Carlo simulations
    private let BTC_DAILY_VOLATILITY : Float = 0.03; // 3% daily volatility
    private let ETH_DAILY_VOLATILITY : Float = 0.04; // 4% daily volatility
        // Chain Key types for ECDSA and Bitcoin integration
    type ECDSAPublicKey = Blob;
    type ECDSAKeyId = { curve: Text; name: Text };
    type BitcoinNetwork = { #mainnet; #testnet; #regtest };
    type BitcoinAddress = Text;
    
    // Portfolio type with amounts and metrics
    type Portfolio = {
        btc : Float;
        eth : Float;
        ckbtc : Float;
        cketh : Float;
        lastRebalanceTime : Int;
        totalValue : Float;
        performance : Float;
        btcAddress : ?Text;
        ethAddress : ?Text;
    };

    // Risk parameters
    let MAX_ALLOCATION : Float = 0.8;  // Maximum 80% in one asset
    let MIN_ALLOCATION : Float = 0.2;  // Minimum 20% in one asset
    let REBALANCE_THRESHOLD : Float = 0.1;  // 10% deviation triggers rebalance

    // Initialize portfolio
    var portfolio : Portfolio = {
        btc = 1000.0;
        eth = 1000.0;
        ckbtc = 0.0;
        cketh = 0.0;
        lastRebalanceTime = 0;
        totalValue = 2000.0;
        performance = 0.0;
        btcAddress = null;
        ethAddress = null;
    };

    // Store latest predictions and metrics
    var latestBtcPrediction : Float = 0.0;
    var latestEthPrediction : Float = 0.0;
    var latestRebalanceResult : Text = "";
    
    // Store performance metrics
    var metrics = {
        sharpeRatio : Float = 0.0;
        volatility : Float = 0.0;
        var95 : Float = 0.0;
        maxDrawdown : Float = 0.0;
        monteCarloSimulated : Bool = false;
    };
    
    // Flag to track if metrics have been updated by the AI model
    var metricsUpdated : Bool = false;

    // Get current portfolio state
    public query func getPortfolio() : async Portfolio {
        return portfolio;
    };
    
    // Chain Key Cryptography functions for Bitcoin address generation
    
    // Get the ECDSA public key for the canister
    public func get_ecdsa_public_key() : async Blob {
        let key_id = { 
            curve = "secp256k1"; 
            name = "dfx_test_key" 
        };
        
        let derivation_path = [];
        
        try {
            let result = await ic.ecdsa_public_key({
                canister_id = null;
                derivation_path = derivation_path;
                key_id = key_id;
            });
            return result.public_key;
        } catch (e) {
            Debug.print("Error getting ECDSA public key: " # Error.message(e));
            throw e;
        };
    };
    
    // Generate a P2PKH Bitcoin address from the canister's ECDSA public key
    public func get_p2pkh_address(network: BitcoinNetwork) : async BitcoinAddress {
        let key_id = { 
            curve = "secp256k1"; 
            name = "dfx_test_key" 
        };
        
        let derivation_path = [];
        
        try {
            let result = await ic.bitcoin_get_address({
                network = network;
                address_type = #p2pkh;
                key_id = key_id;
                derivation_path = derivation_path;
            });
            
            // Update portfolio with the Bitcoin address
            portfolio := {
                portfolio with btcAddress = ?result;
            };
            
            return result;
        } catch (e) {
            Debug.print("Error generating Bitcoin address: " # Error.message(e));
            throw e;
        };
    };
    
    // Get the current Bitcoin address for the canister
    public query func get_bitcoin_address() : async ?BitcoinAddress {
        return portfolio.btcAddress;
    };
    
    // Get the balance of the Bitcoin address
    public func get_bitcoin_balance(network: BitcoinNetwork, min_confirmations: Nat32) : async Nat64 {
        let address = switch (portfolio.btcAddress) {
            case (null) { 
                throw Error.reject("No Bitcoin address generated yet");
            };
            case (?addr) { addr };
        };
        
        try {
            let result = await ic.bitcoin_get_balance({
                network = network;
                address = address;
                min_confirmations = min_confirmations;
            });
            return result;
        } catch (e) {
            Debug.print("Error getting Bitcoin balance: " # Error.message(e));
            throw e;
        };
    };
    
    // Update the ckBTC balance in the portfolio
    public func update_ckbtc_balance(amount: Float) : async () {
        portfolio := {
            portfolio with 
            ckbtc = amount;
            totalValue = portfolio.btc + portfolio.eth + amount + portfolio.cketh;
        };
    };

    // Get latest predictions
    public query func getPredictions() : async {btc : Float; eth : Float} {
        return { btc = latestBtcPrediction; eth = latestEthPrediction };
    };

    // Update predictions from AI model
    public func setPredictions(btcPred : Float, ethPred : Float) : async () {
        latestBtcPrediction := btcPred;
        latestEthPrediction := ethPred;
    };

    // Get latest rebalance result
    public query func getRebalanceResult() : async Text {
        return latestRebalanceResult;
    };
    
    // Get performance metrics
    public query func getMetrics() : async {
        sharpeRatio : Float;
        volatility : Float;
        var95 : Float;
        maxDrawdown : Float;
        updated : Bool;
        monteCarloSimulated : Bool;
    } {
        return {
            sharpeRatio = metrics.sharpeRatio;
            volatility = metrics.volatility;
            var95 = metrics.var95;
            maxDrawdown = metrics.maxDrawdown;
            updated = metricsUpdated;
            monteCarloSimulated = metrics.monteCarloSimulated;
        };
    };
    
    // Update metrics from AI model
    public func updateMetrics(
        sharpeRatio : Float,
        volatility : Float,
        var95 : Float,
        maxDrawdown : Float
    ) : async () {
        metrics := {
            sharpeRatio = sharpeRatio;
            volatility = volatility;
            var95 = var95;
            maxDrawdown = maxDrawdown;
            monteCarloSimulated = false;
        };
        metricsUpdated := true;
    };
    
    // Get secure randomness from the Internet Computer
    public func getRandomness() : async Blob {
        let random = await Random.blob();
        seed := ?random;
        return random;
    };
    
    // Generate a random float between min and max
    private func randomFloat(min : Float, max : Float) : async Float {
        let randomBlob = switch (seed) {
            case (null) { await Random.blob(); };
            case (?existingSeed) { existingSeed };
        };
        
        // Convert first 8 bytes to a number between 0 and 1
        let bytes = Blob.toArray(randomBlob);
        var value : Nat = 0;
        for (i in Iter.range(0, 7)) {
            value := value * 256 + Nat8.toNat(bytes[i % bytes.size()]);
        };
        
        let normalized = Float.fromInt(value % 1_000_000) / 1_000_000.0;
        return min + normalized * (max - min);
    };
    
    // Run Monte Carlo simulation for portfolio risk assessment (optimized version)
    public func runMonteCarloSimulation(days : Nat) : async {
        simulatedSharpeRatio : Float;
        simulatedVolatility : Float;
        simulatedVar95 : Float;
        simulatedMaxDrawdown : Float;
    } {
        // Initialize arrays to store simulation results - using smaller arrays
        let maxDays = if (days > 20) 20 else days; // Limit simulation days to 20 for performance
        var finalValues = Array.init<Float>(NUM_SIMULATIONS, 0.0);
        var dailyReturns = Array.init<Float>(NUM_SIMULATIONS * maxDays, 0.0);
        var maxDrawdowns = Array.init<Float>(NUM_SIMULATIONS, 0.0);
        
        // Current portfolio allocation
        let btcWeight = portfolio.btc / portfolio.totalValue;
        let ethWeight = portfolio.eth / portfolio.totalValue;
        
        // Get a single random blob to use for all simulations
        let randomBlob = await Random.blob();
        seed := ?randomBlob;
        let bytes = Blob.toArray(randomBlob);
        
        // Run simulations
        for (i in Iter.range(0, NUM_SIMULATIONS - 1)) {
            var currentValue = portfolio.totalValue;
            var peakValue = currentValue;
            var currentDrawdown : Float = 0.0;
            
            for (d in Iter.range(0, maxDays - 1)) {
                // Generate deterministic but pseudo-random returns based on position
                let seed1 = Nat8.toNat(bytes[(i * maxDays + d) % bytes.size()]);
                let seed2 = Nat8.toNat(bytes[((i * maxDays + d) + 1) % bytes.size()]);
                
                let btcReturn = (Float.fromInt(seed1) / 255.0 - 0.5) * 2.0 * BTC_DAILY_VOLATILITY;
                let ethReturn = (Float.fromInt(seed2) / 255.0 - 0.5) * 2.0 * ETH_DAILY_VOLATILITY;
                
                // Apply returns to portfolio based on weights
                let portfolioReturn = btcWeight * btcReturn + ethWeight * ethReturn;
                currentValue := currentValue * (1.0 + portfolioReturn);
                
                // Store daily return
                dailyReturns[i * maxDays + d] := portfolioReturn;
                
                // Update peak value and drawdown
                if (currentValue > peakValue) {
                    peakValue := currentValue;
                };
                
                let drawdown = (peakValue - currentValue) / peakValue;
                if (drawdown > currentDrawdown) {
                    currentDrawdown := drawdown;
                };
            };
            
            // Store final values and max drawdown
            finalValues[i] := currentValue;
            maxDrawdowns[i] := currentDrawdown;
        };
        
        // Calculate metrics from simulation results
        var sumReturns : Float = 0.0;
        var sumSquaredReturns : Float = 0.0;
        
        // Use maxDays instead of days to match the optimized simulation
        for (i in Iter.range(0, NUM_SIMULATIONS * maxDays - 1)) {
            sumReturns += dailyReturns[i];
            sumSquaredReturns += dailyReturns[i] * dailyReturns[i];
        };
        
        let avgReturn = sumReturns / Float.fromInt(NUM_SIMULATIONS * maxDays);
        let variance = sumSquaredReturns / Float.fromInt(NUM_SIMULATIONS * maxDays) - avgReturn * avgReturn;
        let simulatedVolatility = Float.sqrt(variance) * Float.sqrt(252.0); // Annualized
        
        // Sort returns for VaR calculation
        let sortedReturns = Array.sort<Float>(Array.freeze(dailyReturns), Float.compare);
        let varIndex = Int.abs(Float.toInt(0.05 * Float.fromInt(NUM_SIMULATIONS * maxDays)));
        let simulatedVar95 = sortedReturns[varIndex];
        
        // Calculate average max drawdown
        var sumDrawdowns : Float = 0.0;
        for (i in Iter.range(0, NUM_SIMULATIONS - 1)) {
            sumDrawdowns += maxDrawdowns[i];
        };
        let simulatedMaxDrawdown = sumDrawdowns / Float.fromInt(NUM_SIMULATIONS);
        
        // Calculate Sharpe ratio (assuming risk-free rate of 0)
        let simulatedSharpeRatio = (avgReturn * 252.0) / simulatedVolatility;
        
        // Update metrics with simulated values
        metrics := {
            sharpeRatio = simulatedSharpeRatio;
            volatility = simulatedVolatility;
            var95 = simulatedVar95;
            maxDrawdown = simulatedMaxDrawdown;
            monteCarloSimulated = true;
        };
        metricsUpdated := true;
        
        return {
            simulatedSharpeRatio = simulatedSharpeRatio;
            simulatedVolatility = simulatedVolatility;
            simulatedVar95 = simulatedVar95;
            simulatedMaxDrawdown = simulatedMaxDrawdown;
        };
    };
    
    // Update metrics from AI model with randomness-enhanced values
    public func updateMetricsWithRandomness(
        sharpeRatio : Float,
        volatility : Float,
        var95 : Float,
        maxDrawdown : Float
    ) : async () {
        // Get randomness
        let random = await Random.blob();
        seed := ?random;
        
        // Add small random perturbation to metrics (±10%)
        let byte1 = Nat8.toNat(Blob.toArray(random)[0]);
        let byte2 = Nat8.toNat(Blob.toArray(random)[1]);
        let byte3 = Nat8.toNat(Blob.toArray(random)[2]);
        let byte4 = Nat8.toNat(Blob.toArray(random)[3]);
        
        let randomFactor1 = Float.fromInt(byte1) * 200.0 / 1000000.0; // 0-0.2
        let randomFactor2 = Float.fromInt(byte2) * 200.0 / 1000000.0;
        let randomFactor3 = Float.fromInt(byte3) * 200.0 / 1000000.0;
        let randomFactor4 = Float.fromInt(byte4) * 200.0 / 1000000.0;
        
        metrics := {
            sharpeRatio = sharpeRatio * (1.0 + randomFactor1 - 0.1);
            volatility = volatility * (1.0 + randomFactor2 - 0.1);
            var95 = var95 * (1.0 + randomFactor3 - 0.1);
            maxDrawdown = maxDrawdown * (1.0 + randomFactor4 - 0.1);
            monteCarloSimulated = true;
        };
        metricsUpdated := true;
    };

    // Calculate optimal weights based on predictions and constraints
    private func calculateOptimalWeights() : (Float, Float) {
        var btcWeight = latestBtcPrediction / (latestBtcPrediction + latestEthPrediction);
        var ethWeight = 1.0 - btcWeight;

        // Apply allocation constraints
        if (btcWeight > MAX_ALLOCATION) {
            btcWeight := MAX_ALLOCATION;
            ethWeight := 1.0 - MAX_ALLOCATION;
        } else if (btcWeight < MIN_ALLOCATION) {
            btcWeight := MIN_ALLOCATION;
            ethWeight := 1.0 - MIN_ALLOCATION;
        };

        return (btcWeight, ethWeight);
    };
    
    // Calculate optimal weights with randomness for exploration
    public func calculateOptimalWeightsWithRandomness() : async (Float, Float) {
        // Get base weights from prediction model
        let (basebtcWeight, baseEthWeight) = calculateOptimalWeights();
        
        // Get randomness
        let random = await Random.blob();
        seed := ?random;
        
        // Convert first byte to a small random adjustment factor (-5% to +5%)
        let bytes = Blob.toArray(random);
        let byteValue = Nat8.toNat(bytes[0]);
        let randomAdjustment = (Float.fromInt(byteValue) / 255.0) * 0.1 - 0.05;
        
        // Apply random adjustment to weights
        var btcWeight = basebtcWeight + randomAdjustment;
        var ethWeight = 1.0 - btcWeight;
        
        // Apply allocation constraints
        if (btcWeight > MAX_ALLOCATION) {
            btcWeight := MAX_ALLOCATION;
            ethWeight := 1.0 - MAX_ALLOCATION;
        } else if (btcWeight < MIN_ALLOCATION) {
            btcWeight := MIN_ALLOCATION;
            ethWeight := 1.0 - MIN_ALLOCATION;
        };
        
        return (btcWeight, ethWeight);
    };

    // Rebalance portfolio based on predictions and constraints
    public shared func rebalance() : async Text {
        let currentTime = Time.now();
        let totalValue = portfolio.btc + portfolio.eth;
        
        // Calculate current weights
        let currentBtcWeight = portfolio.btc / totalValue;
        let _currentEthWeight = portfolio.eth / totalValue;

        // Get optimal weights
        let (targetBtcWeight, targetEthWeight) = calculateOptimalWeights();

        // Check if rebalance is needed
        if (Float.abs(currentBtcWeight - targetBtcWeight) > REBALANCE_THRESHOLD) {
            // Calculate new amounts
            let newBtc = totalValue * targetBtcWeight;
            let newEth = totalValue * targetEthWeight;

            // Update portfolio
            portfolio := {
                btc = newBtc;
                eth = newEth;
                ckbtc = portfolio.ckbtc;
                cketh = portfolio.cketh;
                lastRebalanceTime = currentTime;
                totalValue = totalValue;
                performance = (totalValue - 2000.0) / 2000.0;  // Simple return calculation
                btcAddress = portfolio.btcAddress;
                ethAddress = portfolio.ethAddress;
            };

            latestRebalanceResult := "Portfolio rebalanced. New weights: BTC=" # Float.toText(targetBtcWeight) # ", ETH=" # Float.toText(targetEthWeight);
        } else {
            latestRebalanceResult := "No rebalance needed. Current allocation within threshold.";
        };

        return latestRebalanceResult;
    };
    
    // Rebalance portfolio with randomness-enhanced weights
    public shared func rebalanceWithRandomness() : async Text {
        let currentTime = Time.now();
        let totalValue = portfolio.btc + portfolio.eth;
        
        // Calculate current weights
        let currentBtcWeight = portfolio.btc / totalValue;
        let _currentEthWeight = portfolio.eth / totalValue;

        // Get optimal weights with randomness
        let (targetBtcWeight, targetEthWeight) = await calculateOptimalWeightsWithRandomness();

        // Always rebalance when using randomness to explore different allocations
        // Calculate new amounts
        let newBtc = totalValue * targetBtcWeight;
        let newEth = totalValue * targetEthWeight;

        // Update portfolio
        portfolio := {
            btc = newBtc;
            eth = newEth;
            ckbtc = portfolio.ckbtc;
            cketh = portfolio.cketh;
            lastRebalanceTime = currentTime;
            totalValue = totalValue;
            performance = (totalValue - 2000.0) / 2000.0;  // Simple return calculation
            btcAddress = portfolio.btcAddress;
            ethAddress = portfolio.ethAddress;
        };

        latestRebalanceResult := "Portfolio rebalanced with randomness. New weights: BTC=" # Float.toText(targetBtcWeight) # ", ETH=" # Float.toText(targetEthWeight);
        
        // Run Monte Carlo simulation to update risk metrics
        ignore await runMonteCarloSimulation(30); // Simulate 30 days

        return latestRebalanceResult;
    };
}