import Time "mo:base/Time";
import Float "mo:base/Float";

actor {
    // Portfolio type with amounts and metrics
    type Portfolio = {
        btc : Float;
        eth : Float;
        lastRebalanceTime : Int;
        totalValue : Float;
        performance : Float;
    };

    // Risk parameters
    let MAX_ALLOCATION : Float = 0.8;  // Maximum 80% in one asset
    let MIN_ALLOCATION : Float = 0.2;  // Minimum 20% in one asset
    let REBALANCE_THRESHOLD : Float = 0.1;  // 10% deviation triggers rebalance

    // Initialize portfolio
    var portfolio : Portfolio = {
        btc = 1000.0;
        eth = 1000.0;
        lastRebalanceTime = 0;
        totalValue = 2000.0;
        performance = 0.0;
    };

    // Store latest predictions and metrics
    var latestBtcPrediction : Float = 0.0;
    var latestEthPrediction : Float = 0.0;
    var latestRebalanceResult : Text = "";
    
    // Store performance metrics
    var metrics = {
        sharpeRatio : Float = -3.33;
        volatility : Float = 0.006;
        var95 : Float = -0.0094;
        maxDrawdown : Float = -0.244;
    };

    // Get current portfolio state
    public query func getPortfolio() : async Portfolio {
        return portfolio;
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
    } {
        return metrics;
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
        };
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
                lastRebalanceTime = currentTime;
                totalValue = totalValue;
                performance = (totalValue - 2000.0) / 2000.0;  // Simple return calculation
            };

            latestRebalanceResult := "Portfolio rebalanced. New weights: BTC=" # Float.toText(targetBtcWeight) # ", ETH=" # Float.toText(targetEthWeight);
        } else {
            latestRebalanceResult := "No rebalance needed. Current allocation within threshold.";
        };

        return latestRebalanceResult;
    };
}