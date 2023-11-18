from atexit import register
from fmath.candles import Candles
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
from matplotlib.dates import date2num
import matplotlib.ticker as mticker

def get_candles():
    start, end = "30 Jan 2023", "5 Feb 2023"
    candles = Candles(ticker="MATICUSDT", time_interval="1h", futures=True).get_historical_data(start, end)
    
    return pd.DataFrame(candles)

def get_reference_price(data: pd.DataFrame):
    for i in range(len(data)):
        if "00:00" in data["open_time"].iloc[i]:
            return data["open"].iloc[i]

def build_grid(data: pd.DataFrame,threshold: float):
    reference_price = float(get_reference_price(data=data))
    long_positions = []
    short_positions = []
    for i in range(1, 4):
        long_positions.append(
            {
                reference_price + reference_price*threshold*i: reference_price + reference_price*threshold*(i+1)
            }
        )
        short_positions.append(
            {
                reference_price - reference_price*threshold*i: reference_price - reference_price*threshold*(i+1)
            }
        )
    
    print({"long": long_positions, "short": short_positions, "reference": reference_price})
    return {"long": long_positions, "short": short_positions, "reference": reference_price} 

def plot_candles(candles: pd.DataFrame, grid_data: dict):
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
    for grid_level in grid_data['long']:
        for open_price, close_price in grid_level.items():
            ax.axhline(open_price, color='green', linewidth=0.75, linestyle="--")
            ax.axhline(close_price, color='green', linewidth=0.75, linestyle="--")
            
    for grid_level in grid_data['short']:
        for open_price, close_price in grid_level.items():
            ax.axhline(open_price, color='red', linewidth=0.75, linestyle="--")
            ax.axhline(close_price, color='red', linewidth=0.75, linestyle="--")
            
    ax.axhline(grid_data['reference'], color='black', linewidth=1)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
def main():
    candles = get_candles()
    threshold = 0.03

    grid = build_grid(
        data=candles,
        threshold=threshold
    )

    plot_candles(candles=candles, grid_data=grid)

    
if __name__ == "__main__":
    main()