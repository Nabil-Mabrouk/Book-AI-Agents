# live_data_feed.py
import asyncio
import json
import websockets
from pydantic import BaseModel
from typing import List

class KlineUpdate(BaseModel):
    """A Pydantic model for incoming 1-minute Kline (candlestick) data."""
    symbol: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    is_closed: bool

async def binance_multi_kline_ticker(symbols: List[str]):
    """
    Connects to a single Binance WebSocket and subscribes to multiple 1-minute
    Kline streams (e.g., for BTC, ETH, etc.).
    """
    # 1. Format the stream names for the URL
    #    e.g., ['btcusdt@kline_1m', 'ethusdt@kline_1m']
    stream_names = [f"{s.lower()}usdt@kline_1m" for s in symbols]
    
    # 2. Join them into the path for a combined stream URL
    #    The URL format is wss://stream.binance.com:9443/stream?streams=stream1/stream2/stream3
    websocket_url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(stream_names)}"
    
    while True: # Main loop to handle reconnections
        try:
            print(f"Connecting to Binance multi-stream WebSocket...")
            async with websockets.connect(websocket_url) as websocket:
                print("Connection successful. Streaming live Kline data for:", ", ".join(symbols))
                async for message in websocket:
                    # 3. Parse the combined stream's message format
                    #    The payload is now: {"stream":"<stream_name>","data":{...}}
                    data = json.loads(message)
                    
                    # Extract the actual Kline data from the 'data' key
                    kline_payload = data.get('data', {})
                    kline_data = kline_payload.get('k', {})
                    
                    if kline_data and kline_data.get('x'): # Check if the candlestick is closed
                        update = KlineUpdate(
                            symbol=kline_data['s'],
                            open_price=float(kline_data['o']),
                            high_price=float(kline_data['h']),
                            low_price=float(kline_data['l']),
                            close_price=float(kline_data['c']),
                            volume=float(kline_data['v']),
                            is_closed=kline_data['x']
                        )
                        yield update
                        
        except (websockets.exceptions.ConnectionClosedError, asyncio.TimeoutError) as e:
            print(f"WebSocket connection error: {e}. Attempting to reconnect in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Attempting to reconnect in 5 seconds...")
            await asyncio.sleep(5)