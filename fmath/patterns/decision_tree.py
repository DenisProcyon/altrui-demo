import pandas as pd
import talib as ta
import numpy as np

INDS = {
    "MIDPOINT": {
        "func": ta.MIDPOINT,
        "attrs": (
            "close",
        )
    },
    "BETA": {
        "func": ta.BETA,
        "attrs": (
            "high",
            "low",
        )
    },
    "PLUS_DI": {
        "func": ta.PLUS_DI,
        "attrs": (
            "high",
            "low",
            "close",
        )
    },
    "EMA": {
        "func": ta.EMA,
        "attrs": (
            "close",
        )
    },
    "PLUS_DI": {
        "func": ta.PLUS_DI,
        "attrs": (
            "high",
            "low",
            "close",
        )
    },
    "MOM": {
        "func": ta.MOM,
        "attrs": (
            "close",
        )
    },
    "ROC": {
        "func": ta.ROC,
        "attrs": (
            "close",
        )
    },
    "SMA": {
        "func": ta.SMA,
        "attrs": (
            "close",
        )
    },
    "LINEARREG": {
        "func": ta.LINEARREG,
        "attrs": (
            "close",
        )
    },
    "ROCR": {
        "func": ta.ROCR,
        "attrs": (
            "close",
        )
    },
    "TRIX": {
        "func": ta.TRIX,
        "attrs": (
            "close",
        )
    },
    "MFI": {
        "func": ta.MFI,
        "attrs": (
            "high",
            "low", 
            "close",
            "volume",
        )
    },
    "WILLR": {
        "func": ta.WILLR,
        "attrs": (
            "high",
            "low", 
            "close",
        )
    },
    "RSI": {
        "func": ta.RSI,
        "attrs": (
            "close",
        )
    },
    "ATR": {
        "func": ta.ATR,
        "attrs": (
            "high",
            "low",
            "close",
        )
    },
    "CORREL": {
        "func": ta.CORREL,
        "attrs": (
            "high",
            "low",
        )
    },
}

modes = {
    "buy": 1,
    "sell": -1,
}

def get_data(candles: list[dict], tree: tuple, mode: str):
    candles = pd.DataFrame(candles)

    for node in tree:
        if "SCORE" in node.ind:
            required_attrs = tuple([candles[i] for i in INDS[node.ind.replace("_SCORE", "")]["attrs"]])
            candles[node.ind+str(node.indp)] = INDS[node.ind.replace("_SCORE", "")]["func"](*required_attrs, timeperiod=node.indp) / INDS[node.ind.replace("_SCORE", "")]["func"](*required_attrs, timeperiod=node.indp * 2)
        else:
            required_attrs = tuple([candles[i] for i in INDS[node.ind]["attrs"]])
            candles[node.ind+str(node.indp)] = INDS[node.ind]["func"](*required_attrs, timeperiod=node.indp)


    condition_columns = []
    for index, node in enumerate(tree):
        candles[f'p{index+1}'] = np.where(
            (
                node.opr(candles[node.ind+str(node.indp)], node.indv)
            ), modes[mode], 0
        )
        condition_columns.append(f'p{index+1}')

    candles["p"] = candles[condition_columns].all(axis=1).astype(int)

    return candles
    
    