from cgitb import reset
import pandas as pd
import talib as ta
import numpy as np

class BasePattern:
    def __init__(self, candles: list[dict]):
        self.candles = pd.DataFrame(candles)
        self.pattern_args = [
            self.candles["open"],
            self.candles["high"],
            self.candles["low"],
            self.candles["close"]
        ]
        self.result = {}

    @property
    def patterns(self):
        return {
        "2crows": ta.CDL2CROWS,
        "3blackcrows": ta.CDL3BLACKCROWS,
        "3inside": ta.CDL3INSIDE,
        "3linestrike": ta.CDL3LINESTRIKE,
        "3outside": ta.CDL3OUTSIDE,
        "3starsinsouth": ta.CDL3STARSINSOUTH,
        "3whitesoldiers": ta.CDL3WHITESOLDIERS,
        "abandonedbaby": ta.CDLABANDONEDBABY,
        "advanceblock": ta.CDLADVANCEBLOCK,
        "belthold": ta.CDLBELTHOLD,
        "breakaway": ta.CDLBREAKAWAY,
        "closingmarubozu": ta.CDLCLOSINGMARUBOZU,
        "concealbabyswall": ta.CDLCONCEALBABYSWALL,
        "counterattack": ta.CDLCOUNTERATTACK,
        "darkcloudcover": ta.CDLDARKCLOUDCOVER,
        "doji": ta.CDLDOJI,
        "dojistar": ta.CDLDOJISTAR,
        "dragonflydoji": ta.CDLDRAGONFLYDOJI,
        "engulfing": ta.CDLENGULFING,
        "eveningdojistar": ta.CDLEVENINGDOJISTAR,
        "eveningstar": ta.CDLEVENINGSTAR,
        "gapsidesidewhite": ta.CDLGAPSIDESIDEWHITE,
        "gravestonedoji": ta.CDLGRAVESTONEDOJI,
        "hammer": ta.CDLHAMMER,
        "hangingman": ta.CDLHANGINGMAN,
        "harami": ta.CDLHARAMI,
        "haramicross": ta.CDLHARAMICROSS,
        "highwave": ta.CDLHIGHWAVE,
        "hikkake": ta.CDLHIKKAKE,
        "hikkakemod": ta.CDLHIKKAKEMOD,
        "homingpigeon": ta.CDLHOMINGPIGEON,
        "identical3crows": ta.CDLIDENTICAL3CROWS,
        "inneck": ta.CDLINNECK,
        "invertedhammer": ta.CDLINVERTEDHAMMER,
        "kicking": ta.CDLKICKING,
        "kickingbylength": ta.CDLKICKINGBYLENGTH,
        "ladderbottom": ta.CDLLADDERBOTTOM,
        "longleggeddoji": ta.CDLLONGLEGGEDDOJI,
        "longline": ta.CDLLONGLINE,
        "marubozu": ta.CDLMARUBOZU,
        "matchinglow": ta.CDLMATCHINGLOW,
        "mathold": ta.CDLMATHOLD,
        "morningdojistar": ta.CDLMORNINGDOJISTAR,
        "morningstar": ta.CDLMORNINGSTAR,
        "onneck": ta.CDLONNECK,
        "piercing": ta.CDLPIERCING,
        "rickshawman": ta.CDLRICKSHAWMAN,
        "risefall3methods": ta.CDLRISEFALL3METHODS,
        "separatinglines": ta.CDLSEPARATINGLINES,
        "shootingstar": ta.CDLSHOOTINGSTAR,
        "shortline": ta.CDLSHORTLINE,
        "spinningtop": ta.CDLSPINNINGTOP,
        "stalledpattern": ta.CDLSTALLEDPATTERN,
        "sticksandwich": ta.CDLSTICKSANDWICH,
        "takuri": ta.CDLTAKURI,
        "tasukigap": ta.CDLTASUKIGAP,
        "thrusting": ta.CDLTHRUSTING,
        "tristar": ta.CDLTRISTAR,
        "unique3river": ta.CDLUNIQUE3RIVER,
        "upsidegap2crows": ta.CDLUPSIDEGAP2CROWS,
        "xsidegap3methods": ta.CDLXSIDEGAP3METHODS
    }


    def upgrade(self, only_b: bool = False, only_s: bool = False):
        for pattern, candles in self.result.items():
            b_signals, s_signals = [], []
            for i in range(len(candles)):
                pmatch = candles[pattern].iloc[i]
                if pmatch == 100:
                    b_signals.append(candles["close"].iloc[i])
                    s_signals.append(float("nan"))
                elif pmatch == -100:
                    s_signals.append(candles["close"].iloc[i])
                    b_signals.append(float("nan"))
                else:
                    b_signals.append(float("nan"))
                    s_signals.append(float("nan"))
            
            if only_b:
                candles["b_signals"] = b_signals
            if only_s: 
                candles["s_signals"] = s_signals
            if not only_s and not only_b:
                candles["b_signals"] = b_signals
                candles["s_signals"] = s_signals


    def apply(self, pattern: str):
        candles = self.candles
        candles[pattern] = self.patterns[pattern](*self.pattern_args)
        self.result[pattern] = candles

        self.upgrade()

        return self.result
        

    def apply_all(self, target_patterns: list[str] = None) -> dict[str, pd.DataFrame]:
        candles = self.candles
        for pattern, pfunc in self.patterns.items():
            if target_patterns is not None:
                if pattern in target_patterns:
                    candles[pattern] = pfunc(*self.pattern_args)
                    if np.count_nonzero(candles[pattern]) > 0:
                        self.result[pattern] = candles.copy(deep=True)
                    candles.drop(columns=[pattern])
            else:
                candles[pattern] = pfunc(*self.pattern_args)
                if np.count_nonzero(candles[pattern]) > 0:
                    self.result[pattern] = candles.copy(deep=True)
                candles.drop(columns=[pattern])

        self.upgrade()

        return self.result


            