# Demo of my algo trading project

##### The following repo contains the base and approximately 50% of the functionality of my main algo trading project that has been in development for 1 year+ 

### Files/Modules Description

- `backtest.py`
  - **Purpose**: Main and only backtesting module
  - **Usage**:
    ```python
    # Initializing candles (fmath/candles.py)
    candles = Candles(
        ticker="BTCUSDT",
        time_interval="15min",
        futures=True
    ).get_historical_data("1 Oct 2023", "1 Nov 2023")
    
    # Initializing instrument (fmath/instruments.py)
    instrument = BaseInstrument(
        name="KSReversal",
        candles=candles,
        ticker="BTCUSDT",
        additional_config={}
    )
    
    # Initializing and launching strategy (fmath/strategy/__init__.py)
    strategy = BaseStrategy(
        name="KSReversal",
        ticker=ticker,
        data=data,
        tp=1.02,
        sl=0.98,
        complex_watch=False
    )
    
    result = strategy.apply()
    
    #updating backtest_sessions.json
    session["result"].append(result)
    ```

- `fmath/instruments.py`
  - **Purpose**: Indicators/Technical Approaches
  - **Usage**:
    ```python
      class BaseInstrument:
        def __init__(
            self, name: str, 
            candles: list | list[list], 
            ticker: str,
            additional_config: list = [],
            custom_settings: dict = None) -> None:

            self.name = name
            self.candles = candles
            self.ticker = ticker
    
            self.additional_config = additional_config
    
            self.custom_settings = custom_settings
    
        def apply(self) -> pd.DataFrame:
            match self.name:
                case "SwingV2":
                    raise NotImplementedError # Not in Demo
                ...
    ```

- `fmath/strategy/__init__.py`
  - **Purpose**: TP/SL/Position holding managing
  - **Usage**:
    ```python
    def apply(self):
        match self.name:
            case "KSReversal": 
                return KSReversalStrategy.calculate(self)
            ...
    ```

- `fmath/wallet.py; files/backtest_sessions.json`
  - **Purpose**: Profitability calculations
  - **Usage**:
    ```json
    [
    {
      "id":178193,
      "result":[
         {}
        ]
    }
    ]
    ```
  - **Taking ID 178193**
     ```python
     wallet = Wallet(
         balance=1000,
         leverage=10, 
         order_size=0.01, # % of balance
         session_id=178193
     )
     
     wallet.calculate()
     ```
    
### Active trading module
 - **fmath/trader.py; real_trader.py**
    ```python
    class Trader:
        def __init__(self, leverage: int, order_price: float) -> None:
            self.leverage = leverage
            self.order_price = order_price
            ...
    ```

# Decision Tree Strategy Implementation

### Context
For initial signals allocation in dataset (to make model be based on something) I used my previous strategy which was configured specificly for bearish market and died in Autumn 2023 since all this trend with ETFs became to rise. It was changed significally and adapted for new market conditions but was still not proven to be strictly and continiously profitable on a backtest. 

### Files/Modules Description
- `dec_tree_analysis.py`
  - **Purpose**: Model fitting and indicators correlation identification 
  - **Usage**:
    ```python
    # Adding features to the dataset 
    timeperiods = [5,10,20,40]
    for timeperiod in timeperiods:
        candles[f'BETA_SCORE{timeperiod}'] = ta.BETA(candles["high"], candles["low"], timeperiod=timeperiod) / ta.BETA(candles["high"], candles["low"], timeperiod=timeperiod*2)
        candles[f'MIDPOINT_SCORE{timeperiod}'] = ta.MIDPOINT(candles["close"], timeperiod=timeperiod) / ta.MIDPOINT(candles["close"], timeperiod=timeperiod*2)
        candles[f'RSI{timeperiod}'] = ta.RSI(candles["close"], timeperiod=timeperiod)
        candles[f'TRIX{timeperiod}'] = ta.TRIX(candles["close"], timeperiod=timeperiod)
        candles[f'WILLR{timeperiod}'] = ta.WILLR(candles["high"], candles["low"], candles["close"], timeperiod=timeperiod)
        candles[f'ATR{timeperiod}'] = ta.ATR(candles["high"], candles["low"], candles["close"], timeperiod=timeperiod)
        ...

    # Model training and saving tree to .pickle file 
    for i in [3, 5, 10, 15]:
        model = DecisionTreeClassifier(max_depth=i, class_weight={0: 1, 1: 1})
        model = model.fit(X_train, Y_train)
    
        y_pred = model.predict(X_test)
 
        print(metrics.accuracy_score(Y_test, y_pred))

        fig = plt.figure(figsize=(20,5))
 
        if not os.path.exists(f'decision_trees/{ticker}'):
            os.makedirs(f'decision_trees/{ticker}')
        pickle.dump(fig, open(f'decision_trees/{ticker}/layers{i}.fig.pickle', "wb"))
 
        ...
    ```

### Example of a tree (3 layers)
![image](https://github.com/DenisProcyon/altrui-demo/assets/92217845/6cd93a55-7875-4550-96d8-aa82448270dd)

To follow decision rules for deeper trees ```construct_tree_representation()``` and ```get_best_path()``` functions were implemented since it is obviously hard to follow those conditions manually in the code. 

### Example of output
```
Layer 3
[[0.0, 16.0], [4.0, 5.0], [5.0, 0.0], [8.0, 0.0], [11.0, 18.0]]
{
  "Demo Session": [
    [
      "ATR", 40,
      ">", 0.00010714653399190865
    ],
    [
      "BETA_SCORE", 45,
      ">", 1.1939647793769836
    ]
  ]
}
```

### Implementation of conditions
- `backtest.py`
```python
decision_path = [
        ["ATR", 40,">", 0.00010714653399190865],
        ["BETA_SCORE", 45,">", 1.1939647793769836]
]

instrument = BaseInstrument(
    name="DecisionTree",
    candles=candles,
    ticker=ticker,
    additional_config={
        "decision_path": decision_path,
        "mode": "buy", # for one way mode only
    }
)
```
    
