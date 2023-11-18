import pandas as pd
from fmath.candles import Candles
from datetime import datetime


class BaseStrategy:
    def __init__(self, name: str, ticker: str, data: pd.DataFrame, tp: dict, sl: dict, complex_watch: bool = False):
        self.name = name
        self.ticker = ticker
        self.data = data
        self.tp = tp
        self.sl = sl
        self.complex_watch = complex_watch
        if self.complex_watch:
            start = int(datetime.strptime(data["open_time"].iloc[0], "%d/%m/%Y %H:%M:%S").timestamp() * 1000)
            end = data["close_time"].iloc[-1]
        
            self.short_candles = Candles(ticker=self.ticker, time_interval="5min", futures=True).get_historical_data(start=str(start), end=str(end))

        self.result = {
            "ticker": ticker,
            "positions": [],
            "time_range": f'{data["open_time"].iloc[0]} - {data["open_time"].iloc[-1]}',
            "streaks": {}
        }

    def minute_watch(self, data: pd.DataFrame, order_price: float, type: str, **kwargs):
        local_start = data["open_time"].iloc[0]
        local_end = data["close_time"].iloc[-1]

        for i, short_candle in enumerate(self.short_candles):
            if short_candle["open_time"] == local_start:
                start_index = i
            if short_candle["close_time"] == local_end:
                end_index = i
                break

        try:
            local_short_candles = pd.DataFrame(self.short_candles[start_index:end_index+1])
        except UnboundLocalError:
            end_index = i
        except Exception as e:
            return None

        wt = 0
        change_history = []
        for i in range(1, len(local_short_candles)):
            result = {
                "timestamp": int(local_short_candles["close_time"].iloc[i]), 
                "type": type,
                "order_price": float(order_price), 
                "close_price": float(local_short_candles["open"].iloc[i]),
                "start_timestamp": int(datetime.strptime(local_start, "%d/%m/%Y %H:%M:%S").timestamp() * 1000), 
            }
            if type == "long":
                price_change = float(local_short_candles["open"].iloc[i]) / order_price
                change_history.append(price_change)
                if price_change >= self.tp:
                    result["wt"] = wt
                    result["max_profit"] = max(change_history)
                    result["success"] = True
                    result["profit_pc"] = round(float((price_change - 1) * 100), 3)
                    result["out_of_time"] = False

                    return result
                if price_change <= self.sl:
                    result["wt"] = wt
                    result["max_profit"] = max(change_history)
                    result["success"] = False
                    result["loss_pc"] = round(float((1 - price_change) * 100), 3)
                    result["out_of_time"] = False

                    return result
            else:
                price_change = order_price / float(local_short_candles["open"].iloc[i])
                change_history.append(price_change)
                if price_change >= self.tp:
                    result["wt"] = wt
                    result["max_profit"] = max(change_history)
                    result["success"] = True
                    result["profit_pc"] = round(float((price_change - 1) * 100), 3)
                    result["out_of_time"] = False

                    return result
                if price_change <= self.sl:
                    result["wt"] = wt
                    result["max_profit"] = max(change_history)
                    result["success"] = False
                    result["loss_pc"] = round(float((1 - price_change) * 100), 3)
                    result["out_of_time"] = False

                    return result
            
        if price_change > 1:
            result["wt"] = wt
            result["max_profit"] = max(change_history)
            result["success"] = True
            result["profit_pc"] = round(float((price_change - 1) * 100), 3)
            result["out_of_time"] = True

            return result
        else:
            result["wt"] = wt
            result["max_profit"] = max(change_history)
            result["success"] = False
            result["loss_pc"] = round(float((1 - price_change) * 100), 3)
            result["out_of_time"] = True

            return result

    def simple_watch(self, data: pd.DataFrame, order_price: float, order_index: int, type: str, **kwargs):
        if self.complex_watch:
            result = self.minute_watch(data=data, order_price=order_price, type=type, kwargs=kwargs)

            return result
        wt = 0
        change_history = []
        if kwargs.get("tp") is not None:
            self.tp = kwargs["tp"]
        if kwargs.get("sl") is not None:
            self.sl = kwargs["sl"]
        signal_timestamp = str(self.data["close_time"].iloc[order_index-1])
        if len(data) < 2:
            return None
        for i in range(1, len(data)):
            wt = wt + 1
            result = {
                "timestamp": int(data["close_time"].iloc[i]), 
                "type": type,
                "order_price": float(order_price), 
                "close_price": float(data["open"].iloc[i]),
                "start_timestamp": int(signal_timestamp), 
            }
            if type == "long":
                price_change = float(data["open"].iloc[i]) / order_price
                change_history.append(price_change)
                if price_change >= self.tp:
                    result["wt"] = wt
                    result["max_profit"] = max(change_history)
                    result["success"] = True
                    result["profit_pc"] = round(float((price_change - 1) * 100), 3)
                    result["out_of_time"] = False

                    return result
                if price_change <= self.sl:
                    result["wt"] = wt
                    result["max_profit"] = max(change_history)
                    result["success"] = False
                    result["loss_pc"] = round(float((1 - price_change) * 100), 3)
                    result["out_of_time"] = False

                    return result
            else:
                price_change = order_price / float(data["open"].iloc[i])
                change_history.append(price_change)
                if price_change >= self.tp:
                    result["wt"] = wt
                    result["max_profit"] = max(change_history)
                    result["success"] = True
                    result["profit_pc"] = round(float((price_change - 1) * 100), 3)
                    result["out_of_time"] = False

                    return result
                if price_change <= self.sl:
                    result["wt"] = wt
                    result["max_profit"] = max(change_history)
                    result["success"] = False
                    result["loss_pc"] = round(float((1 - price_change) * 100), 3)
                    result["out_of_time"] = False

                    return result
            
        if price_change > 1:
            result["wt"] = wt
            result["max_profit"] = max(change_history)
            result["success"] = True
            result["profit_pc"] = round(float((price_change - 1) * 100), 3)
            result["out_of_time"] = True

            return result
        else:
            result["wt"] = wt
            result["max_profit"] = max(change_history)
            result["success"] = False
            result["loss_pc"] = round(float((1 - price_change) * 100), 3)
            result["out_of_time"] = True

            return result
    
    def long_watch(self, data: pd.DataFrame, order_price: float, order_index: int, type: str):
        wt = 0
        signal_timestamp = str(self.data["close_time"].iloc[order_index-1])
        for i in range(order_index, len(data)):
            wt = wt + 1
            result = {
                "timestamp": int(data["close_time"].iloc[i]), 
                "type": type,
                "order_price": float(order_price), 
                "close_price": float(data["open"].iloc[i]),
                "start_timestamp": int(signal_timestamp), 
            }
            if type == "short":
                if data["crs"].iloc[i] == 1:
                    price_change = order_price / float(data["open"].iloc[i])
                    if price_change > 1:
                        result["wt"] = wt
                        result["success"] = True
                        result["profit_pc"] = round(float((price_change - 1) * 100), 3)
                        result["out_of_time"] = True

                        return result
                    else:
                        result["wt"] = wt
                        result["success"] = False
                        result["loss_pc"] = round(float((1 - price_change) * 100), 3)
                        result["out_of_time"] = True

                        return result
            else:
                if data["crs"].iloc[i] == -1:
                    price_change = float(data["open"].iloc[i]) / order_price
                    if price_change > 1:
                        result["wt"] = wt
                        result["success"] = True
                        result["profit_pc"] = round(float((price_change - 1) * 100), 3)
                        result["out_of_time"] = True

                        return result
                    else:
                        result["wt"] = wt
                        result["success"] = False
                        result["loss_pc"] = round(float((1 - price_change) * 100), 3)
                        result["out_of_time"] = True

                        return result

    def apply(self):
        match self.name:
            case "KSReversal": 
                return KSReversalStrategy.calculate(self)
            case "SwingStrategy":
                raise NotImplementedError # Not in Demo

class KSReversalStrategy(BaseStrategy):
    def get_last_profit(self, poslen: int, postype: str):
        result = 0
        for position in self.result["positions"][-poslen:]:
            if position["type"] == postype:
                if position["success"]:
                    result = result + 1

        return result

    def calculate(self):
        candles = self.data
        for i in range(len(candles)):
            if candles["s_signals"].iloc[i] != 0:
                result = self.simple_watch(
                    data=candles.iloc[i:i+250],
                    order_price=candles["close"].iloc[i],
                    order_index=i,
                    type="short"
                )
                if result is not None:
                    if result["success"]:
                        print(f'Profit - {result["profit_pc"]}% max profit - {result["max_profit"]}, wt - {result["wt"]}')
                    else:
                        print(f'Loss - {result["loss_pc"]}% max profit - {result["max_profit"]}, wt - {result["wt"]}')
                    self.result["positions"].append(result)
            if candles["b_signals"].iloc[i] != 0:
                result = self.simple_watch(
                    data=candles.iloc[i:i+250],
                    order_price=candles["close"].iloc[i],
                    order_index=i,
                    type="long"
                )
                if result is not None:
                    if result["success"]:
                        print(f'Profit - {result["profit_pc"]}% max profit - {result["max_profit"]}, wt - {result["wt"]}')
                    else:
                        print(f'Loss - {result["loss_pc"]}% max profit - {result["max_profit"]}, wt - {result["wt"]}')
                    self.result["positions"].append(result)

        return self.result
