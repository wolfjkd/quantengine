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
        assert len(catalog) >= 8
        assert 'mom_20' in catalog
        assert 'vol_20' in catalog
        assert 'ma_bias' in catalog
        assert 'turnover' in catalog
    
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