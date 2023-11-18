from asyncore import close_all
from fileinput import close
from operator import le
from binance.client import Client
from fmath.candles import Candles
import pandas as pd
from binance.enums import *
from fmath.conf.cred import CREDS
import telebot
from time import sleep
from datetime import datetime
import logging
from binance.exceptions import BinanceAPIException as api_ex
from pathlib import Path
import json
import time
import inspect


logging.basicConfig(format="%(asctime)s %(levelname)s - %(message)s", level=logging.INFO, handlers=[logging.FileHandler("trader.log"), logging.StreamHandler()])
#bot = telebot.TeleBot()
#TEL_USER = 0

def ensure_balance(func):
    def get_balance(self, *args, **kwargs):
        while True:
            try:
                account = self.active_client.futures_account()
                break
            except Exception as e:
                print("Time need to be synced")
                sleep(3)

        balance = float(account.get("availableBalance"))
        if balance > 10:
            return func(self, *args, **kwargs)
        else:
            self.log_info(info=f'Balance is {balance}. Can not open a position', level="error")
            self.send_message(f'Balance is {balance}. Can not open a position')

    return get_balance

def get_quantity(ticker: str, balance: float, leverage: int, symbols_info: list[dict]):
    candles = Candles(ticker=ticker, time_interval="1min", futures=True, time_limit=1)
    candles = candles.get_data()

    cur_price = candles[-1]["close"]

    trigger = False
    i = 0
    while not trigger:
        i = i + 1
        for s in symbols_info["symbols"]:
            if s["symbol"] == ticker:
                quant_prec = s["quantityPrecision"]
                trigger = True
        if i > 10:
            trigger = True
            quant_prec = 3

    order_price = balance * 0.0285
    quantity = order_price / cur_price * leverage

    quantity = round(quantity, quant_prec)

    return {"q": quantity, "p": order_price}

class Trader:
    def __init__(self, leverage: int, order_price: float) -> None:
        self.leverage = leverage
        self.order_price = order_price
        self.path = Path(__file__).parent.parent / "files/live_positions.json"
        self.balance_history = []

        self.active_client = Client(CREDS.get("BINANCE_API_KEY"), CREDS.get("BINANCE_SECRET_KEY"))

        self.log_info(info="Trader was launched", level="warning")

    def update_live_json(self, oc: str, **kwargs):
        with open(self.path, "r") as file:
            data = json.load(file)

        if oc == "open":
            new_position = {
                "ticker": kwargs["ticker"],
                "order_id": kwargs["order_id"],
                "type": kwargs["position_side"],
                "price": kwargs["price"],
                "open_timestamp": round(time.time() * 1000)
            }
            data.append(new_position)
        else:
            for position in data:
                if position["order_id"] == kwargs["order_id"]:
                    position["close_timestamp"] = round(time.time() * 1000)
                    position["wt"] = kwargs["wt"]
                    position["close_price"] = kwargs["close_price"]
                    position["order_price"] = kwargs["order_moment_price"]
                    position["success"] = kwargs["success"]
                    position["profit"] = kwargs["profit"]
                    position["loss"] = kwargs["loss"]

        with open(self.path, "w") as file:
            json.dump(data, file)

    def send_message(self, text: str):
        try:
            if "head" in str(text):
                text = f'Message was sent from {inspect.stack()}'
            bot.send_message(TEL_USER, text)
        except Exception as e:
            print(e)
            print(text)

    def log_info(self, info: str, level: str = "warning"):
        if level == "warning":
            logging.warning(info)
        elif level == "error":
            logging.error(info)
        elif level == "info":
            logging.info(info)

    def get_balance(self):
        future_data = self.active_client.futures_account()
        for i in future_data.get("assets"):
            if i.get("asset") == "USDT":
                balance = i.get("walletBalance")
                return float(balance)

    def change_leverage(self, leverage: int, ticker: str) -> None:
        """
        Changes default leverage
        """
        while True:
            try:
                self.active_client.futures_change_leverage(leverage=leverage, symbol=ticker)
                return
            except Exception as e:
                self.log_info(f'Could not change leverage to {leverage} for {ticker}, trying {leverage-1}')
                leverage = leverage - 1

    def change_order_price(self, order_price: int) -> None:
        """
        Changes default order price (USDT)
        """
        self.order_price = order_price

    def get_all_orders(self, order_ticker: str) -> list[dict]:
        """
        Gets all open positions for ticker
        """
        orders = self.active_client.futures_get_all_orders(symbol=order_ticker)
        return orders

    def check_if_was_closed(self, order_id: str):
        with open(self.path, "r") as file:
            data = json.load(file)

        for i in data:
            if i["order_id"] == order_id:
                return True

        return False

    def check_order(self, ticker: str, order_moment_price: float, order_type: str, wt: int, order_id: str):
        """
        Checks if order has reached stop-loss or take-profit levels
        """
        candles = Candles(ticker=ticker, time_interval="1min", futures=True, time_limit=1).get_data()
        current_price = candles[-1]["close"]

        tp = 1.04
        sl = 0.965

        if order_type == "SELL":
            price_change = round(order_moment_price / current_price, 4)
            if wt >= 249:
                if price_change > 1:
                    profit = round(float((price_change - 1) * 100), 3)
                    result = {"success": True, "profit": profit, "close_price": current_price}
                    return result
                else:
                    loss = round(float((1 - price_change) * 100), 3)
                    result = {"success": False, "loss": loss, "close_price": current_price}
                    return result
            if price_change >= tp:
                profit = round(float((price_change - 1) * 100), 3)
                result = {"success": True, "profit": profit, "close_price": current_price}
                return result
            if price_change <= sl:
                loss = round(float((1 - price_change) * 100), 3)
                result = {"success": False, "loss": loss, "close_price": current_price}
                return result
            else:
                self.log_info(f'Position for {ticker} ({order_id}) (wt - {wt}) was not closed (Order price - {order_moment_price}, current price - {current_price}, price_change - {price_change})', "info")
                #self.send_message(f'Position for {ticker} was not changed (Order price - {order_moment_price}, current price - {current_price}, price_change - {price_change})')
                return None
        else:
            price_change = round(current_price / order_moment_price, 4)
            if wt >= 249:
                if price_change > 1:
                    profit = round(float((price_change - 1) * 100), 3)
                    result = {"success": True, "profit": profit, "close_price": current_price}
                    return result
                else:
                    loss = round(float((1 - price_change) * 100), 3)
                    result = {"success": False, "loss": loss, "close_price": current_price}
                    return result
            if price_change > tp:
                profit = round(float((price_change - 1) * 100), 3)
                result = {"success": True, "profit": profit, "close_price": current_price}
                return result
            if price_change < sl:
                loss = round(float((1 - price_change) * 100), 3)
                result = {"success": False, "loss": loss, "close_price": current_price}
                return result
            else:
                self.log_info(f'Position for {ticker} ({order_id}) (wt - {wt}) was not closed (Order price - {order_moment_price}, current price - {current_price}, price_change - {price_change})', "info")
                #self.send_message(f'Position for {ticker} was not changed (Order price - {order_moment_price}, current price - {current_price}, price_change - {price_change})')
                return None

    @ensure_balance
    def open_fpos(self, ticker: str, order_type: str, order_moment_price: float, order_id: str) -> dict:
        """
        Opens position
        """

        symbols_info = self.active_client.futures_exchange_info()

        if order_type == "SELL":
            position_side = "SHORT"
        else:
            position_side = "LONG"

        quantity = get_quantity(ticker=ticker, balance=self.get_balance(), leverage=self.leverage, symbols_info=symbols_info)
        order_price = quantity["p"]
        quantity = quantity["q"]

        attempts = 0
        while attempts < 5:
            try:
                order = self.active_client.futures_create_order(
                    symbol=ticker,
                    side=order_type,
                    type="MARKET",
                    positionSide=position_side,
                    #dualSidePosition=True,
                    quantity=quantity,
                )

                order["p"] = order_price
                order["open_time"] = int(datetime.now().timestamp() * 1000)
                order["wt"] = 0

                self.update_live_json(oc="open", price=order_moment_price, position_side=position_side, ticker=ticker, order_id=order_id)

                return order
            except Exception as e:
                self.log_info(info=e, level="error")
                self.send_message(text=f'[ERROR!] CAN NOT OPEN POSITION FOR {ticker}. CHECK LOG')
                attempts = attempts + 1
                sleep(3)
        return

    def close_fpos(self, order_type: str, ticker: str, order_id: str, qty: float = None, **kwargs) -> dict:
        """
        Closes position
        """
        if order_type == "SELL":
            order_type = "BUY"
            position_side = "SHORT"
        else:
            order_type = "SELL"
            position_side = "LONG"

        orders = self.get_all_orders(order_ticker=ticker)
        quant = orders[-1]["executedQty"]

        trs = 0
        while True:
            if trs < 5:
                try:
                    closed = self.active_client.futures_create_order(
                        symbol=ticker,
                        side=order_type,
                        type="MARKET",
                        quantity=qty,
                        #reduceOnly=True
                        positionSide=position_side,
                    )
                    break
                except Exception as e:
                    self.log_info(info=e, level="error")
                    self.send_message(text=f'[ERROR!] CAN NOT CLOSE POSITION FOR {ticker} {order_id}. CHECK LOG')
                    trs = trs + 1
                    error = e
                    sleep(1)
            else:
                if "APIError(code=-2022)" in str(error):
                    self.log_info(info=f'Position for {ticker} ({order_id}) was liquidated', level="warning")
                    self.send_message(f'Position for {ticker} ({order_id}) was luquidated')
                    
                    return "liq"

        future_data = self.active_client.futures_account()
        for i in future_data.get("assets"):
            if i.get("asset") == "USDT":
                balance = i.get("walletBalance")
                break

        self.log_info(info=f'[BALANCE UPDATE] - {balance}', level="info")
        self.send_message(text=f'Balance now is {balance}')
        self.balance_history.append(
            {
                "timestamp": int(datetime.now().timestamp() * 1000),
                "balance": balance
            }
        )

        self.update_live_json(oc="close", ticker=ticker, order_id=order_id, **kwargs)

        return closed