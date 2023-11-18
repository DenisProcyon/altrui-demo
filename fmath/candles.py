from fmath.conf.cred import CREDS
from binance.client import Client
from binance.enums import HistoricalKlinesType
from datetime import datetime

class   Candles:
    def __init__(self, ticker: str, time_interval: str, futures: bool, time_limit: str = None, currency_mode: bool = False, client = None):
        if client is None:
            self.client = Client(CREDS.get("TEST_API_TOKEN"), CREDS.get("TEST_SECRET_KEY"), testnet=False, requests_params={"timeout": 120})
        else:
            self.client = client
        self.ticker = ticker 
        self.time_interval = time_interval
        self.time_limit = time_limit
        self.futures = futures
        self.currency_mode = currency_mode

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
                "volume": candle[5], 
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

    def get_historical_data(self, start: int, end: int):
        if self.currency_mode:
            return self.get_currency_historical_data(start, end)

        time_interval = self.constants["intervals"][self.time_interval]
        
        if self.futures:
            candles = self.client.get_historical_klines(symbol=self.ticker, interval=time_interval, start_str=start, end_str=end, klines_type=HistoricalKlinesType.FUTURES)
        else:
            candles = self.client.get_historical_klines(self.ticker, time_interval, start_str=start, end_str=end)
        
        candles = self.upgrade_candles(candles)

        return candles