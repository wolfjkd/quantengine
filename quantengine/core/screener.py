from quantcore.indicators import ma, rsi, boll, atr


class Screener:
    """条件选股引擎 - 5类30+条件

    5 类分组：
        - 基本面（9个）：pe_ratio / pb_ratio / ps_ratio / dividend_yield / market_cap / roe / roa / gross_margin / net_margin
        - 技术面：ma_5 / ma_20 / ma_60 / macd_golden_cross / macd_death_cross / kdj_golden_cross / kdj_death_cross
                  rsi_oversold / rsi_overbought / boll_lower_touch / boll_upper_touch
                  （并保留 ma_bullish / ma_bearish / rsi_range / momentum_range / new_high / new_low / boll_breakout
                  / macd_gold / macd_dead / kdj_gold / kdj_dead 兼容旧命名）
        - 资金面：volume_ratio / turnover_rate / amount_filter / volume_surge
        - 风险面：volatility_20 / max_drawdown_60 / beta
        - 标记类：is_st / is_new / is_index_component / price_range / board_type

    财务类条件需 stock_data 中携带基本面字段（如 pe_ratio），
    若无对应字段返回 False。
    """

    _conditions = {
        # ===== 基本面（9个） =====
        'pe_ratio': {
            'name': '市盈率范围',
            'category': 'fundamental',
            'description': 'PE在指定区间内',
            'params': {'min': 0, 'max': 50},
        },
        'pb_ratio': {
            'name': '市净率范围',
            'category': 'fundamental',
            'description': 'PB在指定区间内',
            'params': {'min': 0, 'max': 5},
        },
        'ps_ratio': {
            'name': '市销率范围',
            'category': 'fundamental',
            'description': 'PS在指定区间内',
            'params': {'min': 0, 'max': 10},
        },
        'dividend_yield': {
            'name': '股息率范围',
            'category': 'fundamental',
            'description': '股息率大于等于指定值',
            'params': {'min': 0.02},
        },
        'market_cap': {
            'name': '市值范围',
            'category': 'fundamental',
            'description': '总市值在指定区间内（亿）',
            'params': {'min': 50, 'max': 1000},
        },
        'roe': {
            'name': 'ROE范围',
            'category': 'fundamental',
            'description': 'ROE大于等于指定值',
            'params': {'min': 0.10},
        },
        'roa': {
            'name': 'ROA范围',
            'category': 'fundamental',
            'description': 'ROA大于等于指定值',
            'params': {'min': 0.05},
        },
        'gross_margin': {
            'name': '毛利率范围',
            'category': 'fundamental',
            'description': '毛利率大于等于指定值',
            'params': {'min': 0.20},
        },
        'net_margin': {
            'name': '净利率范围',
            'category': 'fundamental',
            'description': '净利率大于等于指定值',
            'params': {'min': 0.10},
        },
        # ===== 技术面（11个新增 + 11个现有保留） =====
        'ma_5': {
            'name': '5日均线位置',
            'category': 'technical',
            'description': '收盘价在5日均线之上/之下',
            'params': {'direction': 'above'},
        },
        'ma_20': {
            'name': '20日均线位置',
            'category': 'technical',
            'description': '收盘价在20日均线之上/之下',
            'params': {'direction': 'above'},
        },
        'ma_60': {
            'name': '60日均线位置',
            'category': 'technical',
            'description': '收盘价在60日均线之上/之下',
            'params': {'direction': 'above'},
        },
        'macd_golden_cross': {
            'name': 'MACD金叉',
            'category': 'technical',
            'description': 'DIF上穿DEA',
            'params': {},
        },
        'macd_death_cross': {
            'name': 'MACD死叉',
            'category': 'technical',
            'description': 'DIF下穿DEA',
            'params': {},
        },
        'kdj_golden_cross': {
            'name': 'KDJ金叉',
            'category': 'technical',
            'description': 'K线上穿D线',
            'params': {},
        },
        'kdj_death_cross': {
            'name': 'KDJ死叉',
            'category': 'technical',
            'description': 'K线下穿D线',
            'params': {},
        },
        'rsi_oversold': {
            'name': 'RSI超卖',
            'category': 'technical',
            'description': 'RSI低于指定阈值（默认30）',
            'params': {'threshold': 30},
        },
        'rsi_overbought': {
            'name': 'RSI超买',
            'category': 'technical',
            'description': 'RSI高于指定阈值（默认70）',
            'params': {'threshold': 70},
        },
        'boll_lower_touch': {
            'name': '触及布林下轨',
            'category': 'technical',
            'description': '收盘价触及或跌破布林下轨',
            'params': {},
        },
        'boll_upper_touch': {
            'name': '触及布林上轨',
            'category': 'technical',
            'description': '收盘价触及或突破布林上轨',
            'params': {},
        },
        # 现有技术面条件（保留兼容旧命名）
        'ma_bullish': {
            'name': '均线多头排列',
            'category': 'technical',
            'description': 'MA5 > MA10 > MA20 > MA60',
            'params': {},
        },
        'ma_bearish': {
            'name': '均线空头排列',
            'category': 'technical',
            'description': 'MA5 < MA10 < MA20 < MA60',
            'params': {},
        },
        'rsi_range': {
            'name': 'RSI区间',
            'category': 'technical',
            'description': 'RSI在指定区间内',
            'params': {'min': 30, 'max': 70},
        },
        'momentum_range': {
            'name': '动量区间',
            'category': 'technical',
            'description': '近期涨幅在指定区间内',
            'params': {'min': -0.1, 'max': 0.1},
        },
        'new_high': {
            'name': '创新高',
            'category': 'technical',
            'description': '收盘价创近期新高',
            'params': {'period': 60},
        },
        'new_low': {
            'name': '创新低',
            'category': 'technical',
            'description': '收盘价创近期新低',
            'params': {'period': 60},
        },
        'boll_breakout': {
            'name': '布林带突破',
            'category': 'technical',
            'description': '收盘价突破布林带上轨或下轨',
            'params': {'direction': 'up'},
        },
        'macd_gold': {
            'name': 'MACD金叉(旧)',
            'category': 'technical',
            'description': 'DIF上穿DEA（兼容旧命名）',
            'params': {},
        },
        'macd_dead': {
            'name': 'MACD死叉(旧)',
            'category': 'technical',
            'description': 'DIF下穿DEA（兼容旧命名）',
            'params': {},
        },
        'kdj_gold': {
            'name': 'KDJ金叉(旧)',
            'category': 'technical',
            'description': 'K线上穿D线（兼容旧命名）',
            'params': {},
        },
        'kdj_dead': {
            'name': 'KDJ死叉(旧)',
            'category': 'technical',
            'description': 'K线下穿D线（兼容旧命名）',
            'params': {},
        },
        # ===== 资金面（2个新增 + 2个现有） =====
        'volume_ratio': {
            'name': '量比',
            'category': 'money',
            'description': '今日成交量与5日均量的比值大于阈值',
            'params': {'min': 1.5},
        },
        'turnover_rate': {
            'name': '换手率',
            'category': 'money',
            'description': '换手率在指定区间内',
            'params': {'min': 0.01, 'max': 0.20},
        },
        'amount_filter': {
            'name': '成交额过滤',
            'category': 'money',
            'description': '成交额大于指定值',
            'params': {'min_amount': 100000000},
        },
        'volume_surge': {
            'name': '放量',
            'category': 'money',
            'description': '成交量放大',
            'params': {'ratio': 2.0},
        },
        # ===== 风险面（3个） =====
        'volatility_20': {
            'name': '20日波动率',
            'category': 'risk',
            'description': '20日年化波动率不超过指定值',
            'params': {'max': 0.40},
        },
        'max_drawdown_60': {
            'name': '60日最大回撤',
            'category': 'risk',
            'description': '60日最大回撤不小于指定值（负数，如-0.25表示回撤不超过25%）',
            'params': {'min': -0.25},
        },
        'beta': {
            'name': '贝塔系数',
            'category': 'risk',
            'description': '贝塔在指定区间内',
            'params': {'min': 0.5, 'max': 1.5},
        },
        # ===== 标记类（5个） =====
        'is_st': {
            'name': '是否ST股',
            'category': 'tag',
            'description': '是否ST股（默认过滤ST）',
            'params': {'exclude': True},
        },
        'is_new': {
            'name': '是否次新股',
            'category': 'tag',
            'description': '上市<1年（252交易日）',
            'params': {'max_days': 252},
        },
        'is_index_component': {
            'name': '是否指数成分股',
            'category': 'tag',
            'description': '是否指数成分股（沪深300等）',
            'params': {'index': 'hs300'},
        },
        'price_range': {
            'name': '价格区间',
            'category': 'tag',
            'description': '收盘价在指定区间内',
            'params': {'min': 0, 'max': 100},
        },
        'board_type': {
            'name': '板块类型',
            'category': 'tag',
            'description': '主板/创业板/科创板',
            'params': {'board': 'main'},
        },
    }

    @classmethod
    def get_conditions(cls):
        return cls._conditions

    @classmethod
    def get_categories(cls):
        """返回 5 类分组：{category: [cond_code, ...]}"""
        categories = {}
        for code, config in cls._conditions.items():
            cat = config.get('category', 'other')
            categories.setdefault(cat, []).append(code)
        return categories

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

            if cls._check_condition(cond_code, klines, params or {}):
                matched.append(cond_code)

        return matched

    @classmethod
    def _check_condition(cls, cond_code, klines, params):
        closes = [k.get('close', 0) for k in klines]
        highs = [k.get('high', 0) for k in klines]
        lows = [k.get('low', 0) for k in klines]
        volumes = [k.get('volume', 0) for k in klines]
        last_kline = klines[-1] if klines else {}

        # ===== 基本面 =====
        if cond_code == 'pe_ratio':
            return cls._check_field_range(last_kline, 'pe_ratio', params, default_max=50)
        elif cond_code == 'pb_ratio':
            return cls._check_field_range(last_kline, 'pb_ratio', params, default_max=5)
        elif cond_code == 'ps_ratio':
            return cls._check_field_range(last_kline, 'ps_ratio', params, default_max=10)
        elif cond_code == 'dividend_yield':
            return cls._check_field_min(last_kline, 'dividend_yield', params, default_min=0.02)
        elif cond_code == 'market_cap':
            return cls._check_field_range(last_kline, 'market_cap', params, default_max=1000)
        elif cond_code == 'roe':
            return cls._check_field_min(last_kline, 'roe', params, default_min=0.10)
        elif cond_code == 'roa':
            return cls._check_field_min(last_kline, 'roa', params, default_min=0.05)
        elif cond_code == 'gross_margin':
            return cls._check_field_min(last_kline, 'gross_margin', params, default_min=0.20)
        elif cond_code == 'net_margin':
            return cls._check_field_min(last_kline, 'net_margin', params, default_min=0.10)

        # ===== 技术面 =====
        elif cond_code == 'ma_5':
            return cls._check_ma_position(closes, 5, params)
        elif cond_code == 'ma_20':
            return cls._check_ma_position(closes, 20, params)
        elif cond_code == 'ma_60':
            return cls._check_ma_position(closes, 60, params)
        elif cond_code in ('macd_golden_cross', 'macd_gold'):
            return cls._check_macd_cross(closes, gold=True)
        elif cond_code in ('macd_death_cross', 'macd_dead'):
            return cls._check_macd_cross(closes, gold=False)
        elif cond_code in ('kdj_golden_cross', 'kdj_gold'):
            return cls._check_kdj_cross(highs, lows, closes, gold=True)
        elif cond_code in ('kdj_death_cross', 'kdj_dead'):
            return cls._check_kdj_cross(highs, lows, closes, gold=False)
        elif cond_code == 'rsi_oversold':
            threshold = params.get('threshold', 30)
            return cls._check_rsi_threshold(closes, threshold, oversold=True)
        elif cond_code == 'rsi_overbought':
            threshold = params.get('threshold', 70)
            return cls._check_rsi_threshold(closes, threshold, oversold=False)
        elif cond_code == 'boll_lower_touch':
            return cls._check_boll_touch(highs, lows, closes, upper=False)
        elif cond_code == 'boll_upper_touch':
            return cls._check_boll_touch(highs, lows, closes, upper=True)
        elif cond_code == 'boll_breakout':
            direction = params.get('direction', 'up')
            return cls._check_boll_touch(highs, lows, closes, upper=(direction == 'up'))
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
            momentum = closes[-1] / closes[-10] - 1 if closes[-10] != 0 else 0
            min_mom = params.get('min', -0.1)
            max_mom = params.get('max', 0.1)
            return min_mom <= momentum <= max_mom
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
        elif cond_code == 'ma_bullish':
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

        # ===== 资金面 =====
        elif cond_code == 'volume_ratio':
            if len(volumes) < 6:
                return False
            min_ratio = params.get('min', 1.5)
            vol_today = volumes[-1]
            vol_ma5 = sum(volumes[-6:-1]) / 5
            if vol_ma5 <= 0:
                return False
            return (vol_today / vol_ma5) >= min_ratio
        elif cond_code == 'turnover_rate':
            turnover = last_kline.get('turnover_rate') if isinstance(last_kline, dict) else None
            if turnover is None:
                return False
            try:
                t = float(turnover)
            except (TypeError, ValueError):
                return False
            min_t = params.get('min', 0.01)
            max_t = params.get('max', 0.20)
            return min_t <= t <= max_t
        elif cond_code == 'amount_filter':
            amount = last_kline.get('amount', 0) if isinstance(last_kline, dict) else 0
            min_amount = params.get('min_amount', 100000000)
            return amount >= min_amount
        elif cond_code == 'volume_surge':
            if len(volumes) < 6:
                return False
            ratio = params.get('ratio', 2.0)
            today_vol = volumes[-1]
            avg_vol = sum(volumes[-6:-1]) / 5
            if avg_vol <= 0:
                return False
            return today_vol >= avg_vol * ratio

        # ===== 风险面 =====
        elif cond_code == 'volatility_20':
            if len(closes) < 21:
                return False
            returns = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
            recent = returns[-20:]
            mean = sum(recent) / len(recent)
            var = sum((r - mean) ** 2 for r in recent) / len(recent)
            vol = (var ** 0.5) * (252 ** 0.5)
            max_vol = params.get('max', 0.40)
            return vol <= max_vol
        elif cond_code == 'max_drawdown_60':
            if len(closes) < 60:
                return False
            prices = closes[-60:]
            peak = prices[0]
            max_dd = 0.0
            for p in prices:
                if p > peak:
                    peak = p
                if peak > 0:
                    dd = p / peak - 1
                    if dd < max_dd:
                        max_dd = dd
            min_dd = params.get('min', -0.25)
            return max_dd >= min_dd
        elif cond_code == 'beta':
            beta_val = last_kline.get('beta') if isinstance(last_kline, dict) else None
            if beta_val is None:
                return False
            try:
                b = float(beta_val)
            except (TypeError, ValueError):
                return False
            min_b = params.get('min', 0.5)
            max_b = params.get('max', 1.5)
            return min_b <= b <= max_b

        # ===== 标记类 =====
        elif cond_code == 'is_st':
            is_st = last_kline.get('is_st', False) if isinstance(last_kline, dict) else False
            exclude = params.get('exclude', True)
            if exclude:
                return not bool(is_st)
            return bool(is_st)
        elif cond_code == 'is_new':
            if not isinstance(last_kline, dict):
                return False
            ipo_days = last_kline.get('ipo_days')
            if ipo_days is None:
                return False
            try:
                d = int(ipo_days)
            except (TypeError, ValueError):
                return False
            max_days = params.get('max_days', 252)
            return d <= max_days
        elif cond_code == 'is_index_component':
            if not isinstance(last_kline, dict):
                return False
            components = last_kline.get('index_components', [])
            if not isinstance(components, (list, tuple, set)):
                return False
            index = params.get('index', 'hs300')
            return index in components
        elif cond_code == 'price_range':
            close = closes[-1] if closes else 0
            min_price = params.get('min', 0)
            max_price = params.get('max', 100)
            return min_price <= close <= max_price
        elif cond_code == 'board_type':
            if not isinstance(last_kline, dict):
                return False
            board = last_kline.get('board_type')
            if board is None:
                return False
            expected = params.get('board', 'main')
            return board == expected

        return False

    # ===== 条件检查辅助函数 =====

    @staticmethod
    def _check_field_range(stock_data, field, params, default_min=0, default_max=None):
        """检查字段在 [min, max] 区间内。无字段返回 False。"""
        if not isinstance(stock_data, dict):
            return False
        val = stock_data.get(field)
        if val is None:
            return False
        try:
            v = float(val)
        except (TypeError, ValueError):
            return False
        min_v = params.get('min', default_min)
        max_v = params.get('max', default_max)
        if max_v is None:
            return v >= min_v
        return min_v <= v <= max_v

    @staticmethod
    def _check_field_min(stock_data, field, params, default_min=0):
        """检查字段 >= min。无字段返回 False。"""
        if not isinstance(stock_data, dict):
            return False
        val = stock_data.get(field)
        if val is None:
            return False
        try:
            v = float(val)
        except (TypeError, ValueError):
            return False
        min_v = params.get('min', default_min)
        return v >= min_v

    @staticmethod
    def _check_ma_position(closes, period, params):
        """收盘价在 N 日均线之上/之下"""
        if len(closes) < period:
            return False
        ma_val = sum(closes[-period:]) / period
        direction = params.get('direction', 'above')
        if direction == 'above':
            return closes[-1] > ma_val
        else:
            return closes[-1] < ma_val

    @staticmethod
    def _check_macd_cross(closes, gold=True):
        from quantcore.indicators import macd
        result = macd(closes)
        if len(result['dif']) < 2 or len(result['dea']) < 2:
            return False
        if gold:
            return result['dif'][-1] > result['dea'][-1] and result['dif'][-2] <= result['dea'][-2]
        else:
            return result['dif'][-1] < result['dea'][-1] and result['dif'][-2] >= result['dea'][-2]

    @staticmethod
    def _check_kdj_cross(highs, lows, closes, gold=True):
        from quantcore.indicators import kdj
        result = kdj(highs, lows, closes)
        if len(result['k']) < 2 or len(result['d']) < 2:
            return False
        if gold:
            return result['k'][-1] > result['d'][-1] and result['k'][-2] <= result['d'][-2]
        else:
            return result['k'][-1] < result['d'][-1] and result['k'][-2] >= result['d'][-2]

    @staticmethod
    def _check_rsi_threshold(closes, threshold, oversold=True):
        rsi_vals = rsi(closes, 14)
        if not rsi_vals:
            return False
        rsi_val = rsi_vals[-1]
        if oversold:
            return rsi_val <= threshold
        else:
            return rsi_val >= threshold

    @staticmethod
    def _check_boll_touch(highs, lows, closes, upper=True):
        boll_result = boll(highs, lows, closes, 20)
        if not boll_result['upper'] or not boll_result['lower']:
            return False
        close = closes[-1]
        if upper:
            return close >= boll_result['upper'][-1]
        else:
            return close <= boll_result['lower'][-1]

    @classmethod
    def _matches_filters(cls, result, filters):
        if 'min_volume' in filters and result['volume'] < filters['min_volume']:
            return False
        if 'min_price' in filters and result['close'] < filters['min_price']:
            return False
        if 'max_price' in filters and result['close'] > filters['max_price']:
            return False
        return True
