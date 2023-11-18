from fmath.trader import Trader
from fmath.candles import Candles
from datetime import datetime, timedelta
from time import sleep
import time
import random
from fmath.instruments import BaseInstrument

import threading
import queue

trader = Trader(leverage=15, order_price=5)
lock = threading.Lock()

tickers = [
    "AUDIOUSDT",
    "CHZUSDT",
    "RENUSDT",
    "REEFUSDT",
    "HBARUSDT",
    "RVNUSDT",
    "CELRUSDT",
    "FTMUSDT",
    "1000SHIBUSDT",
    "OMGUSDT",
]

def generate_id(ticker: str, order_type: str, high_priority: bool = False):
    current = int(time.time())
    if high_priority:
        order_id = f'{str(current)[6:-1]}_{random.randint(5000, 10000)}_{ticker.replace("USDT", "")}_HP_{order_type[0]}'
    else:
        order_id = f'{str(current)[6:-1]}_{random.randint(5000, 10000)}_{ticker.replace("USDT", "")}_NHP_{order_type[0]}'

    return order_id

def apply_instrument(candles: list[list], ticker: str):
    data = BaseInstrument(name="KSReversal", candles=candles, ticker=ticker).apply()
    index = -2
    trader.log_info(info=f'Checking signal for {ticker} at candle {data["open_time"].iloc[index]}', level="info")
    if data is not None:
        if data["b_signals"].iloc[index] != 0:
            price = data["close"].iloc[-1]
            print(data.iloc[index])
            return {"price": price, "type": "BUY"}
        elif data["s_signals"].iloc[index] != 0:
            price = data["close"].iloc[-1]
            print(data.iloc[index])
            return {"price": price, "type": "SELL"}
        else:
            return None
    else:
        return None

def monitor_signals(ticker: str, candles: list[list]) -> dict:
    signal = apply_instrument(candles=candles, ticker=ticker)
    if signal is not None:
        order_moment_price = signal.get("price")
        order_type = signal.get("type")
        order_id = generate_id(ticker, order_type=order_type)

        #opening position
        try:
            new_order = trader.open_fpos(ticker=ticker, order_type=order_type, order_moment_price=order_moment_price, order_id=order_id)
            if new_order is None:
                return None
        except Exception as e:
            trader.log_info(info=e, level="error")
            trader.send_message(text=e)
            return None

        new_order.update({"order_moment_price": order_moment_price, "wt": 0, "order_id": order_id})

        trader.log_info(info=f'Position was OPENED for {ticker} at {order_type} ({order_id}) (price - {order_moment_price}) ({new_order.get("p")} spent)', level="warning")
        trader.send_message(text=f'Position was OPENED for {ticker} at {order_type} ({order_id}) (price - {order_moment_price}) ({new_order.get("p")} spent)')

        return new_order
    else:
        return None

def monitor_orders(positions: list[dict]):
    for position in positions:
        try:
            order_moment_price = position.get("order_moment_price")
            ticker = position.get("symbol")
            order_type = position.get("side")
            wt = position["wt"]
            qty = float(position.get("origQty"))
            order_id = position.get("order_id")

            order_result = trader.check_order(ticker=ticker, order_moment_price=order_moment_price, order_type=order_type, wt=wt, order_id=order_id)
            if order_result is not None:
                closed_order = trader.close_fpos(
                    order_type=order_type,
                    ticker=ticker,
                    qty=qty,
                    order_id=order_id,
                    wt=wt,
                    success=order_result["success"],
                    profit=order_result.get("profit"),
                    loss=order_result.get("loss"),
                    order_moment_price=order_moment_price,
                    close_price=order_result.get("close_price")
                )
                if closed_order is None:
                    continue
                if closed_order == "liq":
                    positions.remove(position)
                    
                    continue

                positions.remove(position)

                if order_result.get("success"):
                    trader.log_info(info=f'PROFIT on {ticker} ({order_id}) for {order_result.get("profit")}', level="info")
                    trader.send_message(text=f'PROFIT on {ticker} ({order_id}) for {order_result.get("profit")}')
                else:
                    trader.log_info(info=f'LOSS on {ticker} ({order_id}) for {order_result.get("loss")}', level="info")
                    trader.send_message(text=f'LOSS on {ticker} ({order_id}) for {order_result.get("loss")}')
            else:
                ct = datetime.now()
                diff = (ct - datetime.fromtimestamp(position["open_time"] / 1000)).total_seconds()
                ma = int(diff / 60)

                position["wt"] = ma // 15
        except Exception as e:
            trader.log_info(info=f'Unexpected error {e} at position {position.get("order_id")}', level="error")
            trader.send_message("Error in monitor")

    return positions

positions = queue.Queue()

def check_signals():
    while True:
        if datetime.now().minute % 15== 0 and datetime.now().second > 5:
            for ticker in tickers:
                try:
                    start_c = datetime.now() - timedelta(days=7)
                    end_c = datetime.now() + timedelta(days=2)

                    candles = Candles(ticker, time_interval="15min", futures=True).get_historical_data(start=str(start_c.timestamp() * 1000), end=str(end_c.timestamp() * 1000))
                
                    new_order = monitor_signals(
                        ticker=ticker,
                        candles=candles
                    )

                    #trader.log_info(f'Signals were checked for {ticker} - {candles[-1]["open_time"]}', level="info")
                    if new_order is not None:
                        positions.put(new_order)
                except Exception as e:
                    trader.log_info(info=f'Signal error - {e}', level="error")
                    trader.send_message(e)

            trader.log_info("Signal for all tickers were checked", "info")
            trader.send_message("Signals for all tickers were checked")

            sleep(60)
        else:
            sleep(2)
    
def check_positions():
    while True:
        if datetime.now().minute % 15 == 0:
            if not positions.empty():
                positions_list = [positions.get() for _ in range(positions.qsize())]
                try:
                    new_positions = monitor_orders(positions_list)
                    trader.log_info("Positions were checked", level="info")
                    for position in new_positions:
                        positions.put(position)
                except Exception as e:
                    for position in positions_list:
                        positions.put(position)
                    trader.log_info(e, "error")
                    trader.send_message(e)
            else:
                trader.log_info(str(positions), "warning")
                print(positions)
            sleep(60)
        else:
            sleep(5)

if __name__ == "__main__":
    signal_thread = threading.Thread(target=check_signals)
    position_thread = threading.Thread(target=check_positions)

    signal_thread.start()
    position_thread.start()

    signal_thread.join()
    position_thread.join()