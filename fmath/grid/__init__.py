import pandas as pd
from fmath.candles import Candles
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
from matplotlib.dates import date2num


class GridLowTradeWindow:
    def __init__(self, candles: pd.DataFrame):
        self.candles = candles

    def get_candles(self):
        return self.candles
    
    def plot(self):
        candles = self.get_candles()
        #print(self.grid_data)

        candles['open_time'] = pd.to_datetime(candles['open_time'], format='%d/%m/%Y %H:%M:%S')
        candles['date_num'] = date2num(candles['open_time'].dt.to_pydatetime())

        candles['open'] = pd.to_numeric(candles['open'])
        candles['high'] = pd.to_numeric(candles['high'])
        candles['low'] = pd.to_numeric(candles['low'])
        candles['close'] = pd.to_numeric(candles['close'])

        fig, ax = plt.subplots()

        quotes = [tuple(x) for x in candles[['date_num', 'open', 'high', 'low', 'close']].values]

        candlestick_ohlc(ax, quotes, width=0.03, colorup='blue', colordown='black')

        # Add grid levels
        for grid_level in self.grid_data['long_positions']:
                ax.axhline(grid_level["activation_price"], color='green', linewidth=0.75, linestyle="--")
                
                
        for grid_level in self.grid_data['short_positions']:
            ax.axhline(grid_level["activation_price"], color='red', linewidth=0.75, linestyle="--")
                
                
        ax.axhline(self.grid_data['reference_price'], color='black', linewidth=1)

        plt.xticks(rotation=45)
        plt.tight_layout()

        plt.show()

class GridHighTradeWindow:
    def __init__(self, ticker: str, start: str, end: str, timeframe: str):
        self.start = start
        self.end = end
        self.ticker = ticker
        self.tf = timeframe
        
    def get_grid_sessions(self) -> list[GridLowTradeWindow]:
        candles = Candles(ticker=self.ticker, time_interval=self.tf, futures=True).get_historical_data(self.start, self.end)
        candles = pd.DataFrame(candles)
        
        grid_sessions = []
        started = False
        for i in range(len(candles)):
            if "18:00" in candles["open_time"].iloc[i] and not started:
                started = True
                start_index = i
            if "03:00" in candles["open_time"].iloc[i] and started:
                started = False
                grid_sessions.append(GridLowTradeWindow(candles=candles.iloc[start_index:i]))

        return grid_sessions

         
class GridBuilder:
    def __init__(self, threshold: float, grid_size: int, grid_tw: GridLowTradeWindow):
        self.threshold = threshold
        self.grid_size = grid_size
        self.grid_tw = grid_tw

    def build(self):
        candles = self.grid_tw.get_candles()

        long_positions = []
        short_positions = []
        reference_price = candles["open"].iloc[0]
        for i in range(1, self.grid_size):
            long_positions.append(
                {
                    "activation_price": reference_price + reference_price*self.threshold*i,
                    "tp_price": reference_price + reference_price*self.threshold*(i+1),
                    "sl_price": reference_price - reference_price*self.threshold*(self.grid_size),
                    "priority": i
                }
            )
            short_positions.append(
                {
                    "activation_price": reference_price - reference_price*self.threshold*i,
                    "tp_price": reference_price - reference_price*self.threshold*(i+1),
                    "sl_price": reference_price + reference_price*self.threshold*(self.grid_size),
                    "priority": i
                }
            )

        result = {
            "long_positions": long_positions,
            "short_positions": short_positions,
            "reference_price": reference_price
        }

        self.grid_tw.grid_data = result

        return self.grid_tw


