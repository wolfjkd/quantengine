import pytest
from quantengine.core.factor import FactorEngine


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


class TestFactorEngine:
    def test_catalog(self):
        catalog = FactorEngine.catalog()
        # 5 类 22 因子
        assert len(catalog) == 22
        # 价值类
        assert 'pe_ratio' in catalog
        assert 'pb_ratio' in catalog
        assert 'ps_ratio' in catalog
        assert 'dividend_yield' in catalog
        assert 'market_cap' in catalog
        # 成长类
        assert 'revenue_growth' in catalog
        assert 'profit_growth' in catalog
        assert 'roe' in catalog
        assert 'roa' in catalog
        # 质量类
        assert 'gross_margin' in catalog
        assert 'net_margin' in catalog
        assert 'debt_ratio' in catalog
        assert 'current_ratio' in catalog
        assert 'cash_flow_ratio' in catalog
        # 动量类
        assert 'mom_20' in catalog
        assert 'mom_60' in catalog
        assert 'momentum_5' in catalog
        assert 'rsi_14' in catalog
        # 风险类
        assert 'vol_20' in catalog
        assert 'vol_60' in catalog
        assert 'max_drawdown_60' in catalog
        assert 'beta' in catalog

    def test_get_categories(self):
        categories = FactorEngine.get_categories()
        assert set(categories.keys()) == {'value', 'growth', 'quality', 'momentum', 'risk'}
        assert len(categories['value']) == 5
        assert len(categories['growth']) == 4
        assert len(categories['quality']) == 5
        assert len(categories['momentum']) == 4
        assert len(categories['risk']) == 4
    
    def test_score(self):
        stocks_data = {
            '000001': generate_test_klines(50),
            '000002': generate_test_klines(50, base_price=15.0),
            '000003': generate_test_klines(50, base_price=8.0),
        }
        
        results = FactorEngine.score(stocks_data)
        
        assert len(results) == 3
        assert results[0]['score'] >= results[-1]['score']
    
    def test_score_with_custom_weights(self):
        stocks_data = {
            '000001': generate_test_klines(50),
            '000002': generate_test_klines(50),
        }
        
        weights = {'mom_20': 2.0, 'vol_20': 0.0}
        results = FactorEngine.score(stocks_data, factor_weights=weights)
        
        assert len(results) == 2
    
    def test_ic_analysis(self):
        stocks_data = {
            '000001': generate_test_klines(80),
            '000002': generate_test_klines(80),
            '000003': generate_test_klines(80),
            '000004': generate_test_klines(80),
            '000005': generate_test_klines(80),
        }
        
        result = FactorEngine.ic_analysis('mom_20', stocks_data)
        
        assert result is not None
        assert 'ic' in result
        assert 'rank_ic' in result
        assert 'samples' in result
        assert result['samples'] == 5
    
    def test_ic_analysis_unknown_factor(self):
        stocks_data = {'000001': generate_test_klines(80)}
        
        with pytest.raises(ValueError):
            FactorEngine.ic_analysis('unknown_factor', stocks_data)
    
    def test_score_with_filters(self):
        stocks_data = {
            '000001': generate_test_klines(50),
            '000002': generate_test_klines(50),
            '000003': generate_test_klines(50),
        }

        results = FactorEngine.score(stocks_data, filters={'min_score': 0})

        assert len(results) >= 1

    def test_score_with_fundamental_data(self):
        """带财务数据的评分：财务因子应参与计算"""
        klines = generate_test_klines(50)
        # 给最后一根 K 线添加财务字段
        klines[-1].update({
            'pe_ratio': 15.0,
            'pb_ratio': 2.0,
            'roe': 0.15,
            'gross_margin': 0.30,
            'beta': 1.0,
            'market_cap': 200,
        })
        stocks_data = {'000001': klines}
        results = FactorEngine.score(stocks_data)
        assert len(results) == 1
        # 财务因子应出现在 factor_scores 中
        factor_scores = results[0]['factor_scores']
        assert 'pe_ratio' in factor_scores
        assert 'pb_ratio' in factor_scores
        assert 'roe' in factor_scores
        assert 'gross_margin' in factor_scores
        assert 'beta' in factor_scores
        assert 'market_cap' in factor_scores

    def test_score_skip_zero_weight(self):
        """权重 <= 0 的因子应被跳过"""
        stocks_data = {'000001': generate_test_klines(50)}
        # 所有因子权重设为 0
        weights = {code: 0.0 for code in FactorEngine.catalog().keys()}
        results = FactorEngine.score(stocks_data, factor_weights=weights)
        assert len(results) == 1
        assert results[0]['score'] == 0
        assert results[0]['factor_scores'] == {}

    def test_score_with_negative_weight(self):
        """负权重应被跳过（weight <= 0）"""
        stocks_data = {'000001': generate_test_klines(50)}
        weights = {'mom_20': -1.0, 'rsi_14': 1.0}
        results = FactorEngine.score(stocks_data, factor_weights=weights)
        assert len(results) == 1
        # mom_20 应被跳过
        assert 'mom_20' not in results[0]['factor_scores']

    def test_ic_analysis_with_fundamental(self):
        """财务因子的 IC 分析（无数据时 samples=0）"""
        stocks_data = {
            '000001': generate_test_klines(80),
            '000002': generate_test_klines(80),
        }
        # 财务因子无数据，应返回 samples=0
        result = FactorEngine.ic_analysis('pe_ratio', stocks_data)
        assert result['samples'] == 0
        assert result['ic'] == 0

    def test_ic_analysis_fundamental_with_data(self):
        """财务因子的 IC 分析（有数据时计算 IC）"""
        stocks_data = {}
        for i, code in enumerate(['000001', '000002', '000003', '000004']):
            klines = generate_test_klines(80, base_price=10.0 + i)
            # ic_analysis 内部调用 klines[:-5]，所以 pe_ratio 必须放在 klines[-6] 或更早
            klines[-6].update({'pe_ratio': 10.0 + i * 5})
            stocks_data[code] = klines
        result = FactorEngine.ic_analysis('pe_ratio', stocks_data)
        assert result['samples'] == 4

    def test_calculate_factor_unknown(self):
        """未知因子应返回 None"""
        result = FactorEngine._calculate_factor('unknown_factor', generate_test_klines(50))
        assert result is None

    def test_calculate_factor_empty_klines(self):
        """空 K 线应返回 None"""
        result = FactorEngine._calculate_factor('mom_20', [])
        assert result is None

    def test_calc_field_invalid(self):
        """_calc_field 异常处理"""
        # 非 dict
        assert FactorEngine._calc_field('not_dict', 'pe_ratio') is None
        # None
        assert FactorEngine._calc_field(None, 'pe_ratio') is None
        # 字段不存在
        assert FactorEngine._calc_field({}, 'pe_ratio') is None
        # 字段为 None
        assert FactorEngine._calc_field({'pe_ratio': None}, 'pe_ratio') is None
        # 字段为 0
        assert FactorEngine._calc_field({'pe_ratio': 0}, 'pe_ratio') is None
        # 字段为非数值字符串
        assert FactorEngine._calc_field({'pe_ratio': 'abc'}, 'pe_ratio') is None
        # 合法值
        assert FactorEngine._calc_field({'pe_ratio': 15.5}, 'pe_ratio') == 15.5
        assert FactorEngine._calc_field({'pe_ratio': '15.5'}, 'pe_ratio') == 15.5

    def test_calc_mom_short_data(self):
        """_calc_mom 数据不足返回 None"""
        assert FactorEngine._calc_mom([1, 2, 3], 20) is None
        # base = 0：closes[-5] 必须为 0
        # 对于 [a, b, c, d, e, f]，closes[-5] = b，所以第二个元素需为 0
        closes = [1, 0, 2, 3, 4, 5]
        assert FactorEngine._calc_mom(closes, 5) is None

    def test_calc_rsi_short_data(self):
        """_calc_rsi 数据不足返回 None"""
        assert FactorEngine._calc_rsi([1, 2, 3], 14) is None

    def test_calc_vol_short_data(self):
        """_calc_vol 数据不足返回 None"""
        assert FactorEngine._calc_vol([1, 2, 3], 20) is None

    def test_calc_max_drawdown(self):
        """_calc_max_drawdown 计算最大回撤"""
        # 数据不足
        assert FactorEngine._calc_max_drawdown([1, 2, 3], 60) is None
        # 上涨趋势，回撤 = 0
        closes = [10 * (1.01 ** i) for i in range(60)]
        dd = FactorEngine._calc_max_drawdown(closes, 60)
        assert dd == 0
        # 下跌趋势，回撤为负
        closes = [10 * (0.99 ** i) for i in range(60)]
        dd = FactorEngine._calc_max_drawdown(closes, 60)
        assert dd < 0
        # 先涨后跌
        closes = [10, 11, 12, 13, 12, 11, 10, 9, 8, 7] + [7] * 50
        dd = FactorEngine._calc_max_drawdown(closes, 60)
        assert dd < 0

    def test_calculate_correlation_short(self):
        """_calculate_correlation 数据不足返回 0"""
        assert FactorEngine._calculate_correlation([], []) == 0
        assert FactorEngine._calculate_correlation([1], [2]) == 0
        # 标准差为 0
        assert FactorEngine._calculate_correlation([1, 1, 1], [1, 2, 3]) == 0

    def test_apply_filters_min_volume(self):
        """_apply_filters min_volume 分支（当前为 pass）"""
        stocks_data = {'000001': generate_test_klines(50)}
        results = FactorEngine.score(stocks_data, filters={'min_volume': 1000})
        assert len(results) == 1