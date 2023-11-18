from flask import Flask, jsonify, request
import json
from pathlib import Path
from fmath.candles import Candles
from datetime import datetime
from flask_cors import CORS
from fmath.instruments import BaseInstrument
from fmath.strategy import BaseStrategy

app = Flask(__name__)
path = Path(__file__).parent / "files/live_positions.json"
CORS(app)

def get_ticker_live_positions(ticker: str, candles: list[dict], data: list[dict]):
    for candle in candles: 
        candle["signal"] = None
        candle["position_close_time"] = None

    for position in data:
        if position["ticker"] == ticker:
            for candle in candles[:-1]:
                if position["open_timestamp"] >= candle["close_time"] and position["open_timestamp"] <= candles[candles.index(candle) + 1]["close_time"]:
                    if position["type"] == "SHORT":
                        candle["signal"] = "sell" 
                        candle["order_id"] = position["order_id"]
                        candle["position_order_price"] = position["price"]
                        if position.get("close_timestamp") is not None:
                            candle["position_close_time"] = position["close_timestamp"]
                            candle["position_close_price"] = position["close_price"]
                            candle["success"] = position["success"]
                            candle["profit"] = position["profit"]
                            candle["loss"] = position["loss"]
                            candle["out_of_time"] = True if position["wt"] >= 250 else False
                            candle["order_id"] = position["order_id"]
                    else:
                        candle["signal"] = "buy"
                        candle["order_id"] = position["order_id"]
                        candle["position_order_price"] = position["price"]
                        if position.get("close_timestamp") is not None:
                            candle["position_close_time"] = position["close_timestamp"]
                            candle["position_close_price"] = position["close_price"]
                            candle["success"] = position["success"]
                            candle["profit"] = position["profit"]
                            candle["loss"] = position["loss"]
                            candle["out_of_time"] = True if position["wt"] >= 250 else False
                            candle["order_id"] = position["order_id"]
                            

    return candles

def update_candles(candles: list[dict], mode: str):
    for index, candle in enumerate(candles):
        if mode == "backtest":
            candles[index]["signal"] = None
        candles[index]["time"] = int(datetime.strptime(candle["open_time"], "%d/%m/%Y %H:%M:%S").timestamp())
        if mode == "backtest":
            if candle["b_signals"] != 0:
                candles[index]["signal"] = "buy"
            if candle["s_signals"] != 0:
                candles[index]["signal"] = "sell"
    
    return candles

def translate_date(start_time: str, end_time: str):
    formats = [
        "%d %b %Y %H:%M",
        "%d %b %Y"
    ]

    for format in formats:
        try:
            start = int(datetime.strptime(start_time, format).timestamp() * 1000)
            end = int(datetime.strptime(end_time, format).timestamp() * 1000)
            
            return {
                "start": start,
                "end": end
            }
        except Exception as e: 
            pass
    
    return None

@app.route("/get_live_analytics", methods=["GET"])
def get_live_analytics():
    with open(path, "r") as file:
        data = json.load(file)

    time_data = translate_date(start_time=request.args.get("start"), end_time=request.args.get("end"))
    if time_data is None:
        return jsonify({"error": "Bad format"})
    else:
        start, end = time_data.values()

    total_positions = 0
    pp = []
    lp = []
    for position in data:
        if position["ticker"] == request.args.get("ticker") and position.get("close_timestamp") is not None:
            if position["open_timestamp"] > start and position["close_timestamp"] < end:
                total_positions = total_positions + 1
                if position.get("success") is not None:
                    if position["success"]:
                        pp.append(position["profit"])
                    else:
                        lp.append(position["loss"])
    
    avg_p = sum(pp) / len(pp)
    avg_l = sum(lp) / len(lp)

    return jsonify(
        {
            "avg_p": avg_p,
            "avg_l": avg_l,
            "total_positions": total_positions
        }
    )


@app.route("/get_live_positions", methods=["GET"])
def get_live_positions():
    candles = Candles(
        ticker=request.args.get("ticker"),
        time_interval=request.args.get("tf"),
        futures=True
    ).get_historical_data(start=request.args.get("start"), end=request.args.get("end"))

    with open(path, "r") as file:
        data = json.load(file)

    ticker_data = get_ticker_live_positions(ticker=request.args.get("ticker"), candles=candles, data=data)

    ticker_data = update_candles(ticker_data, mode="live")
    
    return jsonify(ticker_data)

def add_strategy(candles: list[dict], positions: list[dict]):
    timestamp_mapping = {position["start_timestamp"]: position for position in positions}
    
    candles[0]["position_close_time"] = None
    candles[0]["success"] = None
    candles[0]["profit"] = None
    candles[0]["loss"] = None
    candles[0]["out_of_time"] = None

    for index in range(len(candles)-1):
        position = timestamp_mapping.get(candles[index]["close_time"])
        if position is not None:
            candles[index+1]["position_close_time"] = position["timestamp"]
            candles[index+1]["position_close_price"] = position["close_price"]
            candles[index+1]["position_order_price"] = position["order_price"]
            candles[index+1]["success"] = position["success"]
            candles[index+1]["profit"] = position.get("profit_pc")
            candles[index+1]["loss"] = position.get("loss_pc")
            candles[index+1]["out_of_time"] = position["out_of_time"]
    
    return candles

    
@app.route("/get_backtest_positions", methods=["GET"])
def get__backtest_candles():
    candles = Candles(
        ticker=request.args.get("ticker"),
        time_interval=request.args.get("tf"),
        futures=True
    ).get_historical_data(start=request.args.get("start"), end=request.args.get("end"))

    smi_candles = Candles(ticker=request.args.get("ticker"), time_interval="1d", futures=True).get_historical_data("1 Sep 2023", request.args.get("end"))

    instrument = BaseInstrument(
        name="KSRSMI", 
        candles=[candles, smi_candles],
        ticker=request.args.get("ticker"),
    )

    candles = instrument.apply().to_dict(orient="records")

    candles = update_candles(candles=candles, mode="backtest")

    if request.args.get("strat"):
        strategy = BaseStrategy(
            name="KSReversal",
            ticker=request.args.get("ticker"),
            data=instrument.apply(),
            tp=1.04,
            sl=0.965
        )
        strategy_result = strategy.apply()
        candles = add_strategy(candles=candles, positions=strategy_result["positions"])

    return jsonify(candles)

if __name__ == "__main__":
    app.run(debug=True)