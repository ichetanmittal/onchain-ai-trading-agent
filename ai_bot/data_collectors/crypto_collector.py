import os
import logging
import asyncio
import aiohttp
import hmac
import hashlib
import time
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class CryptoDataCollector:
    """Collects cryptocurrency data from various sources"""
    
    def __init__(self, symbols: List[str], timeframe: str = '1h'):
        """
        Initialize the collector
        
        Args:
            symbols: List of trading pairs (e.g., ['BTC/USDT', 'ETH/USDT'])
            timeframe: Data timeframe (e.g., '1h', '4h', '1d')
        """
        self.symbols = [s.replace('/', '') for s in symbols]  # Convert BTC/USDT to BTCUSDT
        self.timeframe = self._convert_timeframe(timeframe)
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        self.base_urls = [
            'https://api.binance.com',
            'https://api1.binance.com',
            'https://api2.binance.com',
            'https://api3.binance.com'
        ]
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(
            f"https://eth-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"
        ))
        
    def _convert_timeframe(self, timeframe: str) -> str:
        """Convert CCXT timeframe to Binance format"""
        mapping = {
            '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m',
            '30m': '30m', '1h': '1h', '2h': '2h', '4h': '4h',
            '6h': '6h', '8h': '8h', '12h': '12h', '1d': '1d',
            '3d': '3d', '1w': '1w', '1M': '1M'
        }
        return mapping.get(timeframe, '1h')
        
    def _get_signature(self, params: Dict[str, Any]) -> str:
        """Generate signature for authenticated endpoints"""
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
    async def _make_request(self, session: aiohttp.ClientSession, endpoint: str, 
                          params: Dict[str, Any] = None, signed: bool = False) -> Dict:
        """Make request to Binance API with fallback to alternative endpoints"""
        if params is None:
            params = {}
            
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._get_signature(params)
            
        headers = {'X-MBX-APIKEY': self.api_key} if signed else {}
        
        # Try each base URL in sequence
        last_error = None
        for base_url in self.base_urls:
            url = f"{base_url}{endpoint}"
            try:
                async with session.get(url, params=params, headers=headers, timeout=10) as response:
                    if response.status == 429:  # Rate limit
                        retry_after = int(response.headers.get('Retry-After', 5))
                        await asyncio.sleep(retry_after)
                        continue
                        
                    response.raise_for_status()
                    return await response.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                logger.warning(f"Failed to connect to {base_url}: {str(e)}")
                continue
                
        # If we get here, all endpoints failed
        logger.error(f"All Binance API endpoints failed: {str(last_error)}")
        raise last_error
            
    async def collect_data(self) -> pd.DataFrame:
        """Collect market data from Binance"""
        try:
            async with aiohttp.ClientSession() as session:
                all_data = []
                
                # Get klines data for each symbol
                for symbol in self.symbols:
                    endpoint = '/api/v3/klines'
                    params = {
                        'symbol': symbol,
                        'interval': self.timeframe,
                        'limit': 2000  # Maximum allowed by Binance
                    }
                    
                    data = await self._make_request(session, endpoint, params)
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(data, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
                        'taker_buy_quote_volume', 'ignore'
                    ])
                    
                    # Clean up data
                    df = df.drop(['close_time', 'ignore'], axis=1)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df['symbol'] = symbol.replace('USDT', '/USDT')  # Convert back to BTC/USDT format
                    
                    # Convert string columns to float
                    for col in ['open', 'high', 'low', 'close', 'volume', 'quote_volume',
                              'trades', 'taker_buy_volume', 'taker_buy_quote_volume']:
                        df[col] = df[col].astype(float)
                    
                    all_data.append(df)
                
                # Combine all symbols' data
                combined_df = pd.concat(all_data, ignore_index=True)
                
                logger.info(f"Collected {len(combined_df)} data points")
                return combined_df
                
        except Exception as e:
            logger.error(f"Error collecting market data: {str(e)}")
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

    async def collect_all_data(self) -> pd.DataFrame:
        """Collect all types of data and combine them"""
        try:
            market_data = await self.collect_data()
            onchain_data = await self.fetch_onchain_data()
            
            if not market_data.empty and not onchain_data.empty:
                combined_data = pd.merge(
                    market_data,
                    onchain_data,
                    left_index=True,
                    right_index=True,
                    how='left'
                )
            else:
                combined_data = market_data
                
            logger.info(f"Collected {len(combined_data)} data points")
            return combined_data
                
        except Exception as e:
            logger.error(f"Error collecting data: {str(e)}")
            raise
