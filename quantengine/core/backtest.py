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
        self._current_date = None

    def run(self, strategy, klines, params=None):
        strategy_func = self._get_strategy(strategy)
        if strategy_func is None:
            raise ValueError(f"Unknown strategy: {strategy}")

        params = params or {}
        self._reset()

        for i, kline in enumerate(klines):
            date = kline.get('date', '')

            # T+1 规则：新交易日到来时，解冻所有持仓
            if self._current_date is not None and date != self._current_date:
                self._unfreeze_all_positions()
            self._current_date = date

            close = Decimal(str(kline.get('close', 0)))
            high = Decimal(str(kline.get('high', 0)))
            low = Decimal(str(kline.get('low', 0)))

            signal = strategy_func(klines[:i+1], params)

            if signal == 'buy' and self.cash > 0:
                self._execute_buy(kline, klines[:i+1], params)
            elif signal == 'sell' and self.positions:
                self._execute_sell(kline, params)

            equity = self.cash
            for code, pos in self.positions.items():
                equity += pos['quantity'] * close
            self.equity_curve.append(float(equity))

            self._check_stop_loss_take_profit(kline)

        return BacktestResult(self)

    def _unfreeze_all_positions(self):
        """T+1：新交易日开始时，将所有持仓解冻，使其可卖"""
        for pos in self.positions.values():
            for lot in pos.get('positions', []):
                lot['frozen'] = False

    def _get_price_limit(self, stock_code, kline):
        """根据股票代码/名称判断涨跌停幅度：ST 5%、创业板/科创板 20%、普通 10%"""
        code = str(stock_code or '')
        name = kline.get('name') or kline.get('stock_name') or ''
        if isinstance(name, str) and 'ST' in name.upper():
            return Decimal('0.05')
        if kline.get('is_st'):
            return Decimal('0.05')
        if code.startswith(('300', '301', '688')):
            return Decimal('0.20')
        return Decimal('0.10')

    def _is_limit_up(self, kline, prev_close, stock_code):
        """是否触发涨停（无法买入）。涨幅 >= limit 视为涨停"""
        if prev_close is None or prev_close <= 0:
            return False
        limit = self._get_price_limit(stock_code, kline)
        close = Decimal(str(kline.get('close', 0)))
        change_ratio = (close - prev_close) / prev_close
        return change_ratio >= limit - Decimal('0.0001')

    def _is_limit_down(self, kline, prev_close, stock_code):
        """是否触发跌停（无法卖出）。跌幅 >= limit 视为跌停"""
        if prev_close is None or prev_close <= 0:
            return False
        limit = self._get_price_limit(stock_code, kline)
        close = Decimal(str(kline.get('close', 0)))
        change_ratio = (prev_close - close) / prev_close
        return change_ratio >= limit - Decimal('0.0001')
    
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
    
    def _execute_buy(self, kline, klines, params):
        code = kline.get('code', 'unknown')
        close = Decimal(str(kline.get('close', 0)))

        if close <= 0:
            return

        # B-01 涨跌停限制：涨停无法买入
        prev_close = None
        if len(klines) >= 2:
            prev_close = Decimal(str(klines[-2].get('close', 0)))
        if self._is_limit_up(kline, prev_close, code):
            self.logs.append(f"{kline.get('date', '')} SKIP BUY {code} (涨停)")
            return

        # F-02 仓位管理
        max_positions = int(self.settings.get('max_positions', 10))
        max_weight = Decimal(str(self.settings.get('max_weight', 0.2)))

        current_position_count = sum(
            1 for p in self.positions.values() if p['quantity'] > 0
        )
        is_new_position = (
            code not in self.positions or self.positions[code]['quantity'] <= 0
        )
        if is_new_position and current_position_count >= max_positions:
            self.logs.append(
                f"{kline.get('date', '')} SKIP BUY {code} (持仓数达上限 {max_positions})"
            )
            return

        # 计算 total_equity（用当前 close 估值持仓）
        total_equity = self.cash
        for pos_code, pos in self.positions.items():
            if pos['quantity'] > 0:
                total_equity += pos['quantity'] * close

        # 目标买入金额：用户指定 target_weight 优先，否则等权分配
        target_weight = params.get('target_weight') if params else None
        if target_weight is not None:
            target_amount = Decimal(str(target_weight)) * total_equity
        else:
            target_amount = total_equity / Decimal(str(max_positions))

        # 单票上限：max_weight * total_equity
        max_amount = max_weight * total_equity
        if target_amount > max_amount:
            target_amount = max_amount

        # 已有该股票持仓金额 → 仅补仓差额
        existing_amount = Decimal('0')
        if code in self.positions and self.positions[code]['quantity'] > 0:
            existing_amount = self.positions[code]['quantity'] * close
        buy_amount = target_amount - existing_amount
        if buy_amount <= 0:
            return

        # 不超过可用现金
        if buy_amount > self.cash:
            buy_amount = self.cash

        commission_rate = Decimal(str(self.settings['commission_rate']))
        min_commission = Decimal(str(self.settings['min_commission']))
        slippage_bps = Decimal(str(self.settings['slippage_bps']))

        slippage = close * slippage_bps / Decimal('10000')
        actual_price = close + slippage

        # 估算佣金用于计算数量
        est_commission = buy_amount * commission_rate
        if est_commission < min_commission:
            est_commission = min_commission

        quantity = (
            (buy_amount - est_commission) / actual_price
        ).quantize(Decimal('0'), rounding=ROUND_HALF_UP)

        if quantity <= 0:
            return

        # 实际佣金按成交计算
        commission = actual_price * quantity * commission_rate
        if commission < min_commission:
            commission = min_commission

        total_cost = quantity * actual_price + commission

        # 防止超过现金（向下调整数量）
        while total_cost > self.cash and quantity > 0:
            quantity -= Decimal('1')
            commission = actual_price * quantity * commission_rate
            if commission < min_commission:
                commission = min_commission
            total_cost = quantity * actual_price + commission

        if quantity <= 0:
            return

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
            'frozen': True  # F-01 T+1：当日买入当日冻结
        })
        self.positions[code]['quantity'] += quantity
        total_quantity = self.positions[code]['quantity']
        total_cost_basis = sum(
            p['quantity'] * p['cost'] for p in self.positions[code]['positions']
        )
        self.positions[code]['avg_cost'] = (
            total_cost_basis / total_quantity
        ).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

        self.trades.append({
            'date': kline.get('date', ''),
            'code': code,
            'type': 'buy',
            'quantity': int(quantity),
            'price': float(actual_price),
            'commission': float(commission),
            'slippage': float(slippage),
        })

        self.logs.append(
            f"{kline.get('date', '')} BUY {code} {int(quantity)} @ {float(actual_price)}"
        )

    def _execute_sell(self, kline, params):
        code = kline.get('code', 'unknown')

        if code not in self.positions:
            return

        pos = self.positions[code]
        if pos['quantity'] <= 0:
            return

        close = Decimal(str(kline.get('close', 0)))
        if close <= 0:
            return

        # B-01 涨跌停限制：跌停无法卖出
        prev_close_val = kline.get('prev_close')
        if prev_close_val is not None:
            prev_close = Decimal(str(prev_close_val))
            if self._is_limit_down(kline, prev_close, code):
                self.logs.append(f"{kline.get('date', '')} SKIP SELL {code} (跌停)")
                return

        # F-01 T+1 规则：只卖出未冻结的 lots
        sellable_lots = [
            lot for lot in pos['positions']
            if not lot.get('frozen', False) and lot['quantity'] > 0
        ]
        if not sellable_lots:
            self.logs.append(
                f"{kline.get('date', '')} SKIP SELL {code} (T+1 冻结)"
            )
            return

        quantity = sum(lot['quantity'] for lot in sellable_lots)
        if quantity <= 0:
            return

        slippage = close * Decimal(str(self.settings['slippage_bps'])) / Decimal('10000')
        actual_price = close - slippage

        commission_rate = Decimal(str(self.settings['commission_rate']))
        min_commission = Decimal(str(self.settings['min_commission']))
        stamp_tax_rate = Decimal(str(self.settings['stamp_tax_rate']))

        commission = actual_price * quantity * commission_rate
        if commission < min_commission:
            commission = min_commission

        stamp_tax = actual_price * quantity * stamp_tax_rate

        total_revenue = quantity * actual_price - commission - stamp_tax
        avg_cost = pos['avg_cost']
        profit = total_revenue - quantity * avg_cost

        self.cash += total_revenue

        # 移除已卖出的 lots，保留仍冻结或数量为 0 的
        pos['positions'] = [
            lot for lot in pos['positions']
            if lot.get('frozen', False) or lot['quantity'] <= 0
        ]
        pos['quantity'] -= quantity
        if pos['quantity'] <= 0:
            pos['quantity'] = Decimal('0')
            pos['avg_cost'] = Decimal('0')

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

        self.logs.append(
            f"{kline.get('date', '')} SELL {code} {int(quantity)} @ {float(actual_price)}"
        )
    
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
        self._current_date = None
    
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