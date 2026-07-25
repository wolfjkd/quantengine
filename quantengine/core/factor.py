from quantcore.indicators import ma, rsi


class FactorEngine:
    """因子引擎 - 5类22因子

    5 类分组：
        - 价值类（5个）：pe_ratio / pb_ratio / ps_ratio / dividend_yield / market_cap
        - 成长类（4个）：revenue_growth / profit_growth / roe / roa
        - 质量类（5个）：gross_margin / net_margin / debt_ratio / current_ratio / cash_flow_ratio
        - 动量类（4个）：mom_20 / mom_60 / momentum_5 / rsi_14
        - 风险类（4个）：vol_20 / vol_60 / max_drawdown_60 / beta

    财务类因子（价值/成长/质量）从 K 线最后一根的基本面快照字段读取，
    若 stock_data 中无对应字段，则返回 None，并在评分时跳过该因子。
    纯价格类因子（动量/风险）从 K 线数据直接计算。
    """

    _factors = {
        # ===== 价值类（5个） =====
        'pe_ratio': {
            'name': '市盈率',
            'category': 'value',
            'direction': 'negative',
            'default_weight': 1.0,
            'description': '股价/每股收益，越低越便宜',
        },
        'pb_ratio': {
            'name': '市净率',
            'category': 'value',
            'direction': 'negative',
            'default_weight': 1.0,
            'description': '股价/每股净资产，越低越便宜',
        },
        'ps_ratio': {
            'name': '市销率',
            'category': 'value',
            'direction': 'negative',
            'default_weight': 0.5,
            'description': '股价/每股营收，越低越便宜',
        },
        'dividend_yield': {
            'name': '股息率',
            'category': 'value',
            'direction': 'positive',
            'default_weight': 0.8,
            'description': '每股股息/股价，越高越好',
        },
        'market_cap': {
            'name': '市值',
            'category': 'value',
            'direction': 'positive',
            'default_weight': 0.5,
            'description': '总市值（小市值效应）',
        },
        # ===== 成长类（4个） =====
        'revenue_growth': {
            'name': '营收增长率',
            'category': 'growth',
            'direction': 'positive',
            'default_weight': 1.0,
            'description': '营业收入同比增长率',
        },
        'profit_growth': {
            'name': '净利润增长率',
            'category': 'growth',
            'direction': 'positive',
            'default_weight': 1.0,
            'description': '净利润同比增长率',
        },
        'roe': {
            'name': '净资产收益率',
            'category': 'growth',
            'direction': 'positive',
            'default_weight': 0.8,
            'description': '净利润/净资产',
        },
        'roa': {
            'name': '总资产收益率',
            'category': 'growth',
            'direction': 'positive',
            'default_weight': 0.6,
            'description': '净利润/总资产',
        },
        # ===== 质量类（5个） =====
        'gross_margin': {
            'name': '毛利率',
            'category': 'quality',
            'direction': 'positive',
            'default_weight': 0.8,
            'description': '毛利/营业收入',
        },
        'net_margin': {
            'name': '净利率',
            'category': 'quality',
            'direction': 'positive',
            'default_weight': 0.8,
            'description': '净利润/营业收入',
        },
        'debt_ratio': {
            'name': '资产负债率',
            'category': 'quality',
            'direction': 'negative',
            'default_weight': 0.5,
            'description': '总负债/总资产，越低越好',
        },
        'current_ratio': {
            'name': '流动比率',
            'category': 'quality',
            'direction': 'positive',
            'default_weight': 0.5,
            'description': '流动资产/流动负债',
        },
        'cash_flow_ratio': {
            'name': '现金流比率',
            'category': 'quality',
            'direction': 'positive',
            'default_weight': 0.5,
            'description': '经营现金流/净利润',
        },
        # ===== 动量类（4个） =====
        'mom_20': {
            'name': '20日动量',
            'category': 'momentum',
            'direction': 'positive',
            'default_weight': 1.0,
            'description': '20日收益率',
        },
        'mom_60': {
            'name': '60日动量',
            'category': 'momentum',
            'direction': 'positive',
            'default_weight': 0.8,
            'description': '60日收益率',
        },
        'momentum_5': {
            'name': '5日动量',
            'category': 'momentum',
            'direction': 'positive',
            'default_weight': 0.8,
            'description': '5日收益率',
        },
        'rsi_14': {
            'name': 'RSI(14)',
            'category': 'momentum',
            'direction': 'neutral',
            'default_weight': 0.2,
            'description': '相对强弱指数（中值回归）',
        },
        # ===== 风险类（4个） =====
        'vol_20': {
            'name': '20日波动率',
            'category': 'risk',
            'direction': 'negative',
            'default_weight': 0.5,
            'description': '20日收益率年化标准差',
        },
        'vol_60': {
            'name': '60日波动率',
            'category': 'risk',
            'direction': 'negative',
            'default_weight': 0.5,
            'description': '60日收益率年化标准差',
        },
        'max_drawdown_60': {
            'name': '60日最大回撤',
            'category': 'risk',
            'direction': 'negative',
            'default_weight': 0.6,
            'description': '过去60日最大回撤',
        },
        'beta': {
            'name': '贝塔系数',
            'category': 'risk',
            'direction': 'negative',
            'default_weight': 0.5,
            'description': '相对市场敏感度（低 beta 效应）',
        },
    }

    @classmethod
    def catalog(cls):
        return cls._factors

    @classmethod
    def get_categories(cls):
        """返回 5 类分组：{category: [factor_code, ...]}"""
        categories = {}
        for code, config in cls._factors.items():
            cat = config.get('category', 'other')
            categories.setdefault(cat, []).append(code)
        return categories

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

                # 财务因子无数据时跳过
                if factor_value is None:
                    continue

                direction = config['direction']

                if direction == 'negative':
                    factor_value = -factor_value
                # neutral / positive 不调整方向

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

            if factor_value is None:
                continue

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
        """计算因子值。无数据时返回 None。"""
        if not klines:
            return None

        closes = [k.get('close', 0) for k in klines]
        last_kline = klines[-1] if klines else {}

        # ===== 价值类（从基本面快照读取，无则 None） =====
        if factor_code == 'pe_ratio':
            return cls._calc_field(last_kline, 'pe_ratio')
        elif factor_code == 'pb_ratio':
            return cls._calc_field(last_kline, 'pb_ratio')
        elif factor_code == 'ps_ratio':
            return cls._calc_field(last_kline, 'ps_ratio')
        elif factor_code == 'dividend_yield':
            return cls._calc_field(last_kline, 'dividend_yield')
        elif factor_code == 'market_cap':
            return cls._calc_field(last_kline, 'market_cap')

        # ===== 成长类 =====
        elif factor_code == 'revenue_growth':
            return cls._calc_field(last_kline, 'revenue_growth')
        elif factor_code == 'profit_growth':
            return cls._calc_field(last_kline, 'profit_growth')
        elif factor_code == 'roe':
            return cls._calc_field(last_kline, 'roe')
        elif factor_code == 'roa':
            return cls._calc_field(last_kline, 'roa')

        # ===== 质量类 =====
        elif factor_code == 'gross_margin':
            return cls._calc_field(last_kline, 'gross_margin')
        elif factor_code == 'net_margin':
            return cls._calc_field(last_kline, 'net_margin')
        elif factor_code == 'debt_ratio':
            return cls._calc_field(last_kline, 'debt_ratio')
        elif factor_code == 'current_ratio':
            return cls._calc_field(last_kline, 'current_ratio')
        elif factor_code == 'cash_flow_ratio':
            return cls._calc_field(last_kline, 'cash_flow_ratio')

        # ===== 动量类 =====
        elif factor_code == 'mom_20':
            return cls._calc_mom(closes, 20)
        elif factor_code == 'mom_60':
            return cls._calc_mom(closes, 60)
        elif factor_code == 'momentum_5':
            return cls._calc_mom(closes, 5)
        elif factor_code == 'rsi_14':
            return cls._calc_rsi(closes, 14)

        # ===== 风险类 =====
        elif factor_code == 'vol_20':
            return cls._calc_vol(closes, 20)
        elif factor_code == 'vol_60':
            return cls._calc_vol(closes, 60)
        elif factor_code == 'max_drawdown_60':
            return cls._calc_max_drawdown(closes, 60)
        elif factor_code == 'beta':
            return cls._calc_field(last_kline, 'beta')

        return None

    # ===== 因子计算辅助函数 =====

    @staticmethod
    def _calc_field(stock_data, field):
        """从基本面快照（K线 dict）读取字段。无则返回 None。"""
        if not isinstance(stock_data, dict):
            return None
        val = stock_data.get(field)
        if val is None:
            return None
        try:
            fval = float(val)
        except (TypeError, ValueError):
            return None
        if fval == 0:
            return None
        return fval

    @staticmethod
    def _calc_mom(closes, period):
        """N日动量 = closes[-1] / closes[-period] - 1"""
        if len(closes) < period:
            return None
        base = closes[-period]
        if base == 0:
            return None
        return closes[-1] / base - 1

    @staticmethod
    def _calc_rsi(closes, period=14):
        rsi_vals = rsi(closes, period)
        if not rsi_vals:
            return None
        return rsi_vals[-1]

    @staticmethod
    def _calc_vol(closes, period=20):
        """N日年化波动率（基于最近 N 日收益率）"""
        if len(closes) < period + 1:
            return None
        returns = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
        if len(returns) < period:
            return None
        recent_returns = returns[-period:]
        mean = sum(recent_returns) / len(recent_returns)
        variance = sum((r - mean) ** 2 for r in recent_returns) / len(recent_returns)
        return (variance ** 0.5) * (252 ** 0.5)

    @staticmethod
    def _calc_max_drawdown(closes, period=60):
        """N日最大回撤（负数或0）"""
        if len(closes) < period:
            return None
        prices = closes[-period:]
        peak = prices[0]
        max_dd = 0.0
        for p in prices:
            if p > peak:
                peak = p
            if peak > 0:
                dd = p / peak - 1
                if dd < max_dd:
                    max_dd = dd
        return max_dd

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
