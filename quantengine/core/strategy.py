from quantcore.indicators import ma, macd, kdj, rsi, boll


class StrategyLab:
    _strategies = {
        'dual_ma': {
            'name': '双均线策略',
            'type': 'trend',
            'description': '基于快慢均线交叉的趋势跟踪策略',
            'params': {'fast_period': 5, 'slow_period': 20},
        },
        'macd': {
            'name': 'MACD策略',
            'type': 'trend',
            'description': '基于MACD金叉死叉的趋势策略',
            'params': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
        },
        'kdj': {
            'name': 'KDJ策略',
            'type': 'oscillator',
            'description': '基于KDJ超买超卖的震荡策略',
            'params': {'n': 9, 'm1': 3, 'm2': 3},
        },
        'boll': {
            'name': '布林带策略',
            'type': 'reversion',
            'description': '基于布林带突破的均值回归策略',
            'params': {'period': 20, 'num_std': 2},
        },
        'rsi': {
            'name': 'RSI策略',
            'type': 'oscillator',
            'description': '基于RSI超买超卖的震荡策略',
            'params': {'period': 14, 'oversold': 30, 'overbought': 70},
        },
        'momentum': {
            'name': '动量策略',
            'type': 'momentum',
            'description': '基于近期涨幅的动量策略',
            'params': {'period': 20},
        },
        'mean_reversion': {
            'name': '均值回归策略',
            'type': 'reversion',
            'description': '基于均线乖离的均值回归策略',
            'params': {'period': 20, 'threshold': 0.1},
        },
        'composite': {
            'name': '综合评分策略',
            'type': 'composite',
            'description': '基于多维度评分的综合策略',
            'params': {},
        },
    }
    
    @classmethod
    def catalog(cls):
        return cls._strategies
    
    @classmethod
    def run(cls, key, klines, params=None, filters=None):
        strategy_func = cls._get_strategy_func(key)
        if strategy_func is None:
            raise ValueError(f"Unknown strategy: {key}")
        
        params = params or cls._strategies.get(key, {}).get('params', {})
        
        signals = []
        for i, kline in enumerate(klines):
            signal = strategy_func(klines[:i+1], params)
            signals.append({
                'date': kline.get('date', ''),
                'signal': signal,
                'close': kline.get('close', 0),
            })
        
        if filters:
            signals = cls._apply_filters(signals, filters)
        
        return signals
    
    @classmethod
    def compare(cls, keys, klines, params=None):
        results = {}
        for key in keys:
            try:
                results[key] = cls.run(key, klines, params)
            except Exception as e:
                results[key] = {'error': str(e)}
        return results
    
    @classmethod
    def register(cls, key, strategy_class, config):
        cls._strategies[key] = config
    
    @classmethod
    def _get_strategy_func(cls, key):
        func_map = {
            'dual_ma': cls._strategy_dual_ma,
            'macd': cls._strategy_macd,
            'kdj': cls._strategy_kdj,
            'boll': cls._strategy_boll,
            'rsi': cls._strategy_rsi,
            'momentum': cls._strategy_momentum,
            'mean_reversion': cls._strategy_mean_reversion,
            'composite': cls._strategy_composite,
        }
        return func_map.get(key)
    
    @classmethod
    def _strategy_dual_ma(cls, klines, params):
        fast_period = params.get('fast_period', 5)
        slow_period = params.get('slow_period', 20)
        
        closes = [k.get('close', 0) for k in klines]
        if len(closes) < slow_period:
            return 'hold'
        
        fast_ma = ma(closes, fast_period)
        slow_ma = ma(closes, slow_period)
        
        if len(fast_ma) >= 2 and len(slow_ma) >= 2:
            if fast_ma[-1] > slow_ma[-1] and fast_ma[-2] <= slow_ma[-2]:
                return 'buy'
            elif fast_ma[-1] < slow_ma[-1] and fast_ma[-2] >= slow_ma[-2]:
                return 'sell'
        return 'hold'
    
    @classmethod
    def _strategy_macd(cls, klines, params):
        closes = [k.get('close', 0) for k in klines]
        result = macd(closes)
        
        if len(result['dif']) >= 2 and len(result['dea']) >= 2:
            if result['dif'][-1] > result['dea'][-1] and result['dif'][-2] <= result['dea'][-2]:
                return 'buy'
            elif result['dif'][-1] < result['dea'][-1] and result['dif'][-2] >= result['dea'][-2]:
                return 'sell'
        return 'hold'
    
    @classmethod
    def _strategy_kdj(cls, klines, params):
        highs = [k.get('high', 0) for k in klines]
        lows = [k.get('low', 0) for k in klines]
        closes = [k.get('close', 0) for k in klines]
        
        result = kdj(highs, lows, closes)
        
        if len(result['k']) >= 2 and len(result['d']) >= 2:
            if result['k'][-1] > result['d'][-1] and result['k'][-2] <= result['d'][-2]:
                return 'buy'
            elif result['k'][-1] < result['d'][-1] and result['k'][-2] >= result['d'][-2]:
                return 'sell'
        return 'hold'
    
    @classmethod
    def _strategy_boll(cls, klines, params):
        highs = [k.get('high', 0) for k in klines]
        lows = [k.get('low', 0) for k in klines]
        closes = [k.get('close', 0) for k in klines]
        
        result = boll(highs, lows, closes)
        
        if len(result['lower']) >= 1 and len(result['upper']) >= 1:
            if closes[-1] <= result['lower'][-1]:
                return 'buy'
            elif closes[-1] >= result['upper'][-1]:
                return 'sell'
        return 'hold'
    
    @classmethod
    def _strategy_rsi(cls, klines, params):
        closes = [k.get('close', 0) for k in klines]
        result = rsi(closes)
        
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)
        
        if len(result) >= 2:
            if result[-1] <= oversold and result[-2] > oversold:
                return 'buy'
            elif result[-1] >= overbought and result[-2] < overbought:
                return 'sell'
        return 'hold'
    
    @classmethod
    def _strategy_momentum(cls, klines, params):
        period = params.get('period', 20)
        
        closes = [k.get('close', 0) for k in klines]
        if len(closes) < period + 1:
            return 'hold'
        
        momentum = closes[-1] / closes[-period] - 1
        
        if momentum > 0.1:
            return 'buy'
        elif momentum < -0.1:
            return 'sell'
        return 'hold'
    
    @classmethod
    def _strategy_mean_reversion(cls, klines, params):
        period = params.get('period', 20)
        threshold = params.get('threshold', 0.1)
        
        closes = [k.get('close', 0) for k in klines]
        if len(closes) < period:
            return 'hold'
        
        ma_val = sum(closes[-period:]) / period
        bias = (closes[-1] - ma_val) / ma_val
        
        if bias < -threshold:
            return 'buy'
        elif bias > threshold:
            return 'sell'
        return 'hold'
    
    @classmethod
    def _strategy_composite(cls, klines, params):
        closes = [k.get('close', 0) for k in klines]
        
        if len(closes) < 20:
            return 'hold'
        
        score = 0
        
        ma_5 = sum(closes[-5:]) / 5
        ma_20 = sum(closes[-20:]) / 20
        if ma_5 > ma_20:
            score += 25
        
        momentum = closes[-1] / closes[-10] - 1
        if momentum > 0:
            score += 20
        
        vol_recent = sum(k.get('volume', 0) for k in klines[-5:]) / 5
        vol_avg = sum(k.get('volume', 0) for k in klines[-20:]) / 20
        if vol_recent > vol_avg * 1.2:
            score += 15
        
        score += 20
        
        atr_vals = []
        for i in range(1, len(closes)):
            tr = max(
                klines[i].get('high', 0) - klines[i].get('low', 0),
                abs(klines[i].get('high', 0) - closes[i-1]),
                abs(klines[i].get('low', 0) - closes[i-1])
            )
            atr_vals.append(tr)
        if atr_vals and atr_vals[-1] < sum(atr_vals) / len(atr_vals):
            score += 10
        
        score += 10
        
        if score >= 80:
            return 'buy'
        elif score <= 30:
            return 'sell'
        return 'hold'
    
    @classmethod
    def _apply_filters(cls, signals, filters):
        filtered = []
        for signal in signals:
            include = True
            if 'min_volume' in filters:
                pass
            if include:
                filtered.append(signal)
        return filtered