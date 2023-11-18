from ast import pattern
from fmath.patterns import BasePattern, ksreversal, stochastic_momentum, kernel_regression, rvi
import pandas as pd
import numpy as np

pd.options.mode.chained_assignment = None

class BaseInstrument:
    """
    Apply function always returns pandas dataframe
    """

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

    def apply(self,) -> pd.DataFrame:
        match self.name:
            case "SwingV2":
                raise NotImplementedError # Not in Demo
            case "Swing":
                raise NotImplementedError # Not in Demo
            case "NWKSR":
                raise NotImplementedError # Not in Demo
            case "KernelKS":
                return KernelRegressionKS.get_data(self)
            case "KSReversal":
                return KSReversal.get_data(self)
            case "KSRSMI_BASE":
                return KSRSMI_BASIC.get_data(self)
            case "KSRSMI":
                return KSRSMI.get_data(self) 

class KernelRegressionKS(BaseInstrument):
    def get_data(self):
        kernel_candles = kernel_regression.get_data(self.candles[1])

        return ksreversal.get_data(self.candles[0], smi_mode=True, smi_data=kernel_candles)

class KSRSMI_BASIC(BaseInstrument):
    def get_data(self):
        candles = stochastic_momentum.get_data(self.candles, instrument_name=self.name)

        return ksreversal.get_data(candles=candles, smi_mode=True)
            
class KSRSMI(BaseInstrument):
    def get_data(self):
        smi_data = stochastic_momentum.get_data(self.candles[1])

        return ksreversal.get_data(self.candles[0], smi_mode=True, smi_data=smi_data)
            
class KSReversal(BaseInstrument):
    def get_data(self):
        
        data = ksreversal.get_data(
            self.candles
        )

        return data
        