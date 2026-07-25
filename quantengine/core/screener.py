from quantcore.indicators import ma, rsi, boll, atr


class Screener:
    _conditions = {
        'ma_bullish': {
            'name': '均线多头排列',
            'description': 'MA5 > MA10 > MA20 > MA60',
            'params': {},
        },
        'ma_bearish': {
            'name': '均线空头排列',
            'description': 'MA5 < MA10 < MA20 < MA60',
            'params': {},
        },
        'rsi_range': {
            'name': 'RSI区间',
            'description': 'RSI在指定区间内',
            'params': {'min': 30, 'max': 70},
        },
        'momentum_range': {
            'name': '动量区间',
            'description': '近期涨幅在指定区间内',
            'params': {'min': -0.1, 'max': 0.1},
        },
        'price_range': {
            'name': '价格区间',
            'description': '收盘价在指定区间内',
            'params': {'min': 0, 'max': 100},
        },
        'amount_filter': {
            'name': '成交额过滤',
            'description': '成交额大于指定值',
            'params': {'min_amount': 100000000},
        },
        'new_high': {
            'name': '创新高',
            'description': '收盘价创近期新高',
            'params': {'period': 60},
        },
        'new_low': {
            'name': '创新低',
            'description': '收盘价创近期新低',
            'params': {'period': 60},
        },
        'boll_breakout': {
            'name': '布林带突破',
            'description': '收盘价突破布林带上轨或下轨',
            'params': {'direction': 'up'},
        },
        'volume_surge': {
            'name': '放量',
            'description': '成交量放大',
            'params': {'ratio': 2.0},
        },
        'macd_gold': {
            'name': 'MACD金叉',
            'description': 'DIF上穿DEA',
            'params': {},
        },
        'macd_dead': {
            'name': 'MACD死叉',
            'description': 'DIF下穿DEA',
            'params': {},
        },
        'kdj_gold': {
            'name': 'KDJ金叉',
            'description': 'K线上穿D线',
            'params': {},
        },
        'kdj_dead': {
            'name': 'KDJ死叉',
            'description': 'K线下穿D线',
            'params': {},
        },
    }
    
    @classmethod
    def get_conditions(cls):
        return cls._conditions
    
    @classmethod
    def screen(cls, stocks_data, conditions, filters=None, options=None):
        results = []
        
        for stock_code, klines in stocks_data.items():
            if len(klines) < 20:
                continue
            
            match = cls._match_conditions(klines, conditions)
            
            if match:
                result = {
                    'stock_code': stock_code,
                    'close': klines[-1].get('close', 0),
                    'volume': klines[-1].get('volume', 0),
                    'matched_conditions': match,
                }
                
                if filters and not cls._matches_filters(result, filters):
                    continue
                
                results.append(result)
        
        return results
    
    @classmethod
    def _match_conditions(cls, klines, conditions):
        matched = []
        
        for cond_code, params in conditions.items():
            if cond_code not in cls._conditions:
                continue
            
            if cls._check_condition(cond_code, klines, params):
                matched.append(cond_code)
        
        return matched
    
    @classmethod
    def _check_condition(cls, cond_code, klines, params):
        closes = [k.get('close', 0) for k in klines]
        highs = [k.get('high', 0) for k in klines]
        lows = [k.get('low', 0) for k in klines]
        volumes = [k.get('volume', 0) for k in klines]
        
        if cond_code == 'ma_bullish':
            if len(closes) < 60:
                return False
            ma5 = sum(closes[-5:]) / 5
            ma10 = sum(closes[-10:]) / 10
            ma20 = sum(closes[-20:]) / 20
            ma60 = sum(closes[-60:]) / 60
            return ma5 > ma10 > ma20 > ma60
        
        elif cond_code == 'ma_bearish':
            if len(closes) < 60:
                return False
            ma5 = sum(closes[-5:]) / 5
            ma10 = sum(closes[-10:]) / 10
            ma20 = sum(closes[-20:]) / 20
            ma60 = sum(closes[-60:]) / 60
            return ma5 < ma10 < ma20 < ma60
        
        elif cond_code == 'rsi_range':
            rsi_vals = rsi(closes, 14)
            if not rsi_vals:
                return False
            rsi_val = rsi_vals[-1]
            min_rsi = params.get('min', 30)
            max_rsi = params.get('max', 70)
            return min_rsi <= rsi_val <= max_rsi
        
        elif cond_code == 'momentum_range':
            if len(closes) < 10:
                return False
            momentum = closes[-1] / closes[-10] - 1
            min_mom = params.get('min', -0.1)
            max_mom = params.get('max', 0.1)
            return min_mom <= momentum <= max_mom
        
        elif cond_code == 'price_range':
            close = closes[-1]
            min_price = params.get('min', 0)
            max_price = params.get('max', 100)
            return min_price <= close <= max_price
        
        elif cond_code == 'amount_filter':
            amount = klines[-1].get('amount', 0)
            min_amount = params.get('min_amount', 100000000)
            return amount >= min_amount
        
        elif cond_code == 'new_high':
            period = params.get('period', 60)
            if len(closes) < period:
                return False
            return closes[-1] == max(closes[-period:])
        
        elif cond_code == 'new_low':
            period = params.get('period', 60)
            if len(closes) < period:
                return False
            return closes[-1] == min(closes[-period:])
        
        elif cond_code == 'boll_breakout':
            boll_result = boll(highs, lows, closes, 20)
            if not boll_result['upper'] or not boll_result['lower']:
                return False
            
            direction = params.get('direction', 'up')
            if direction == 'up':
                return closes[-1] >= boll_result['upper'][-1]
            else:
                return closes[-1] <= boll_result['lower'][-1]
        
        elif cond_code == 'volume_surge':
            if len(volumes) < 6:
                return False
            ratio = params.get('ratio', 2.0)
            today_vol = volumes[-1]
            avg_vol = sum(volumes[-6:-1]) / 5
            return today_vol >= avg_vol * ratio
        
        elif cond_code == 'macd_gold':
            from quantcore.indicators import macd
            result = macd(closes)
            if len(result['dif']) < 2 or len(result['dea']) < 2:
                return False
            return result['dif'][-1] > result['dea'][-1] and result['dif'][-2] <= result['dea'][-2]
        
        elif cond_code == 'macd_dead':
            from quantcore.indicators import macd
            result = macd(closes)
            if len(result['dif']) < 2 or len(result['dea']) < 2:
                return False
            return result['dif'][-1] < result['dea'][-1] and result['dif'][-2] >= result['dea'][-2]
        
        elif cond_code == 'kdj_gold':
            from quantcore.indicators import kdj
            result = kdj(highs, lows, closes)
            if len(result['k']) < 2 or len(result['d']) < 2:
                return False
            return result['k'][-1] > result['d'][-1] and result['k'][-2] <= result['d'][-2]
        
        elif cond_code == 'kdj_dead':
            from quantcore.indicators import kdj
            result = kdj(highs, lows, closes)
            if len(result['k']) < 2 or len(result['d']) < 2:
                return False
            return result['k'][-1] < result['d'][-1] and result['k'][-2] >= result['d'][-2]
        
        return False
    
    @classmethod
    def _matches_filters(cls, result, filters):
        if 'min_volume' in filters and result['volume'] < filters['min_volume']:
            return False
        if 'min_price' in filters and result['close'] < filters['min_price']:
            return False
        if 'max_price' in filters and result['close'] > filters['max_price']:
            return False
        return True