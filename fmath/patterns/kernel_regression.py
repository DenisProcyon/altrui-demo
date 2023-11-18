import pandas as pd
import numpy as np

def get_kr(src, h, x_0, r):

    yhat = []
    
    for idx in range(len(src)):
        if idx < x_0:
            yhat.append(None)
            continue

        curw = 0.0
        cumw = 0.0
        for i in range(int(max(0, idx - h)), idx):
            y = src[i]
            distance = idx - 1

            w = np.power(1 + (np.power(distance, 2) / (h * h * 2 * r)), -r)
            curw = curw + y * w
            cumw = cumw + w
        
        estval = curw / cumw if cumw != 0 else 0
        yhat.append(estval)

    return yhat

def get_data(candles: list[dict]):
    candles = pd.DataFrame(candles)

    src = candles["open"]
    h = 50
    r = 3
    x_0 = 50

    yhat1 = get_kr(src, h, x_0, r)

    yhat2 = get_kr(src, h-2, x_0, r)

    candles["yhat1"] = yhat1
    candles["yhat2"] = yhat2

    candles["p"] = 0
    for i in range(x_0, len(candles)):
        if candles["yhat2"].iloc[i] < candles["open"].iloc[i]:
            candles["p"].iloc[i] = 1
        else:
            candles["p"].iloc[i] = -1

    return candles





