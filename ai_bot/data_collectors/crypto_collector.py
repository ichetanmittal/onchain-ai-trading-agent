import os
import logging
import asyncio
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from binance.client import Client as BinanceClient
from web3 import Web3
import ccxt.async_support as ccxt
from .base_collector import BaseDataCollector

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class CryptoDataCollector(BaseDataCollector):
    """Collects cryptocurrency data from various sources"""
    
    def __init__(self, symbols: List[str], timeframe: str = '1h', exchange_id: str = 'binance'):
        """
        Initialize the collector
        
        Args:
            symbols: List of trading pairs (e.g., ['BTC/USDT', 'ETH/USDT'])
            timeframe: Data timeframe (e.g., '1h', '4h', '1d')
            exchange_id: Exchange to use (default: 'binance')
        """
        super().__init__(symbols)
        self.symbols = symbols
        self.timeframe = timeframe
        self.exchange_id = exchange_id
        
        # Initialize clients
        self.binance = BinanceClient(
            api_key=os.getenv('BINANCE_API_KEY'),
            api_secret=os.getenv('BINANCE_API_SECRET')
        )
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(
            f"https://eth-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"
        ))
        
        # Initialize async exchange with longer timeout
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_API_SECRET'),
            'enableRateLimit': True,
            'timeout': 30000,  # 30 seconds timeout
            'options': {
                'defaultType': 'spot',  # Use spot market instead of futures
                'adjustForTimeDifference': True,
                'recvWindow': 60000,  # 60 seconds receive window
                'warnOnFetchOHLCVLimitArgument': False,
                'fetchCurrencies': False  # Skip fetching currencies to avoid rate limits
            }
        })
        
    async def collect_all_data(self) -> pd.DataFrame:
        """Collect all types of data and combine them"""
        try:
            # Initialize exchange markets with retry
            for attempt in range(3):
                try:
                    # Only load markets for the symbols we need
                    markets = {}
                    for symbol in self.symbols:
                        try:
                            # Use fetch_ohlcv instead of fetch_ticker for more reliable data
                            ohlcv = await self.exchange.fetch_ohlcv(
                                symbol,
                                timeframe=self.timeframe,
                                limit=1
                            )
                            if ohlcv and len(ohlcv) > 0:
                                markets[symbol] = {
                                    'last': ohlcv[0][4],  # Use closing price
                                    'timestamp': ohlcv[0][0]
                                }
                            await asyncio.sleep(1)  # Rate limit compliance
                        except Exception as e:
                            logger.warning(f"Error fetching OHLCV for {symbol}: {str(e)}")
                    
                    if not markets:
                        if attempt == 2:
                            raise ValueError("Could not fetch any market data")
                        continue
                    break
                    
                except (ccxt.RequestTimeout, ccxt.ExchangeNotAvailable) as e:
                    if attempt == 2:
                        raise
                    wait_time = 2 ** attempt
                    logger.warning(f"Retrying market load after {wait_time}s, attempt {attempt + 2}")
                    await asyncio.sleep(wait_time)  # Exponential backoff
                    
            # Collect different types of data concurrently
            market_data, onchain_data = await asyncio.gather(
                self.fetch_market_data(),
                self.fetch_onchain_data(),
                return_exceptions=True  # Don't let one failure stop everything
            )
            
            # Handle potential exceptions
            if isinstance(market_data, Exception):
                logger.error(f"Error fetching market data: {str(market_data)}")
                market_data = pd.DataFrame()
            
            if isinstance(onchain_data, Exception):
                logger.error(f"Error fetching onchain data: {str(onchain_data)}")
                onchain_data = pd.DataFrame()
            
            # Combine all data
            if not market_data.empty and not onchain_data.empty:
                combined_data = pd.merge(
                    market_data,
                    onchain_data,
                    left_index=True,
                    right_index=True,
                    how='left'
                )
            elif not market_data.empty:
                combined_data = market_data
            elif not onchain_data.empty:
                combined_data = onchain_data
            else:
                raise ValueError("No data could be collected from any source")
            
            logger.info(f"Collected {len(combined_data)} data points")
            return combined_data
            
        except Exception as e:
            logger.error(f"Error collecting data: {str(e)}")
            raise
        finally:
            try:
                await self.exchange.close()
            except Exception as e:
                logger.error(f"Error closing exchange: {str(e)}")
        
    async def fetch_market_data(self) -> pd.DataFrame:
        """Fetch market data including OHLCV and order book metrics"""
        try:
            all_data = []
            
            for symbol in self.symbols:
                try:
                    # Fetch OHLCV data with retry
                    for attempt in range(3):  # Try 3 times
                        try:
                            ohlcv = await self.exchange.fetch_ohlcv(
                                symbol,
                                timeframe=self.timeframe,
                                limit=1000  # Adjust as needed
                            )
                            break
                        except ccxt.RequestTimeout:
                            if attempt == 2:  # Last attempt
                                raise
                            await asyncio.sleep(1)  # Wait before retry
                            
                    # Convert to DataFrame
                    df = pd.DataFrame(
                        ohlcv,
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    )
                    df['symbol'] = symbol
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    
                    # Add order book metrics with retry
                    for attempt in range(3):  # Try 3 times
                        try:
                            order_book = await self.exchange.fetch_order_book(symbol)
                            df['bid_ask_spread'] = order_book['asks'][0][0] - order_book['bids'][0][0]
                            df['order_book_depth'] = len(order_book['asks']) + len(order_book['bids'])
                            break
                        except ccxt.RequestTimeout:
                            if attempt == 2:  # Last attempt
                                raise
                            await asyncio.sleep(1)  # Wait before retry
                            
                    all_data.append(df)
                    
                except Exception as e:
                    logger.error(f"Error fetching data for {symbol}: {str(e)}")
                    continue
                
            # Combine data from all symbols
            if not all_data:
                raise ValueError("No data collected from any symbol")
                
            market_data = pd.concat(all_data)
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            raise
            
    async def fetch_onchain_data(self) -> pd.DataFrame:
        """Fetch on-chain metrics from Ethereum"""
        try:
            # Get latest block
            latest_block = self.w3.eth.block_number
            
            # Initialize data storage
            blocks_data = []
            
            # Collect data for last 100 blocks
            for block_number in range(latest_block - 100, latest_block + 1):
                try:
                    block = self.w3.eth.get_block(block_number)
                    
                    block_data = {
                        'timestamp': datetime.fromtimestamp(block['timestamp']),
                        'gas_used': block['gasUsed'],
                        'gas_limit': block['gasLimit'],
                        'transaction_count': len(block['transactions']),
                        'base_fee': block['baseFeePerGas'] if 'baseFeePerGas' in block else None
                    }
                    
                    blocks_data.append(block_data)
                    
                except Exception as e:
                    logger.warning(f"Error fetching block {block_number}: {str(e)}")
                    continue
                
            if not blocks_data:
                raise ValueError("No on-chain data collected")
                
            # Convert to DataFrame
            onchain_df = pd.DataFrame(blocks_data)
            onchain_df.set_index('timestamp', inplace=True)
            
            # Resample to match market data timeframe
            onchain_df = onchain_df.resample(self.timeframe).mean()
            
            return onchain_df
            
        except Exception as e:
            logger.error(f"Error fetching on-chain data: {str(e)}")
            raise
            
    async def __aenter__(self):
        """Async context manager entry"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.exchange.close()
        
    def __del__(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'exchange'):
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.exchange.close())
                else:
                    loop.run_until_complete(self.exchange.close())
        except Exception as e:
            logger.error(f"Error closing exchange connection: {str(e)}")
