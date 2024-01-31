from pathlib import Path
import json
import pandas as pd
from matplotlib import pyplot as plt
from collections import defaultdict

tickers_results = {}

class Wallet:
    def __init__(self, balance: float | int, leverage, order_size: float, session_id: int, liq_p: float|int = None, isolated: bool = False):
        self.market_fee = 0.04 / 100
        self.balance = balance
        self.session_id = session_id
        self.order_size = order_size
        self.opened_positions = []
        self.balance_history = []
        self.leverage = leverage
        self.isolated = isolated
        self.liq_p = liq_p
        self.path = Path(__file__).parent.parent / "files/backtest_sessions.json"
    

    def close_position(self, position: dict):
        for opened_position in self.opened_positions:
            if position["id"] == opened_position["id"]:
                if position.get("success"):
                    commission = opened_position["commission"] * (1 - position["profit_pc"] / 100)
                    self.balance = self.balance - commission 

                    profit = opened_position["position_size"] * (position["profit_pc"] / 100)
                    self.balance = self.balance + profit 
                    if position["ticker"] in tickers_results:
                        tickers_results[position["ticker"]] = tickers_results[position["ticker"]] + profit 
                    else:
                        tickers_results[position["ticker"]] = profit 
                    self.balance_history.append((self.balance, position["timestamp"]))
                else:
                    if self.isolated:
                        if position["loss_pc"] > self.liq_p:
                            position["loss_pc"] = self.liq_p
                    commission = opened_position["commission"] * (1 + position["loss_pc"] / 100)
                    self.balance = self.balance - commission 
                    
                    loss = opened_position["position_size"] * (position["loss_pc"] / 100)
                    self.balance = self.balance - loss 
                    if position["ticker"] in tickers_results:
                        tickers_results[position["ticker"]] = tickers_results[position["ticker"]] - loss 
                    else:
                        tickers_results[position["ticker"]] = 0 - loss
                    self.balance_history.append((self.balance, position["timestamp"]))
                

    def open_position(self, position: dict):
        position_size = self.balance * self.order_size * self.leverage
        
        commission = position_size * self.market_fee
        self.balance = self.balance - commission
            
        
        self.opened_positions.append(
            {
                "ticker": position["ticker"],
                "position_size": position_size,
                "commission": commission,
                "id": position["id"]
            }
        )

    def save_graph(self):
        balance_history = pd.DataFrame(self.balance_history, columns=["Balance", "Time"])

        balance_history["Time"] = pd.to_datetime(balance_history["Time"], unit="ms")

        balance_history.plot(x="Time", y="Balance")
        plt.savefig(f'balance_for_{self.session_id}.png')

    def launch_timeline(self, positions: list[dict], activities: list[int]):
        timestamp_positions = defaultdict(list)
        start_timestamp_positions = defaultdict(list)
        for position in positions:
            timestamp_positions[position["timestamp"]].append(position)
            start_timestamp_positions[position["start_timestamp"]].append(position)

        open_history = []
        opened = 0
        activities_len = len(activities)
        for index, activity in enumerate(activities):
            if activity in timestamp_positions:
                for position in timestamp_positions[activity]:
                    self.close_position(position)
                    opened -= 1
                    open_history.append(opened)
            if activity in start_timestamp_positions:
                for position in start_timestamp_positions[activity]:
                    self.open_position(position)
                    opened += 1
                    open_history.append(opened)
            if index % 1000 == 0: 
                print(f'{index} / {activities_len}')

        self.save_graph()
        print(self.balance)
        print(f'Max open - {max(open_history)}')
        
        print({ticker: b for ticker, b in sorted(tickers_results.items(), key=lambda item: item[1])})

    def get_positions(self) -> list[dict]:
        with open(self.path) as file:
            data = json.load(file)

        combined = []
        for session in data:
            if session["id"] == self.session_id:
                session_result = session["result"]
                for ticker_positions in session_result:
                    for position in ticker_positions["positions"]:
                        position["ticker"] = ticker_positions["ticker"]
                        combined.append(position)

        for index, position in enumerate(combined):
            position["id"] = index

        return combined

    def sort_positions(self, positions: list[dict]):
        activity_times = []
        for position in positions:
            activity_times = activity_times + [position["timestamp"], position["start_timestamp"]]

        activity_times.sort()
        
        return list(dict.fromkeys(activity_times))

    def calculate(self):
        positions = self.get_positions()

        activities = self.sort_positions(positions)

        self.launch_timeline(positions=positions, activities=activities)
        
        pp = []
        lp = []
        for position in positions:
            if position["success"]:
                pp.append(position["profit_pc"])
            else:
                lp.append(position["loss_pc"])

                
        print(f'PP - {len(pp)}, avg p - {sum(pp) / len(pp)}')
        print(f'LP - {len(lp)}, avf l - {sum(lp) / len(lp)}')

        for position in positions:
            if position["success"]:
                if position["profit_pc"] == max(pp):
                    print(position)
            else:
                if position["loss_pc"] == max(lp):
                    print(position)
                if position["loss_pc"] == min(lp):
                    print(position)
                    break

wallet = Wallet(balance=1000, leverage=10, order_size=0.01, session_id=786202)
wallet.calculate()