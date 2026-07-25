from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from quantcore.indicators import ma, macd, kdj, rsi, boll, atr
from quantcore.metrics import total_return, annualized_return, max_drawdown, sharpe_ratio, win_rate, profit_factor


DEFAULT_SETTINGS = {
    'commission_rate': 0.00025,
    'min_commission': 5.0,
    'stamp_tax_rate': 0.0005,
    'slippage_bps': 10,
    'risk_free_rate': 0.03,
    'trading_days_year': 252,
    'max_weight': 0.2,
    'max_positions': 10,
    'stop_loss': 0.05,
    'take_profit': 0.10,
    'fill_mode': 'close',
}


class BacktestEngine:
    def __init__(self, initial_cash=1000000.0, settings=None):
        self.initial_cash = Decimal(str(initial_cash))
        self.settings = {**DEFAULT_SETTINGS, **(settings or {})}
        self.cash = self.initial_cash
        self.positions = {}
        self.equity_curve = []
        self.trades = []
        self.logs = []
    
    def run(self, strategy, klines, params=None):
        strategy_func = self._get_strategy(strategy)
        if strategy_func is None:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        params = params or {}
        self._reset()
        
        for i, kline in enumerate(klines):
            date = kline.get('date', '')
            close = Decimal(str(kline.get('close', 0)))
            high = Decimal(str(kline.get('high', 0)))
            low = Decimal(str(kline.get('low', 0)))
            
            signal = strategy_func(klines[:i+1], params)
            
            if signal == 'buy' and self.cash > 0:
                self._execute_buy(kline, params)
            elif signal == 'sell' and self.positions:
                self._execute_sell(kline, params)
            
            equity = self.cash
            for code, pos in self.positions.items():
                equity += pos['quantity'] * close
            self.equity_curve.append(float(equity))
            
            self._check_stop_loss_take_profit(kline)
        
        return BacktestResult(self)
    
    def _get_strategy(self, strategy):
        strategies = {
            'dual_ma': self._strategy_dual_ma,
            'macd': self._strategy_macd,
            'kdj': self._strategy_kdj,
            'boll': self._strategy_boll,
            'rsi': self._strategy_rsi,
            'momentum': self._strategy_momentum,
            'mean_reversion': self._strategy_mean_reversion,
            'composite': self._strategy_composite,
        }
        return strategies.get(strategy)
    
    def _strategy_dual_ma(self, klines, params):
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
    
    def _strategy_macd(self, klines, params):
        closes = [k.get('close', 0) for k in klines]
        result = macd(closes)
        
        if len(result['dif']) >= 2 and len(result['dea']) >= 2:
            if result['dif'][-1] > result['dea'][-1] and result['dif'][-2] <= result['dea'][-2]:
                return 'buy'
            elif result['dif'][-1] < result['dea'][-1] and result['dif'][-2] >= result['dea'][-2]:
                return 'sell'
        return 'hold'
    
    def _strategy_kdj(self, klines, params):
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
    
    def _strategy_boll(self, klines, params):
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
    
    def _strategy_rsi(self, klines, params):
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
    
    def _strategy_momentum(self, klines, params):
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
    
    def _strategy_mean_reversion(self, klines, params):
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
    
    def _strategy_composite(self, klines, params):
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
        
        volumes = [k.get('volume', 0) for k in klines]
        if len(volumes) >= 20:
            vol_recent = sum(volumes[-5:]) / 5
            vol_avg = sum(volumes[-20:]) / 20
            if vol_recent > vol_avg * 1.2:
                score += 15
        
        score += 20
        
        atr_vals = []
        highs = [k.get('high', 0) for k in klines]
        lows = [k.get('low', 0) for k in klines]
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
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
    
    def _execute_buy(self, kline, params):
        code = kline.get('code', 'unknown')
        close = Decimal(str(kline.get('close', 0)))
        
        if close <= 0:
            return
        
        commission = close * Decimal(str(self.settings['commission_rate']))
        if commission < Decimal(str(self.settings['min_commission'])):
            commission = Decimal(str(self.settings['min_commission']))
        
        slippage = close * Decimal(str(self.settings['slippage_bps'])) / Decimal('10000')
        actual_price = close + slippage
        
        available_cash = self.cash - commission
        quantity = (available_cash / actual_price).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
        
        if quantity <= 0:
            return
        
        total_cost = quantity * actual_price + commission
        
        if total_cost > self.cash:
            quantity = ((self.cash - commission) / actual_price).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
            total_cost = quantity * actual_price + commission
        
        self.cash -= total_cost
        
        if code not in self.positions:
            self.positions[code] = {
                'quantity': Decimal('0'),
                'avg_cost': Decimal('0'),
                'positions': []
            }
        
        self.positions[code]['positions'].append({
            'quantity': quantity,
            'cost': actual_price,
            'date': kline.get('date', ''),
            'frozen': True
        })
        self.positions[code]['quantity'] += quantity
        total_quantity = self.positions[code]['quantity']
        total_cost_basis = sum(p['quantity'] * p['cost'] for p in self.positions[code]['positions'])
        self.positions[code]['avg_cost'] = (total_cost_basis / total_quantity).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        
        self.trades.append({
            'date': kline.get('date', ''),
            'code': code,
            'type': 'buy',
            'quantity': int(quantity),
            'price': float(actual_price),
            'commission': float(commission),
            'slippage': float(slippage),
        })
        
        self.logs.append(f"{kline.get('date', '')} BUY {code} {int(quantity)} @ {float(actual_price)}")
    
    def _execute_sell(self, kline, params):
        code = kline.get('code', 'unknown')
        
        if code not in self.positions:
            return
        
        close = Decimal(str(kline.get('close', 0)))
        slippage = close * Decimal(str(self.settings['slippage_bps'])) / Decimal('10000')
        actual_price = close - slippage
        
        quantity = self.positions[code]['quantity']
        
        commission = actual_price * quantity * Decimal(str(self.settings['commission_rate']))
        if commission < Decimal(str(self.settings['min_commission'])):
            commission = Decimal(str(self.settings['min_commission']))
        
        stamp_tax = actual_price * quantity * Decimal(str(self.settings['stamp_tax_rate']))
        
        total_revenue = quantity * actual_price - commission - stamp_tax
        profit = total_revenue - quantity * self.positions[code]['avg_cost']
        
        self.cash += total_revenue
        
        self.trades.append({
            'date': kline.get('date', ''),
            'code': code,
            'type': 'sell',
            'quantity': int(quantity),
            'price': float(actual_price),
            'commission': float(commission),
            'stamp_tax': float(stamp_tax),
            'profit': float(profit),
        })
        
        self.positions[code] = {
            'quantity': Decimal('0'),
            'avg_cost': Decimal('0'),
            'positions': []
        }
        
        self.logs.append(f"{kline.get('date', '')} SELL {code} {int(quantity)} @ {float(actual_price)}")
    
    def _check_stop_loss_take_profit(self, kline):
        code = kline.get('code', 'unknown')
        
        if code not in self.positions:
            return
        
        close = Decimal(str(kline.get('close', 0)))
        avg_cost = self.positions[code]['avg_cost']
        
        if avg_cost <= 0:
            return
        
        ret = (close - avg_cost) / avg_cost
        
        if ret <= -self.settings['stop_loss']:
            self._execute_sell(kline, {})
        elif ret >= self.settings['take_profit']:
            self._execute_sell(kline, {})
    
    def _reset(self):
        self.cash = self.initial_cash
        self.positions = {}
        self.equity_curve = []
        self.trades = []
        self.logs = []
    
    def add_strategy(self, strategy_class):
        pass
    
    def get_settings(self):
        return self.settings
    
    def set_settings(self, settings):
        self.settings.update(settings)


class BacktestResult:
    def __init__(self, engine):
        self.engine = engine
    
    @property
    def equity_curve(self):
        return self.engine.equity_curve
    
    @property
    def trades(self):
        return self.engine.trades
    
    @property
    def metrics(self):
        return self._calculate_metrics()
    
    @property
    def logs(self):
        return self.engine.logs
    
    def _calculate_metrics(self):
        ec = self.equity_curve
        trades = self.trades
        
        return {
            'total_return': total_return(ec),
            'annualized_return': annualized_return(ec),
            'max_drawdown': max_drawdown(ec),
            'sharpe_ratio': sharpe_ratio(ec),
            'win_rate': win_rate(trades),
            'profit_factor': profit_factor(trades),
            'num_trades': len(trades),
            'initial_cash': float(self.engine.initial_cash),
            'final_equity': ec[-1] if ec else float(self.engine.initial_cash),
        }
    
    def summary(self):
        m = self.metrics
        return {
            'total_return': f"{m['total_return']:.2%}",
            'annualized_return': f"{m['annualized_return']:.2%}",
            'max_drawdown': f"{m['max_drawdown']:.2%}",
            'sharpe_ratio': f"{m['sharpe_ratio']:.2f}",
            'win_rate': f"{m['win_rate']:.2%}",
            'profit_factor': f"{m['profit_factor']:.2f}",
            'num_trades': m['num_trades'],
            'initial_cash': f"¥{m['initial_cash']:,.2f}",
            'final_equity': f"¥{m['final_equity']:,.2f}",
        }
    
    def plot(self, show=True):
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(12, 6))
            plt.plot(self.equity_curve)
            plt.title('Equity Curve')
            plt.xlabel('Trading Day')
            plt.ylabel('Equity')
            plt.grid(True)
            if show:
                plt.show()
            return plt
        except ImportError:
            return None