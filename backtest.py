from fmath import strategy
from fmath.candles import Candles
from fmath.instruments import BaseInstrument
from fmath.strategy import BaseStrategy
from random import randint
from pathlib import Path
import json


tickers = [
"RENUSDT",
"REEFUSDT",
"HBARUSDT",
"CELRUSDT",
"FTMUSDT",
"1000SHIBUSDT",
"OMGUSDT"
]


path = Path(__file__).parent / "files/backtest_sessions.json"


start = "1 Oct 2022"
end = "1 Nov 2022"

def update_sessions(session: dict):
    with open(path) as file:
        sessions = json.load(file)

    sessions.append(session)

    with open(path, "w") as file:
        json.dump(sessions, file)

session = {
    "id": randint(100000, 999999),
    "result": [],
    "info": "Demo Session",
}

for ticker in tickers.copy():
    print(ticker)

    candles = Candles(ticker=ticker, time_interval="15min", futures=True).get_historical_data(start, end)

    decision_path = [
        [
        "ATR", 40,
        ">", 0.00010714653399190865
        ],
        [
        "BETA_SCORE", 45,
        ">", 1.1939647793769836
        ]
    ]

    instrument = BaseInstrument(
        name="DecisionTree",
        candles=candles,
        ticker=ticker,
        additional_config={
            "decision_path": decision_path,
            "mode": "buy",
        }
    )

    data = instrument.apply()

    strategy = BaseStrategy(
        name="KSReversal",
        ticker=ticker,
        data=data,
        tp=1.02,
        sl=0.98,
        complex_watch=False
    )

    result = strategy.apply()
    
    session["result"].append(result)

update_sessions(session=session)
