from pyexpat import model
import pandas as pd
from pathlib import Path
import json
from fmath.candles import Candles
import talib as ta
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn import metrics

from sklearn import tree
import matplotlib.pyplot as plt 
import pickle
import warnings 
warnings.simplefilter(action="ignore")

import os
import re

positions_file = Path(__file__).parent / "files/backtest_sessions.json"

timeperiods = [5,10,15,20,25,30,35,40,45,50]

def apply_intruments(candles: pd.DataFrame) -> pd.DataFrame:
    
    for timeperiod in timeperiods:
        candles[f'BETA_SCORE{timeperiod}'] = ta.BETA(candles["high"], candles["low"], timeperiod=timeperiod) / ta.BETA(candles["high"], candles["low"], timeperiod=timeperiod*2)
        candles[f'MIDPOINT_SCORE{timeperiod}'] = ta.MIDPOINT(candles["close"], timeperiod=timeperiod) / ta.MIDPOINT(candles["close"], timeperiod=timeperiod*2)
        candles[f'RSI{timeperiod}'] = ta.RSI(candles["close"], timeperiod=timeperiod)
        candles[f'TRIX{timeperiod}'] = ta.TRIX(candles["close"], timeperiod=timeperiod)
        candles[f'WILLR{timeperiod}'] = ta.WILLR(candles["high"], candles["low"], candles["close"], timeperiod=timeperiod)
        candles[f'ATR{timeperiod}'] = ta.ATR(candles["high"], candles["low"], candles["close"], timeperiod=timeperiod)

    return candles

def modify_ticker_positions(ticker_candles: dict[str, pd.DataFrame], positions: pd.DataFrame):
    result = []
    for i in range(len(positions)):
        condition = ticker_candles[positions["ticker"].iloc[i]]["close_time"].shift(1) == positions["start_timestamp"].iloc[i]
        try:
            target_candle = ticker_candles[positions["ticker"].iloc[i]][condition].iloc[0]
            result.append(pd.concat([positions.iloc[i], target_candle]).to_dict())
        except Exception as e:
            print(e)
    
    return pd.DataFrame(result)
            
def get_m_data(data: pd.DataFrame):
    start, end = data["start_timestamp"].min() * 0.999, data["timestamp"].max() * 1.001
    ticker_candles = {}
    tickers = data["ticker"].unique().tolist()
    for index, ticker in enumerate(tickers):
        candles = Candles(ticker=ticker, time_interval="15min", futures=True).get_historical_data(start=str(start), end=str(end))
        candles = apply_intruments(candles=pd.DataFrame(candles))
        ticker_candles[ticker] = candles
        print(f'{ticker}, {index + 1} / {len(tickers)}')
    
    result_positions = modify_ticker_positions(ticker_candles=ticker_candles, positions=data)

    return result_positions

def update_positions(data: list[dict]):
    for position in data:
        if position["success"]:
            position["loss_pc"] = 0
        else:
            position["profit_pc"] = 0
    
    return data

def combine_positions(data: dict):
    all_positions = []
    for ticker_data in data:
        for position in ticker_data["positions"]:
            position["ticker"] = ticker_data["ticker"]
        all_positions = all_positions + ticker_data["positions"]

    return all_positions

def get_positions_data(session_id: int) -> pd.DataFrame:
    with open(positions_file) as file:
        sessions = json.load(file)
    
    for session in sessions:
        if session["id"] == session_id:
            target_session = session
    
    session = combine_positions(target_session["result"])
    session = update_positions(session)

    return pd.DataFrame(session)

def get_all_session_ids():
    with open(positions_file) as file:
        sessions = json.load(file)

    result = []
    for session in sessions:
        result.append((session["id"], session["info"]))
    
    return result

def get_best_path(nodes: list):
    samples = [node["samples"][0].tolist() for node in nodes]
    
    target_samples = sorted(samples, key=lambda x: (x[0], -x[1]))

    print(target_samples[0:5])

    for node in nodes:
        if target_samples[0] == node["samples"][0].tolist():
            target_node_id = node["index"]

    path = []
    for node in reversed(nodes):
        if target_node_id in [node["left"], node["right"]]:
            opr = "<=" if target_node_id == node["left"] else ">"
            ind_period = re.findall(r'\d+', node["feature"])[0]
            path.append(
                (
                    node["feature"].replace(ind_period, ""),
                    int(ind_period),
                    opr,
                    node["feature_value"]
                )
            )
            target_node_id = node["index"]
    
    return path

def construct_tree_representation(tree_repr: tree, features: list):
    nodes = []
    for node_index in range(tree_repr.node_count):
        node_left_c = tree_repr.children_left[node_index]
        node_right_c = tree_repr.children_right[node_index]

        leaf = True if node_left_c == -1 and node_right_c == -1 else False

        node_feature = features[tree_repr.feature[node_index]] if leaf is False else None
        node_feature_value = tree_repr.threshold[node_index] if leaf is False else None
        node_samples = tree_repr.value[node_index]

        nodes.append(
            {
                "index": node_index,
                "left": node_left_c,
                "right": node_right_c,
                "samples": node_samples,
                "leaf": leaf,
                "feature": node_feature,
                "feature_value": node_feature_value
            }
        )
    
    best_path = get_best_path(nodes=nodes)

    return best_path

def main():
    sessions = get_all_session_ids()

    for session in sessions:
        session_id = session[0]
        session_name = session[1]

        print(f'Session for {session_name}. Session id - {session_id}')

        pos_data = get_positions_data(session_id=session_id)
        m_data = get_m_data(pos_data).dropna()

        features = [i for i in m_data.columns.to_list() if i not in [
            "max_profit",
            "success",
            "ticker",
            "wt", 
            "close", 
            "close_time", 
            "type",
            "open",
            "close_price",
            "open_price",
            "profit_pc", "loss_pc", 
            "high",
            "low", 
            "order_price",
            "close", 
            "start_timestamp",
            "timestamp",
            "open_time",
            "out_of_time",
            "number_of_trades",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
            "volume",
            "quote_asset_volume"
        ]]

        m_data["type"] = m_data["type"].replace({"long": 1, "short": 0})

        X = m_data[features]
        Y = m_data["success"].astype(int)

        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.3, random_state=1)

        result = {}
        for i in [3, 5, 7, 10, 15, 20]:
            model = DecisionTreeClassifier(max_depth=i)
            model = model.fit(X_train, Y_train)

            y_pred = model.predict(X_test)

            print(metrics.accuracy_score(Y_test, y_pred))

            fig = plt.figure(figsize=(20,5))
            tree_representation = tree.plot_tree(model, feature_names=features, filled=True, precision=5)
            
            if not os.path.exists(f'decision_trees/{session_name}'):
                os.makedirs(f'decision_trees/{session_name}')
            pickle.dump(fig, open(f'decision_trees/{session_name}/layers{i}.fig.pickle', "wb"))
            
            print(f'Layer {i}')    

            best_path = construct_tree_representation(tree_repr=model.tree_, features=features)

            result[session_name] = best_path
           
        print(json.dumps(result, indent=2).replace('",\n     ', '",') + ",")

if __name__ == "__main__":
    main()