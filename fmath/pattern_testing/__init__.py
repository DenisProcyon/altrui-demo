from tkinter import E
import pandas as pd

class PatternTesting:
    def __init__(self, data: dict[str, pd.DataFrame], timeframe: str, trend_strategy: bool):
        self.data = data
        self.timeframe = timeframe
        self.trend_strategy = trend_strategy

    @property
    def tf_settings(self):
        return {
            "5min": {
                "threshold": 150,
                "limit_pc": 0.5,
            }
        }

    def get_min_max_values(self, data: pd.DataFrame):
        minpos = data["low"].values.argmin()
        minval = data.iloc[minpos]["low"]
        
        maxpos = data["high"].values.argmax()
        maxval = data.iloc[maxpos]["high"]

        return {
            "max": {
                "val": maxval, 
                "len": maxpos
            },
            "min": {
                "val": minval,
                "len": minpos
            }
        }
        

    """
    This function refers to build a data source with price movements in range of given threshold       
    """
    def check_move(self, data: pd.DataFrame, mtype: str):
        order_place = data["close"].iloc[0]
        
        mmvalues = self.get_min_max_values(data=data)

        min_pchange = ((mmvalues["min"]["val"] - order_place) / mmvalues["min"]["val"]) * 100
        max_pchange = ((mmvalues["max"]["val"] - order_place) / mmvalues["max"]["val"]) * 100

        top_min_location = mmvalues["min"]["len"]
        top_max_location = mmvalues["max"]["len"]

        return {
            "min": {
                "minpc": min_pchange,
                "topmin": top_min_location
            },
            "max": {
                "maxpc": max_pchange,
                "topmax": top_max_location
            }
        } 

    
    def get_closest_tchange(self, data: pd.DataFrame):
        for i in range(1, len(data)):
            if not pd.isna(data["b_signals"].iloc[i]):
                return i
            if not pd.isna(data["s_signals"].iloc[i]):
                return i
        return
            

    """
    This function refers to test pattern, when meeting buy or sell signals.

    Threshold is an abstract gap for price change (It can differ from pattern to pattern and from timeframe to timeframe)
    and this solution should be extended
    """
    def test_pattern(self, candles: pd.DataFrame, pattern: str):
        move_threshold = self.tf_settings[self.timeframe]["threshold"]

        av_min_pchange_s, av_min_pchange_b = [], []
        av_max_pchange_s, av_max_pchange_b = [], []

        av_len_min_change_s, av_len_min_change_b = [], []
        av_len_max_change_s, av_len_max_change_b = [], []

        len_b_signals = 0
        len_s_signals = 0

        for i in range(len(candles)):
            if not pd.isna(candles["b_signals"].iloc[i]):
                if self.trend_strategy:
                    move_threshold = self.get_closest_tchange(candles[i:])
                    if move_threshold is None:
                        continue
                try:
                    result = self.check_move(data=candles.iloc[i:i+move_threshold], mtype="buy")

                    av_max_pchange_b.append(result["max"]["maxpc"])
                    av_min_pchange_b.append(result["min"]["minpc"])

                    av_len_max_change_b.append(result["max"]["topmax"])
                    av_len_min_change_b.append(result["min"]["topmin"])

                    len_b_signals = len_b_signals + 1
                except IndexError:
                    pass
            if not pd.isna(candles["s_signals"].iloc[i]):
                if self.trend_strategy:
                    move_threshold = self.get_closest_tchange(candles[i:])
                    if move_threshold is None:
                        continue
                try: 
                    result = self.check_move(data=candles.iloc[i:i+move_threshold], mtype="sell")
                    
                    av_max_pchange_s.append(result["max"]["maxpc"])
                    av_min_pchange_s.append(result["min"]["minpc"])

                    av_len_max_change_s.append(result["max"]["topmax"])
                    av_len_min_change_s.append(result["min"]["topmin"])

                    len_s_signals = len_s_signals + 1
                except IndexError:
                    pass
        
        return {
            "sell": {
                "avmax_change": av_max_pchange_s,
                "avmin_change": av_min_pchange_s,
                "avmin_len": av_len_min_change_s,
                "avmax_len": av_len_max_change_s,
                "signal_len": len_s_signals
            },
            "buy": {
                "avmax_change": av_max_pchange_b,
                "avmin_change": av_min_pchange_b,
                "avmin_len": av_len_min_change_b,
                "avmax_len": av_len_max_change_b,
                "signal_len": len_b_signals
            }
        }


    def launch(self):
        pattern_result = {}
        for pattern, candles in self.data.items():
            result = self.test_pattern(candles=candles, pattern=pattern)

            if len(result["buy"]["avmax_change"]) > 0:
                avtop_price_b = sum(result["buy"]["avmax_change"])/len(result["buy"]["avmax_change"])
            else:
                avtop_price_b = None

            if len(result["buy"]["avmin_change"]) > 0:
                avmin_price_b = sum(result["buy"]["avmin_change"])/len(result["buy"]["avmin_change"])
            else:
                avmin_price_b = None

            if len(result["buy"]["avmax_len"]) > 0:
                avpermax_b = sum(result["buy"]["avmax_len"])/len(result["buy"]["avmax_len"])
            else:
                avpermax_b = None

            if len(result["buy"]["avmin_len"]) > 0:
                avpermin_b = sum(result["buy"]["avmin_len"])/len(result["buy"]["avmin_len"])
            else: 
                avpermin_b = None


            
            if len(result["sell"]["avmax_change"]) > 0:
                avtop_price_s = sum(result["sell"]["avmax_change"])/len(result["sell"]["avmax_change"])
            else:
                avtop_price_s = None

            if len(result["sell"]["avmin_change"]) > 0:
                avmin_price_s = sum(result["sell"]["avmin_change"])/len(result["sell"]["avmin_change"])
            else:
                avmin_price_s = None

            if len(result["sell"]["avmax_len"]) > 0:
                avpermax_s = sum(result["sell"]["avmax_len"])/len(result["sell"]["avmax_len"])
            else:
                avpermax_s = None

            if len(result["sell"]["avmin_len"]) > 0:
                avpermin_s = sum(result["sell"]["avmin_len"])/len(result["sell"]["avmin_len"])
            else: 
                avpermin_s = None

            pattern_result[pattern] = {
                "buy": {
                    "avmax_change": avtop_price_b,
                    "avmin_change": avmin_price_b,
                    "avmin_len": avpermin_b,
                    "avmax_len": avpermax_b,
                    "signal_len": result["buy"]["signal_len"]
                },
                "sell": {
                    "avmax_change": avtop_price_s,
                    "avmin_change": avmin_price_s,
                    "avmin_len": avpermin_s,
                    "avmax_len": avpermax_s,
                    "signal_len": result["sell"]["signal_len"]
                }
            }

        return pattern_result

