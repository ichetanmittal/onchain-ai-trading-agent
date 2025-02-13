// motoko_contracts/src/motoko_contracts/main.mo

actor {
  // Internal state for the latest AI prediction
  var latestPrediction : Float = 0.0;

  // Store new prediction
  public func setPrediction(newPred : Float) : async () {
    latestPrediction := newPred;
  };

  // Retrieve current prediction
  public func getPrediction() : async Float {
    return latestPrediction;
  };
}