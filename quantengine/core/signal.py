from quantcore.indicators import ma, macd, kdj, rsi, boll, atr


class TradingSignal:
    def __init__(self, stock_code, signal, score, trade_plan, dimensions):
        self.stock_code = stock_code
        self.signal = signal
        self.score = score
        self.trade_plan = trade_plan
        self.dimensions = dimensions
    
    def to_dict(self):
        return {
            'stock_code': self.stock_code,
            'signal': self.signal,
            'score': self.score,
            'trade_plan': self.trade_plan.to_dict() if self.trade_plan else None,
            'dimensions': self.dimensions,
        }


class TradePlan:
    def __init__(self, entry_price, stop_loss, take_profit, position_pct, risk_reward_ratio):
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.position_pct = position_pct
        self.risk_reward_ratio = risk_reward_ratio
    
    def to_dict(self):
        return {
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_pct': self.position_pct,
            'risk_reward_ratio': self.risk_reward_ratio,
        }


class SignalEngine:
    _weights = {
        'trend': 0.25,
        'momentum': 0.20,
        'volume': 0.15,
        'rsi': 0.15,
        'risk': 0.10,
        'pattern': 0.15,
    }
    
    @classmethod
    def analyze(cls, stock_code, klines, options=None):
        options = options or {}
        
        if len(klines) < 20:
            return TradingSignal(stock_code, 'avoid', 0, None, {})
        
        dimensions = cls._calculate_dimensions(klines)
        score = cls._calculate_score(dimensions)
        signal = cls._determine_signal(score)
        trade_plan = cls._generate_trade_plan(klines, dimensions, score)
        
        return TradingSignal(stock_code, signal, score, trade_plan, dimensions)
    
    @classmethod
    def scan(cls, stocks_data, filters=None, options=None):
        results = []
        for stock_code, klines in stocks_data.items():
            try:
                signal = cls.analyze(stock_code, klines, options)
                if filters:
                    if not cls._matches_filters(signal, filters):
                        continue
                results.append(signal)
            except Exception as e:
                pass
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    @classmethod
    def _calculate_dimensions(cls, klines):
        closes = [k.get('close', 0) for k in klines]
        highs = [k.get('high', 0) for k in klines]
        lows = [k.get('low', 0) for k in klines]
        volumes = [k.get('volume', 0) for k in klines]
        
        dimensions = {}
        
        ma_5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else 0
        ma_10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else 0
        ma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else 0
        ma_60 = sum(closes[-60:]) / 60 if len(closes) >= 60 else 0
        
        if ma_5 > ma_10 > ma_20 > ma_60:
            trend_score = 100
        elif ma_5 > ma_10 > ma_20:
            trend_score = 75
        elif ma_5 < ma_10 < ma_20:
            trend_score = 25
        elif ma_5 < ma_10 < ma_20 < ma_60:
            trend_score = 0
        else:
            trend_score = 50
        
        dimensions['trend'] = trend_score
        
        momentum_5 = closes[-1] / closes[-5] - 1 if len(closes) >= 5 else 0
        momentum_10 = closes[-1] / closes[-10] - 1 if len(closes) >= 10 else 0
        
        momentum_score = 50 + (momentum_5 + momentum_10) * 200
        momentum_score = max(0, min(100, momentum_score))
        dimensions['momentum'] = momentum_score
        
        if len(volumes) >= 20:
            vol_avg = sum(volumes[-20:]) / 20
            vol_recent = sum(volumes[-5:]) / 5
            volume_score = min(100, (vol_recent / vol_avg) * 50)
        else:
            volume_score = 50
        
        dimensions['volume'] = volume_score
        
        rsi_vals = rsi(closes, 14)
        if rsi_vals:
            rsi_val = rsi_vals[-1]
            if rsi_val >= 70:
                rsi_score = 25
            elif rsi_val <= 30:
                rsi_score = 75
            else:
                rsi_score = 50 + (50 - rsi_val) * 0.5
        else:
            rsi_score = 50
        
        dimensions['rsi'] = rsi_score
        
        atr_vals = atr(highs, lows, closes, 14)
        boll_result = boll(highs, lows, closes, 20)
        
        if atr_vals and boll_result['mid']:
            atr_val = atr_vals[-1] if atr_vals else 0
            boll_width = (boll_result['upper'][-1] - boll_result['lower'][-1]) / boll_result['mid'][-1] if boll_result['mid'] else 0
            
            volatility_score = 100 - min(100, atr_val * 10 + boll_width * 100)
        else:
            volatility_score = 50
        
        dimensions['risk'] = volatility_score
        
        if len(closes) >= 2:
            body = abs(closes[-1] - klines[-1].get('open', closes[-1]))
            range_ = klines[-1].get('high', closes[-1]) - klines[-1].get('low', closes[-1])
            
            if range_ > 0:
                body_ratio = body / range_
                if body_ratio > 0.8:
                    pattern_score = 75 if closes[-1] > klines[-1].get('open', closes[-1]) else 25
                elif body_ratio < 0.2:
                    pattern_score = 50
                else:
                    pattern_score = 50
            else:
                pattern_score = 50
        else:
            pattern_score = 50
        
        dimensions['pattern'] = pattern_score
        
        return dimensions
    
    @classmethod
    def _calculate_score(cls, dimensions):
        score = 0
        for dim, weight in cls._weights.items():
            score += dimensions.get(dim, 50) * weight
        return round(score, 2)
    
    @classmethod
    def _determine_signal(cls, score):
        if score >= 90:
            return 'strong_buy'
        elif score >= 70:
            return 'buy'
        elif score >= 40:
            return 'neutral'
        elif score >= 20:
            return 'sell'
        else:
            return 'strong_sell'
    
    @classmethod
    def _generate_trade_plan(cls, klines, dimensions, score):
        if score < 40:
            return None
        
        close = klines[-1].get('close', 0)
        highs = [k.get('high', 0) for k in klines]
        lows = [k.get('low', 0) for k in klines]
        
        atr_vals = atr(highs, lows, [k.get('close', 0) for k in klines], 14)
        atr_val = atr_vals[-1] if atr_vals else close * 0.02
        
        entry_price = close
        stop_loss = round(close - atr_val * 1.5, 2)
        take_profit = round(close + atr_val * 2, 2)
        position_pct = min(0.2, score / 500)
        risk_reward_ratio = round((take_profit - entry_price) / (entry_price - stop_loss), 2) if (entry_price - stop_loss) > 0 else 0
        
        return TradePlan(entry_price, stop_loss, take_profit, position_pct, risk_reward_ratio)
    
    @classmethod
    def _matches_filters(cls, signal, filters):
        if 'min_score' in filters and signal.score < filters['min_score']:
            return False
        if 'max_score' in filters and signal.score > filters['max_score']:
            return False
        if 'signal' in filters and signal.signal not in filters['signal']:
            return False
        return True