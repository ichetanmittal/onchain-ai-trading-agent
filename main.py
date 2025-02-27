import argparse
import asyncio
import logging
from ai_bot.controller import TradingBotController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='AI Trading Bot')
        parser.add_argument('--config', type=str, required=True, help='Path to configuration file')
        parser.add_argument('--mode', choices=['train', 'trade', 'optimize'], required=True,
                          help='Operation mode: train, trade, or optimize')
        parser.add_argument('--interval', type=int, default=3600,
                          help='Trading interval in seconds (default: 3600)')
        parser.add_argument('--trials', type=int, default=100,
                          help='Number of optimization trials (default: 100)')
        args = parser.parse_args()
        
        # Initialize controller
        controller = TradingBotController(config_path=args.config)
        
        if args.mode == 'train':
            # Retrain model
            logger.info("Starting model retraining...")
            await controller.initialize()
            logger.info("Model retraining completed")
            
        elif args.mode == 'optimize':
            # Run hyperparameter optimization
            logger.info("Starting hyperparameter optimization...")
            await controller.initialize()
            controller.optimize_hyperparameters(n_trials=args.trials)
            logger.info("Hyperparameter optimization completed")
            
        else:  # trade mode
            # Start continuous trading
            logger.info("Starting continuous trading...")
            await controller.initialize()
            await controller.start_continuous_trading(interval_seconds=args.interval)
            
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
