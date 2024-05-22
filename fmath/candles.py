from fmath.conf.cred import CREDS
from binance.client import Client
from binance.enums import HistoricalKlinesType
from datetime import datetime

import pandas as pd
import numpy as np
from pathlib import Path
import os


class Candles:
    def __init__(self, ticker: str, time_interval: str, futures: bool, time_limit: str = None, currency_mode: bool = False, client = None):
        if client is None:
            self.client = Client(CREDS.get("TEST_API_TOKEN"), CREDS.get("TEST_SECRET_KEY"), testnet=False, requests_params={"timeout": 120})
        else:
            self.client = client
        self.ticker = ticker 
        self.time_interval = time_interval
        self.time_limit = time_limit
        self.futures = futures

    @property
    def constants(self):
        return {
            "intervals": {
                "1min": Client.KLINE_INTERVAL_1MINUTE,
                "3min": Client.KLINE_INTERVAL_3MINUTE,
                "5min": Client.KLINE_INTERVAL_5MINUTE,
                "15min": Client.KLINE_INTERVAL_15MINUTE,
                "30min": Client.KLINE_INTERVAL_30MINUTE,
                "1h": Client.KLINE_INTERVAL_1HOUR,
                "2h": Client.KLINE_INTERVAL_2HOUR,
                "4h": Client.KLINE_INTERVAL_4HOUR,
                "8h": Client.KLINE_INTERVAL_8HOUR,
                "12h": Client.KLINE_INTERVAL_12HOUR,
                "1d": Client.KLINE_INTERVAL_1DAY,
                "1w": Client.KLINE_INTERVAL_1WEEK
            }
        }
    
    def upgrade_candles(self, candles: list[dict]):
        smart_candles = []
        for candle in candles:
            smart_candles.append({
                "open_time": datetime.fromtimestamp(candle[0]/1000).strftime("%d/%m/%Y %H:%M:%S"), 
                "open": float(candle[1]),
                "high": float(candle[2]), "low" : float(candle[3]), 
                "close": float(candle[4]),
                "volume": float(candle[5]), 
                "close_time": candle[6],
                "quote_asset_volume": float(candle[7]),
                "number_of_trades": float(candle[8]), 
                "taker_buy_base_asset_volume": float(candle[9]),
                "taker_buy_quote_asset_volume": float(candle[10])
            })

        return smart_candles

    def get_data(self) -> dict:

        """
        This function returns number of candles 
        for given ticker and time marker 
        """

        time_interval = self.constants["intervals"][self.time_interval]

        if self.futures:
            candles = self.client.futures_klines(symbol=self.ticker, interval=time_interval, limit=self.time_limit)
        else:
            candles = self.client.get_klines(symbol=self.ticker, interval=time_interval, limit=self.time_limit)

        candles = self.upgrade_candles(candles)

        return candles
    
    def get_from_storage(self, file: Path, start_s: int, end_s: int):
        candles = pd.read_csv(file)

        target_candles = candles[(candles["close_time"] >= start_s) & (candles["close_time"] <= end_s)]

        return target_candles
    
    def put_to_storage(self, data: list[dict], start_s: int, end_s: int):
        data.to_csv(Path(f'./candles_storage/{self.ticker}_{self.time_interval}_{start_s}_{end_s}.csv'), index=False)

    def get_historical_data(self, start: str, end: str):
        try:
            start_s = int(datetime.timestamp(datetime.strptime(start, "%d %b %Y")) * 1000)
            end_s = int(datetime.timestamp(datetime.strptime(end, "%d %b %Y")) * 1000)
        except ValueError as e:
            start_s = int(float(start))
            end_s = int(float(end))
            
        dir_path = Path("./candles_storage")

        from_storage = False
        for file in dir_path.rglob("*.csv"):
            file_name = str(file).split("/")[-1]
            ticker, time_int, start_ts, end_ts = [i.replace(".csv", "") for i in file_name.split("_")]
            if ticker == self.ticker and time_int == self.time_interval and int(start_ts) <= start_s and int(end_ts) >= end_s:
                candles = self.get_from_storage(file=file, start_s=start_s, end_s=end_s)
                print(f'Got candles from {file_name}')
                return candles
        
        time_interval = self.constants["intervals"][self.time_interval]
        
        if self.futures:
            candles = self.client.get_historical_klines(symbol=self.ticker, interval=time_interval, start_str=start, end_str=end, klines_type=HistoricalKlinesType.FUTURES)
        else:
            candles = self.client.get_historical_klines(self.ticker, time_interval, start_str=start, end_str=end)
        
        candles = pd.DataFrame(self.upgrade_candles(candles))

        if not from_storage:
            self.put_to_storage(data=candles, start_s=start_s, end_s=end_s)

        return candles

            
