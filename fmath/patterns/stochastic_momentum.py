import pandas as pd
import talib as ta

def get_ema_ema(source: pd.Series, length: int):
    return ta.EMA(
        ta.EMA(source, timeperiod=length),
        timeperiod=length
    )

def get_data(candles: list[dict], instrument_name: str = "KSRSMI"):
    """
    Returns pandas df with "p" = 1/-1 
    """

    candles = pd.DataFrame(candles)

    k = 10
    d = 25
    emalen = 60

    candles["highest"] = candles["high"].rolling(window=k).max()
    candles["lowest"] = candles["low"].rolling(window=k).min()

    candles["hlrange"] = candles["highest"] - candles["lowest"]

    candles["rel_range"] = candles["open"] - (candles["highest"] + candles["lowest"]) / 2

    candles["smi"] = 200 * get_ema_ema(candles["rel_range"], d) / get_ema_ema(candles["hlrange"], d)

    candles["ema"] = ta.EMA(candles["smi"], timeperiod=emalen)

    if instrument_name == "KSRSMI":
        candles["p"] = candles["smi"] > candles["ema"]

        candles["p"] = candles["p"].replace({True: 1, False: -1})

        return candles
    else:
        candles["p"] = 0
        
        for i in range(len(candles)):
            if candles["smi"].iloc[i] > 41:
                candles["p"].iloc[i]  = -1
            if candles["smi"].iloc[i] < -41:
                candles["p"].iloc[i] = 1
        
        return candles

    

