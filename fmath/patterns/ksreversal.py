import pandas as pd
import talib as ta
import numpy as np
    

def smi_combine(candles: pd.DataFrame, smi_data: pd.DataFrame):
    candles["p"] = None
    period = 0

    for i in range(len(candles)):
        if candles["open_time"].iloc[i] in smi_data["open_time"].values:
            try:
                period = smi_data[smi_data["open_time"] == candles["open_time"].iloc[i]]["p"].item()
                candles["p"].iloc[i] = period
            except Exception as e:
                print("Error")
                candles["p"].iloc[i] = period
        else:
            candles["p"].iloc[i] = period
    
    return candles

def get_data(candles: list[dict], smi_mode: bool = False, smi_data: pd.DataFrame = None, sb_periods: list[dict] = None, fp: int = 34, sp: int = 15, sigp: int = 16, tp: int = 2):
    candles = pd.DataFrame(candles)

    macd_line, signal_line, _ = ta.MACD(candles["close"], fastperiod=fp, slowperiod=sp, signalperiod=sigp)
    upper_boll, mid_line, lower_boll = ta.BBANDS(candles["close"], timeperiod=tp, nbdevup=4, nbdevdn=4)

    if not smi_mode:
        buy_signal = np.where((np.minimum(candles['open'].shift(1), candles['close'].shift(1)) <= lower_boll.shift(1)) & 
                            (np.maximum(candles['open'].shift(1), candles['close'].shift(1)) <= mid_line) &
                            (macd_line.shift(1) > signal_line.shift(1)) & 
                            (macd_line.shift(2) < signal_line.shift(2)), 1, 0) 

        sell_signal = np.where((np.maximum(candles['open'].shift(1), candles['close'].shift(1)) >= upper_boll.shift(1)) & 
                            (np.minimum(candles['open'].shift(1), candles['close'].shift(1)) >= mid_line) &
                            (macd_line.shift(1) < signal_line.shift(1)) & 
                            (macd_line.shift(2) > signal_line.shift(2)), 1, 0)
    else:
        if smi_data is not None:
            candles = smi_combine(candles=candles, smi_data=smi_data)

        buy_signal = np.where((candles["p"] == 1) &
                            (np.minimum(candles['open'].shift(1), candles['low'].shift(1)) <= lower_boll.shift(1)) & 
                            (np.maximum(candles['open'].shift(1), candles['low'].shift(1)) <= mid_line) & 
                            (macd_line.shift(1) > signal_line.shift(1)) & 
                            (macd_line.shift(2) < signal_line.shift(2)), 1, 0) 

        sell_signal = np.where((candles["p"] == -1) &
                            (np.maximum(candles['open'].shift(1), candles['close'].shift(1)) >= upper_boll.shift(1)) & 
                            (np.minimum(candles['open'].shift(1), candles['close'].shift(1)) >= mid_line) & 
                            (macd_line.shift(1) < signal_line.shift(1)) & 
                            (macd_line.shift(2) > signal_line.shift(2)), 1, 0)
    
    candles['b_signals'] = buy_signal
    candles['s_signals'] = sell_signal

    return candles