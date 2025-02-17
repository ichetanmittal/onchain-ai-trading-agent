actor {
  // A simple portfolio type with two assets (BTC & ETH)
  type Portfolio = {
    btc : Float;
    eth : Float;
  };

  // Initialize with some dummy amounts
  var portfolio : Portfolio = {
    btc = 1000.0;
    eth = 1000.0;
  };

  // Store latest predictions and rebalance result
  var latestBtcPrediction : Float = 0.0;
  var latestEthPrediction : Float = 0.0;
  var latestRebalanceResult : Text = "";

  public func getPortfolio() : async Portfolio {
    return portfolio;
  };

  // Let's also see predictions
  public func getPredictions() : async {btc : Float; eth : Float} {
    return { btc = latestBtcPrediction; eth = latestEthPrediction };
  };

  public func setPredictions(btcPred : Float, ethPred : Float) : async () {
    latestBtcPrediction := btcPred;
    latestEthPrediction := ethPred;
  };

  // Get the latest rebalance result
  public func getRebalanceResult() : async Text {
    return latestRebalanceResult;
  };

  // Simple example: if BTC pred > ETH pred => 70/30; else 30/70
  public func rebalance() : async Text {
    let total = portfolio.btc + portfolio.eth;
    if (latestBtcPrediction > latestEthPrediction) {
      portfolio := {
        btc = total * 0.7;
        eth = total * 0.3;
      };
      latestRebalanceResult := "BTC predicted to outperform => Rebalanced to 70/30.";
    } else {
      portfolio := {
        btc = total * 0.3;
        eth = total * 0.7;
      };
      latestRebalanceResult := "ETH predicted to outperform => Rebalanced to 30/70.";
    };
    return latestRebalanceResult;
  };
}