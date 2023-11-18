from fmath.candles import Candles
from datetime import datetime
import pandas as pd
from fmath.grid import GridLowTradeWindow
import copy
from fmath.conf.cred import CREDS
from binance.client import Client

client = Client(CREDS.get("TEST_API_TOKEN"), CREDS.get("TEST_SECRET_KEY"), testnet=False)

class GridStrategy:
    def __init__(self, data: list, ticker: str) -> None:
        self.data = data
        self.ticker = ticker
    

    def open_pos(self, candles: list[dict], order_price: float, type: str, tp_price: float, sl_price: float, priority: int):
        if len(candles) == 0:
            return
        for candle in candles:
            current_price = candle["open"]
            if type == "short":
                price_change = order_price / float(candle["open"])
                if current_price <= tp_price:
                    return {
                        "success": True,
                        "profit_pc": round(float((price_change - 1) * 100), 3),
                        "close_price": current_price,
                        "start_timestamp": candles[0]["close_time"],
                        "timestamp": candle["close_time"],
                        "order_price": order_price,
                        "type": type,
                        "out_of_time": False,
                        "priority": priority
                    }
                if current_price >= sl_price:
                    return {
                        "success": False,
                        "loss_pc": round(float((1 - price_change) * 100), 3),
                        "close_price": current_price,
                        "start_timestamp": candles[0]["close_time"],
                        "timestamp": candle["close_time"],
                        "order_price": order_price,
                        "type": type,
                        "out_of_time": False,
                        "priority": priority
                    }
            else:
                price_change = float(candle["open"]) / order_price
                if current_price >= tp_price:
                    return {
                        "success": True,
                        "profit_pc": round(float((price_change - 1) * 100), 3),
                        "close_price": current_price,
                        "start_timestamp": candles[0]["close_time"],
                        "timestamp": candle["close_time"],
                        "order_price": order_price,
                        "type": type,
                        "out_of_time": False,
                        "priority": priority
                    }
                if current_price <= sl_price:
                    return {
                        "success": False,
                        "loss_pc": round(float((1 - price_change) * 100), 3),
                        "close_price": current_price,
                        "start_timestamp": candles[0]["close_time"],
                        "timestamp": candle["close_time"],
                        "order_price": order_price,
                        "type": type,
                        "out_of_time": False,
                        "priority": priority
                    }
        
        if type == "short":
            price_change = order_price / current_price
            if price_change >= 1:
                return {
                    "success": True,
                    "profit_pc": round(float((price_change - 1) * 100), 3),
                    "close_price": current_price,
                    "start_timestamp": candles[0]["close_time"],
                    "timestamp": candles[-1]["close_time"],
                    "order_price": order_price,
                    "type": type,
                    "out_of_time": True,
                    "priority": priority
                }
            if price_change <= 1:
                return {
                    "success": False,
                    "loss_pc": round(float((1 - price_change) * 100), 3),
                    "close_price": current_price,
                    "start_timestamp": candles[0]["close_time"],
                    "timestamp": candles[-1]["close_time"],
                    "order_price": order_price,
                    "type": type,
                    "out_of_time": True,
                    "priority": priority
                }
        else:
            price_change = current_price / order_price
            if price_change >= 1:
                return {
                    "success": True,
                    "profit_pc": round(float((price_change - 1) * 100), 3),
                    "close_price": current_price,
                    "start_timestamp": candles[0]["close_time"],
                    "timestamp": candles[-1]["close_time"],
                    "order_price": order_price,
                    "type": type,
                    "out_of_time": True,
                    "priority": priority
                }
            if price_change <= 1:
                return {
                    "success": False,
                    "loss_pc": round(float((1 - price_change) * 100), 3),
                    "close_price": current_price,
                    "start_timestamp": candles[0]["close_time"],
                    "timestamp": candles[-1]["close_time"],
                    "order_price": order_price,
                    "type": type,
                    "out_of_time": True,
                    "priority": priority
                }

                

    def process_window(self, data: GridLowTradeWindow):
        start = str(data.candles["close_time"].iloc[0])
        end = str(data.candles["close_time"].iloc[-1])

        grid_data = copy.deepcopy(data.grid_data)
        
        result = []
        short_candles = Candles(client=client, ticker=self.ticker, time_interval="1min", futures=True).get_historical_data(start=start, end=end)
        for candle in short_candles:
            current_price = candle["open"]
            if current_price > grid_data["reference_price"]:
                if len(grid_data["long_positions"]) == 0:
                    continue
                target_price = grid_data["long_positions"][0]["activation_price"]
                if current_price >= target_price:
                    pos_result = self.open_pos(
                        candles=short_candles[short_candles.index(candle)+1:],
                        order_price=current_price, 
                        type="long", 
                        tp_price=grid_data["long_positions"][0]["tp_price"], 
                        sl_price=grid_data["long_positions"][0]["sl_price"],
                        priority=grid_data["long_positions"][0]["priority"]
                    )
                    if pos_result is not None:
                        result.append(pos_result)
                        print(f'Position was opened for {current_price} for long and closed at {pos_result["close_price"]} success - {pos_result["success"]}')
                    del grid_data["long_positions"][0]
            else:
                if len(grid_data["short_positions"]) == 0:
                    continue
                target_price = grid_data["short_positions"][0]["activation_price"]
                if current_price <= target_price:
                    pos_result = self.open_pos(
                        candles=short_candles[short_candles.index(candle)+1:],
                        order_price=current_price, 
                        type="short", 
                        tp_price=grid_data["short_positions"][0]["tp_price"], 
                        sl_price=grid_data["short_positions"][0]["sl_price"],
                        priority=grid_data["short_positions"][0]["priority"]
                    )
                    if pos_result is not None:
                        result.append(pos_result)
                        print(f'Position was opened for {current_price} for short and closed at {pos_result["close_price"]} success - {pos_result["success"]}')
                    del grid_data["short_positions"][0]
    
            
        return result
        

    def apply(self):
        result = {
            "ticker": self.ticker,
            "positions": []
        }

        for window in self.data:
            window_result = self.process_window(data=window)
            result["positions"] = result["positions"] + window_result
            print(f'{self.data.index(window)} / {len(self.data)}')

        return result