from quantcore.indicators import ma, ema, sma, wma, macd, kdj, rsi, boll, atr, vol_ma


class Indicators:
    @classmethod
    def ma(cls, closes, period, method='sma'):
        return ma(closes, period, method)
    
    @classmethod
    def ema(cls, closes, period):
        return ema(closes, period)
    
    @classmethod
    def sma(cls, closes, period):
        return sma(closes, period)
    
    @classmethod
    def wma(cls, closes, period):
        return wma(closes, period)
    
    @classmethod
    def macd(cls, closes, fast_period=12, slow_period=26, signal_period=9):
        return macd(closes, fast_period, slow_period, signal_period)
    
    @classmethod
    def kdj(cls, highs, lows, closes, n=9, m1=3, m2=3):
        return kdj(highs, lows, closes, n, m1, m2)
    
    @classmethod
    def rsi(cls, closes, period=14):
        return rsi(closes, period)
    
    @classmethod
    def boll(cls, highs, lows, closes, period=20, num_std=2):
        return boll(highs, lows, closes, period, num_std)
    
    @classmethod
    def atr(cls, highs, lows, closes, period=14):
        return atr(highs, lows, closes, period)
    
    @classmethod
    def vol_ma(cls, volumes, period=5):
        return vol_ma(volumes, period)