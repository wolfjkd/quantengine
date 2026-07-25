from quantcore.indicators import ma, rsi
from quantcore.utils import zscore


class FactorEngine:
    _factors = {
        'mom_20': {
            'name': '20日动量',
            'direction': 'positive',
            'default_weight': 1.0,
            'description': '20日收益率',
        },
        'vol_20': {
            'name': '20日波动率',
            'direction': 'negative',
            'default_weight': 0.5,
            'description': '20日收益率标准差',
        },
        'ma_bias': {
            'name': '均线乖离',
            'direction': 'positive',
            'default_weight': 0.5,
            'description': '价格与20日均线的偏离度',
        },
        'turnover': {
            'name': '成交额活跃度',
            'direction': 'positive',
            'default_weight': 0.3,
            'description': '近5日成交额与近20日均值的比值',
        },
        'rsi_14': {
            'name': 'RSI(14)',
            'direction': 'positive',
            'default_weight': 0.2,
            'description': '相对强弱指数',
        },
        'momentum_5': {
            'name': '5日动量',
            'direction': 'positive',
            'default_weight': 0.8,
            'description': '5日收益率',
        },
        'boll_width': {
            'name': '布林带宽度',
            'direction': 'negative',
            'default_weight': 0.3,
            'description': '布林带宽度与中轨的比值',
        },
        'volume_ratio': {
            'name': '量比',
            'direction': 'positive',
            'default_weight': 0.4,
            'description': '今日成交量与5日均量的比值',
        },
    }
    
    @classmethod
    def catalog(cls):
        return cls._factors
    
    @classmethod
    def score(cls, stocks_data, factor_weights=None, filters=None, options=None):
        factor_weights = factor_weights or {}
        results = []
        
        for stock_code, klines in stocks_data.items():
            if len(klines) < 20:
                continue
            
            scores = {}
            for factor_code, config in cls._factors.items():
                weight = factor_weights.get(factor_code, config['default_weight'])
                if weight <= 0:
                    continue
                
                factor_value = cls._calculate_factor(factor_code, klines)
                direction = config['direction']
                
                if direction == 'negative':
                    factor_value = -factor_value
                
                scores[factor_code] = factor_value * weight
            
            total_score = sum(scores.values())
            results.append({
                'stock_code': stock_code,
                'score': total_score,
                'factor_scores': scores,
                'close': klines[-1].get('close', 0),
            })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        
        if filters:
            results = cls._apply_filters(results, filters)
        
        return results
    
    @classmethod
    def ic_analysis(cls, factor_code, stocks_data, period=60):
        if factor_code not in cls._factors:
            raise ValueError(f"Unknown factor: {factor_code}")
        
        factor_values = []
        future_returns = []
        
        for stock_code, klines in stocks_data.items():
            if len(klines) < period + 5:
                continue
            
            factor_value = cls._calculate_factor(factor_code, klines[:-5])
            
            current_close = klines[-period - 5].get('close', 0)
            future_close = klines[-5].get('close', 0)
            
            if current_close > 0:
                future_return = future_close / current_close - 1
                factor_values.append(factor_value)
                future_returns.append(future_return)
        
        if len(factor_values) < 2:
            return {'ic': 0, 'rank_ic': 0, 'samples': 0}
        
        ic = cls._calculate_correlation(factor_values, future_returns)
        
        factor_ranks = cls._rank(factor_values)
        return_ranks = cls._rank(future_returns)
        rank_ic = cls._calculate_correlation(factor_ranks, return_ranks)
        
        return {
            'ic': ic,
            'rank_ic': rank_ic,
            'samples': len(factor_values),
            'factor_code': factor_code,
            'factor_name': cls._factors[factor_code]['name'],
        }
    
    @classmethod
    def _calculate_factor(cls, factor_code, klines):
        closes = [k.get('close', 0) for k in klines]
        volumes = [k.get('volume', 0) for k in klines]
        
        if factor_code == 'mom_20':
            return closes[-1] / closes[-20] - 1 if len(closes) >= 20 else 0
        
        elif factor_code == 'mom_5':
            return closes[-1] / closes[-5] - 1 if len(closes) >= 5 else 0
        
        elif factor_code == 'vol_20':
            if len(closes) < 21:
                return 0
            returns = [closes[i] / closes[i-1] - 1 for i in range(1, len(closes))]
            mean = sum(returns) / len(returns)
            variance = sum((r - mean) ** 2 for r in returns) / len(returns)
            return (variance ** 0.5) * (252 ** 0.5)
        
        elif factor_code == 'ma_bias':
            if len(closes) < 20:
                return 0
            ma_20 = sum(closes[-20:]) / 20
            return (closes[-1] - ma_20) / ma_20
        
        elif factor_code == 'turnover':
            if len(volumes) < 20:
                return 0
            vol_avg = sum(volumes[-20:]) / 20
            vol_recent = sum(volumes[-5:]) / 5
            return vol_recent / vol_avg if vol_avg > 0 else 0
        
        elif factor_code == 'rsi_14':
            rsi_vals = rsi(closes, 14)
            return rsi_vals[-1] if rsi_vals else 50
        
        elif factor_code == 'boll_width':
            if len(closes) < 20:
                return 0
            ma_val = sum(closes[-20:]) / 20
            prices = closes[-20:]
            variance = sum((p - ma_val) ** 2 for p in prices) / 20
            std = variance ** 0.5
            return (2 * std) / ma_val if ma_val > 0 else 0
        
        elif factor_code == 'volume_ratio':
            if len(volumes) < 6:
                return 0
            vol_today = volumes[-1]
            vol_ma5 = sum(volumes[-6:-1]) / 5
            return vol_today / vol_ma5 if vol_ma5 > 0 else 0
        
        return 0
    
    @classmethod
    def _calculate_correlation(cls, x, y):
        n = len(x)
        if n < 2:
            return 0
        
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / n
        std_x = (sum((xi - mean_x) ** 2 for xi in x) / n) ** 0.5
        std_y = (sum((yi - mean_y) ** 2 for yi in y) / n) ** 0.5
        
        if std_x == 0 or std_y == 0:
            return 0
        
        return cov / (std_x * std_y)
    
    @classmethod
    def _rank(cls, values):
        sorted_indices = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0] * len(values)
        for rank, idx in enumerate(sorted_indices):
            ranks[idx] = rank + 1
        return ranks
    
    @classmethod
    def _apply_filters(cls, results, filters):
        filtered = []
        for result in results:
            include = True
            
            if 'min_score' in filters and result['score'] < filters['min_score']:
                include = False
            
            if 'min_volume' in filters:
                pass
            
            if include:
                filtered.append(result)
        
        return filtered