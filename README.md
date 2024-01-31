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
        additional_config=["rvi"]
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
    
