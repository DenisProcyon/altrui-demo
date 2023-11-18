from fmath.grid import GridHighTradeWindow, GridBuilder
from fmath.strategy.grid_strategy import GridStrategy
from random import randint
import json
from pathlib import Path

path = Path(__file__).parent / "files/backtest_sessions.json"


tickers = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOTUSDT",
    "MATICUSDT",
    "ATOMUSDT",
    "LTCUSDT",
    "LINKUSDT",
    "IOTAUSDT",
    "SOLUSDT",
]

session = {
    "id": randint(100000, 999999),
    "result": []
}

def update_sessions(session: dict):
    with open(path) as file:
        sessions = json.load(file)

    sessions.append(session)

    with open(path, "w") as file:
        json.dump(sessions, file)


for ticker in tickers:
    grid_windows = GridHighTradeWindow(ticker=ticker, start="1 Apr 2023", end="1 Jun 2023", timeframe="15min").get_grid_sessions()

    results = []
    for grid_window in grid_windows:
        builder = GridBuilder(threshold=0.003, grid_size=4, grid_tw=grid_window)
        window_result = builder.build()
        results.append(window_result)

    strategy = GridStrategy(data=results, ticker=ticker).apply()

    session["result"].append(strategy)

update_sessions(session)

