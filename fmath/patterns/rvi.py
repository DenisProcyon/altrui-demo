import pandas as pd
import talib as ta
import numpy as np
import matplotlib.pyplot as plt

def get_data(candles: list[dict]) -> pd.DataFrame:
    """
    Returns pandas df with "p" = 1/-1 
    """

    candles = pd.DataFrame(candles)

    stddev_length = 2
    length = 5
    
    stddev = candles["open"].rolling(window=stddev_length).std()
    change = candles["open"].diff()

    upper = ta.EMA(np.where(change <= 0, 0, stddev), timeperiod=length)
    lower = ta.EMA(np.where(change > 0, 0, stddev), timeperiod=length)

    with np.errstate(divide="ignore", invalid="ignore"):
        rvi = (upper / (upper + lower)) * 100
        candles["rvi"] = np.nan_to_num(rvi)

    candles["p"] = 0
    for i in range(len(candles)):
        if candles["rvi"].iloc[i] <= 30:
            candles["p"].iloc[i] = 1
        if candles["rvi"].iloc[i] >= 70:
            candles["p"].iloc[i] = -1
    
    return candles