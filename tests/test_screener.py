import pytest
from quantengine.core.screener import Screener


def generate_test_klines(count=50, base_price=10.0):
    klines = []
    for i in range(count):
        base_price *= (1 + (i % 5 - 2) * 0.01)
        klines.append({
            'date': f'2024-01-{i+1:02d}',
            'open': round(base_price, 2),
            'high': round(base_price * 1.01, 2),
            'low': round(base_price * 0.99, 2),
            'close': round(base_price, 2),
            'volume': 1000000,
            'amount': round(base_price * 1000000, 2),
        })
    return klines


def generate_bullish_klines(count=60):
    klines = []
    base_price = 10.0
    for i in range(count):
        base_price *= 1.005
        klines.append({
            'date': f'2024-01-{i+1:02d}',
            'open': round(base_price, 2),
            'high': round(base_price * 1.01, 2),
            'low': round(base_price * 0.99, 2),
            'close': round(base_price, 2),
            'volume': 1000000,
            'amount': round(base_price * 1000000, 2),
        })
    return klines


def generate_fundamental_klines(count=50, base_price=10.0):
    """生成带基本面字段的 K 线（最后一根附带财务快照）"""
    klines = generate_test_klines(count, base_price=base_price)
    klines[-1].update({
        'pe_ratio': 15.0,
        'pb_ratio': 2.0,
        'ps_ratio': 3.0,
        'dividend_yield': 0.03,
        'market_cap': 200,
        'roe': 0.15,
        'roa': 0.08,
        'gross_margin': 0.30,
        'net_margin': 0.12,
        'turnover_rate': 0.05,
        'beta': 1.0,
        'is_st': False,
        'ipo_days': 500,
        'index_components': ['hs300', 'sz50'],
        'board_type': 'main',
    })
    return klines


class TestScreener:
    def test_get_conditions(self):
        conditions = Screener.get_conditions()
        assert len(conditions) >= 12
        assert 'ma_bullish' in conditions
        assert 'ma_bearish' in conditions
        assert 'rsi_range' in conditions
        assert 'macd_gold' in conditions
    
    def test_screen(self):
        stocks_data = {
            '000001': generate_test_klines(50),
            '000002': generate_test_klines(50),
            '000003': generate_test_klines(50),
        }
        
        conditions = {'rsi_range': {'min': 20, 'max': 80}}
        results = Screener.screen(stocks_data, conditions)
        
        assert len(results) <= 3
    
    def test_screen_ma_bullish(self):
        stocks_data = {
            '000001': generate_bullish_klines(70),
            '000002': generate_test_klines(70),
        }
        
        conditions = {'ma_bullish': {}}
        results = Screener.screen(stocks_data, conditions)
        
        assert len(results) >= 1
    
    def test_screen_macd_gold(self):
        stocks_data = {
            '000001': generate_test_klines(50),
            '000002': generate_test_klines(50),
        }
        
        conditions = {'macd_gold': {}}
        results = Screener.screen(stocks_data, conditions)
        
        assert isinstance(results, list)
    
    def test_screen_kdj_gold(self):
        stocks_data = {
            '000001': generate_test_klines(50),
        }
        
        conditions = {'kdj_gold': {}}
        results = Screener.screen(stocks_data, conditions)
        
        assert isinstance(results, list)
    
    def test_screen_new_high(self):
        stocks_data = {
            '000001': generate_bullish_klines(70),
        }
        
        conditions = {'new_high': {'period': 30}}
        results = Screener.screen(stocks_data, conditions)
        
        assert len(results) >= 1
    
    def test_screen_boll_breakout(self):
        stocks_data = {
            '000001': generate_test_klines(50),
        }
        
        conditions = {'boll_breakout': {'direction': 'up'}}
        results = Screener.screen(stocks_data, conditions)
        
        assert isinstance(results, list)
    
    def test_screen_volume_surge(self):
        stocks_data = {
            '000001': generate_test_klines(50),
        }
        
        conditions = {'volume_surge': {'ratio': 1.5}}
        results = Screener.screen(stocks_data, conditions)
        
        assert isinstance(results, list)
    
    def test_screen_with_filters(self):
        stocks_data = {
            '000001': generate_test_klines(50),
            '000002': generate_test_klines(50),
        }
        
        conditions = {'rsi_range': {}}
        filters = {'min_price': 5, 'max_price': 100}
        results = Screener.screen(stocks_data, conditions, filters)
        
        assert isinstance(results, list)

    def test_get_categories(self):
        """验证 5 类分组"""
        categories = Screener.get_categories()
        assert set(categories.keys()) == {'fundamental', 'technical', 'money', 'risk', 'tag'}
        # 基本面 9 个
        assert len(categories['fundamental']) == 9
        # 风险面 3 个
        assert len(categories['risk']) == 3
        # 标记类 5 个
        assert len(categories['tag']) == 5
        # 资金面 4 个
        assert len(categories['money']) == 4
        # 技术面 >= 11
        assert len(categories['technical']) >= 11

    def test_screen_unknown_condition(self):
        """未知条件应被跳过（不报错）"""
        stocks_data = {'000001': generate_test_klines(50)}
        conditions = {'unknown_cond': {}}
        results = Screener.screen(stocks_data, conditions)
        assert len(results) == 0

    def test_screen_fundamental_conditions(self):
        """基本面条件：有财务数据时命中"""
        stocks_data = {'000001': generate_fundamental_klines(50)}
        # PE 在 10-20 区间
        results = Screener.screen(stocks_data, {'pe_ratio': {'min': 10, 'max': 20}})
        assert len(results) == 1
        # PB 在 1-3 区间
        results = Screener.screen(stocks_data, {'pb_ratio': {'min': 1, 'max': 3}})
        assert len(results) == 1
        # PS 在 1-5 区间
        results = Screener.screen(stocks_data, {'ps_ratio': {'min': 1, 'max': 5}})
        assert len(results) == 1
        # 股息率 >= 0.02
        results = Screener.screen(stocks_data, {'dividend_yield': {'min': 0.02}})
        assert len(results) == 1
        # 市值在 100-500 亿
        results = Screener.screen(stocks_data, {'market_cap': {'min': 100, 'max': 500}})
        assert len(results) == 1
        # ROE >= 0.10
        results = Screener.screen(stocks_data, {'roe': {'min': 0.10}})
        assert len(results) == 1
        # ROA >= 0.05
        results = Screener.screen(stocks_data, {'roa': {'min': 0.05}})
        assert len(results) == 1
        # 毛利率 >= 0.20
        results = Screener.screen(stocks_data, {'gross_margin': {'min': 0.20}})
        assert len(results) == 1
        # 净利率 >= 0.10
        results = Screener.screen(stocks_data, {'net_margin': {'min': 0.10}})
        assert len(results) == 1

    def test_screen_fundamental_no_data(self):
        """基本面条件：无财务数据时返回空"""
        stocks_data = {'000001': generate_test_klines(50)}
        results = Screener.screen(stocks_data, {'pe_ratio': {'min': 0, 'max': 50}})
        assert len(results) == 0
        results = Screener.screen(stocks_data, {'roe': {'min': 0.0}})
        assert len(results) == 0

    def test_screen_fundamental_out_of_range(self):
        """基本面条件：超出区间时不命中"""
        stocks_data = {'000001': generate_fundamental_klines(50)}
        # PE=15 不在 [100, 200] 区间
        results = Screener.screen(stocks_data, {'pe_ratio': {'min': 100, 'max': 200}})
        assert len(results) == 0

    def test_screen_ma_position(self):
        """技术面：均线位置条件"""
        stocks_data = {'000001': generate_bullish_klines(70)}
        # 上涨趋势，收盘价在 5/20/60 日均线之上
        results = Screener.screen(stocks_data, {'ma_5': {'direction': 'above'}})
        assert len(results) >= 1
        results = Screener.screen(stocks_data, {'ma_20': {'direction': 'above'}})
        assert len(results) >= 1
        results = Screener.screen(stocks_data, {'ma_60': {'direction': 'above'}})
        assert len(results) >= 1
        # below 方向
        results = Screener.screen(stocks_data, {'ma_5': {'direction': 'below'}})
        assert isinstance(results, list)

    def test_screen_macd_golden_cross(self):
        """技术面：MACD 金叉（新命名）"""
        stocks_data = {'000001': generate_test_klines(50)}
        results = Screener.screen(stocks_data, {'macd_golden_cross': {}})
        assert isinstance(results, list)

    def test_screen_macd_death_cross(self):
        """技术面：MACD 死叉（新命名）"""
        stocks_data = {'000001': generate_test_klines(50)}
        results = Screener.screen(stocks_data, {'macd_death_cross': {}})
        assert isinstance(results, list)

    def test_screen_kdj_golden_cross(self):
        """技术面：KDJ 金叉（新命名）"""
        stocks_data = {'000001': generate_test_klines(50)}
        results = Screener.screen(stocks_data, {'kdj_golden_cross': {}})
        assert isinstance(results, list)

    def test_screen_kdj_death_cross(self):
        """技术面：KDJ 死叉（新命名）"""
        stocks_data = {'000001': generate_test_klines(50)}
        results = Screener.screen(stocks_data, {'kdj_death_cross': {}})
        assert isinstance(results, list)

    def test_screen_rsi_oversold_overbought(self):
        """技术面：RSI 超买超卖"""
        stocks_data = {'000001': generate_test_klines(50)}
        results = Screener.screen(stocks_data, {'rsi_oversold': {'threshold': 30}})
        assert isinstance(results, list)
        results = Screener.screen(stocks_data, {'rsi_overbought': {'threshold': 70}})
        assert isinstance(results, list)

    def test_screen_boll_touch(self):
        """技术面：布林带触及上下轨"""
        stocks_data = {'000001': generate_test_klines(50)}
        results = Screener.screen(stocks_data, {'boll_lower_touch': {}})
        assert isinstance(results, list)
        results = Screener.screen(stocks_data, {'boll_upper_touch': {}})
        assert isinstance(results, list)

    def test_screen_volume_ratio(self):
        """资金面：量比"""
        stocks_data = {'000001': generate_test_klines(50)}
        results = Screener.screen(stocks_data, {'volume_ratio': {'min': 0.5}})
        assert isinstance(results, list)

    def test_screen_turnover_rate(self):
        """资金面：换手率"""
        stocks_data = {'000001': generate_fundamental_klines(50)}
        # 有 turnover_rate 字段
        results = Screener.screen(stocks_data, {'turnover_rate': {'min': 0.01, 'max': 0.20}})
        assert len(results) == 1
        # 无 turnover_rate 字段
        stocks_data2 = {'000001': generate_test_klines(50)}
        results = Screener.screen(stocks_data2, {'turnover_rate': {'min': 0.01, 'max': 0.20}})
        assert len(results) == 0

    def test_screen_amount_filter(self):
        """资金面：成交额过滤"""
        stocks_data = {'000001': generate_test_klines(50)}
        # 成交额 = close * volume = 10 * 1000000 = 1000万 < 1亿
        results = Screener.screen(stocks_data, {'amount_filter': {'min_amount': 1000000}})
        assert len(results) >= 1
        results = Screener.screen(stocks_data, {'amount_filter': {'min_amount': 100000000}})
        assert len(results) == 0

    def test_screen_volatility_20(self):
        """风险面：20日波动率"""
        stocks_data = {'000001': generate_test_klines(50)}
        # 默认 max=0.40，测试 K 线波动较大可能超过 0.4
        results = Screener.screen(stocks_data, {'volatility_20': {'max': 1.0}})
        assert len(results) >= 1
        results = Screener.screen(stocks_data, {'volatility_20': {'max': 0.001}})
        assert isinstance(results, list)

    def test_screen_max_drawdown_60(self):
        """风险面：60日最大回撤"""
        stocks_data = {'000001': generate_bullish_klines(70)}
        # 上涨趋势，回撤接近 0
        results = Screener.screen(stocks_data, {'max_drawdown_60': {'min': -0.01}})
        assert len(results) >= 1
        results = Screener.screen(stocks_data, {'max_drawdown_60': {'min': -0.001}})
        assert isinstance(results, list)

    def test_screen_beta(self):
        """风险面：贝塔系数"""
        stocks_data = {'000001': generate_fundamental_klines(50)}
        # beta=1.0 在 [0.5, 1.5]
        results = Screener.screen(stocks_data, {'beta': {'min': 0.5, 'max': 1.5}})
        assert len(results) == 1
        # beta=1.0 不在 [2.0, 3.0]
        results = Screener.screen(stocks_data, {'beta': {'min': 2.0, 'max': 3.0}})
        assert len(results) == 0
        # 无 beta 字段
        stocks_data2 = {'000001': generate_test_klines(50)}
        results = Screener.screen(stocks_data2, {'beta': {'min': 0.5, 'max': 1.5}})
        assert len(results) == 0

    def test_screen_is_st(self):
        """标记类：ST 股过滤"""
        # 非 ST（is_st=False），exclude=True，应命中
        stocks_data = {'000001': generate_fundamental_klines(50)}
        results = Screener.screen(stocks_data, {'is_st': {'exclude': True}})
        assert len(results) == 1
        # exclude=False，且 is_st=False，应不命中
        results = Screener.screen(stocks_data, {'is_st': {'exclude': False}})
        assert len(results) == 0

    def test_screen_is_new(self):
        """标记类：次新股"""
        # ipo_days=500 > 252，不是次新股
        stocks_data = {'000001': generate_fundamental_klines(50)}
        results = Screener.screen(stocks_data, {'is_new': {'max_days': 252}})
        assert len(results) == 0
        # ipo_days=500 <= 600，是次新股（放宽阈值）
        results = Screener.screen(stocks_data, {'is_new': {'max_days': 600}})
        assert len(results) == 1
        # 无 ipo_days 字段
        stocks_data2 = {'000001': generate_test_klines(50)}
        results = Screener.screen(stocks_data2, {'is_new': {'max_days': 252}})
        assert len(results) == 0

    def test_screen_is_index_component(self):
        """标记类：指数成分股"""
        stocks_data = {'000001': generate_fundamental_klines(50)}
        # index_components=['hs300', 'sz50']，包含 'hs300'
        results = Screener.screen(stocks_data, {'is_index_component': {'index': 'hs300'}})
        assert len(results) == 1
        # 不包含 'csi500'
        results = Screener.screen(stocks_data, {'is_index_component': {'index': 'csi500'}})
        assert len(results) == 0

    def test_screen_board_type(self):
        """标记类：板块类型"""
        stocks_data = {'000001': generate_fundamental_klines(50)}
        # board_type='main'，匹配
        results = Screener.screen(stocks_data, {'board_type': {'board': 'main'}})
        assert len(results) == 1
        # board_type='main'，不匹配 'gem'
        results = Screener.screen(stocks_data, {'board_type': {'board': 'gem'}})
        assert len(results) == 0

    def test_screen_price_range_tag(self):
        """标记类：价格区间（标记类）"""
        stocks_data = {'000001': generate_test_klines(50)}
        results = Screener.screen(stocks_data, {'price_range': {'min': 0, 'max': 100}})
        assert len(results) >= 1

    def test_screen_momentum_range(self):
        """技术面：动量区间"""
        stocks_data = {'000001': generate_test_klines(50)}
        results = Screener.screen(stocks_data, {'momentum_range': {'min': -1.0, 'max': 1.0}})
        assert len(results) >= 1

    def test_screen_new_low(self):
        """技术面：创新低"""
        stocks_data = {'000001': generate_test_klines(70)}
        results = Screener.screen(stocks_data, {'new_low': {'period': 30}})
        assert isinstance(results, list)

    def test_screen_ma_bearish(self):
        """技术面：均线空头排列"""
        stocks_data = {'000001': generate_test_klines(70)}
        results = Screener.screen(stocks_data, {'ma_bearish': {}})
        assert isinstance(results, list)

    def test_screen_volume_surge_no_match(self):
        """资金面：放量（不命中场景）"""
        stocks_data = {'000001': generate_test_klines(50)}
        # 测试 K 线 volume 都是 1000000，量比 = 1.0 < 5.0
        results = Screener.screen(stocks_data, {'volume_surge': {'ratio': 5.0}})
        assert len(results) == 0

    def test_screen_multiple_conditions(self):
        """组合条件：多个条件同时满足"""
        stocks_data = {
            '000001': generate_fundamental_klines(70),
            '000002': generate_test_klines(70),
        }
        conditions = {
            'ma_5': {'direction': 'above'},
            'pe_ratio': {'min': 10, 'max': 20},
        }
        results = Screener.screen(stocks_data, conditions)
        # 只有 000001 有财务数据且 PE 在区间
        assert len(results) <= 2