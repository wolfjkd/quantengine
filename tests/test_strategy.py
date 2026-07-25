import pytest
from quantengine.core.strategy import StrategyLab


def generate_test_klines(count=50):
    klines = []
    base_price = 10.0
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


class TestStrategyLab:
    def test_catalog(self):
        catalog = StrategyLab.catalog()
        assert len(catalog) >= 8
        assert 'dual_ma' in catalog
        assert 'macd' in catalog
        assert 'kdj' in catalog
        assert 'boll' in catalog
    
    def test_run_dual_ma(self):
        klines = generate_test_klines(50)
        signals = StrategyLab.run('dual_ma', klines)
        
        assert len(signals) == len(klines)
        for signal in signals:
            assert signal['signal'] in ['buy', 'sell', 'hold']
    
    def test_run_macd(self):
        klines = generate_test_klines(50)
        signals = StrategyLab.run('macd', klines)
        
        assert len(signals) == len(klines)
        for signal in signals:
            assert signal['signal'] in ['buy', 'sell', 'hold']
    
    def test_run_kdj(self):
        klines = generate_test_klines(50)
        signals = StrategyLab.run('kdj', klines)
        
        assert len(signals) == len(klines)
        for signal in signals:
            assert signal['signal'] in ['buy', 'sell', 'hold']
    
    def test_run_boll(self):
        klines = generate_test_klines(50)
        signals = StrategyLab.run('boll', klines)
        
        assert len(signals) == len(klines)
        for signal in signals:
            assert signal['signal'] in ['buy', 'sell', 'hold']
    
    def test_run_rsi(self):
        klines = generate_test_klines(50)
        signals = StrategyLab.run('rsi', klines)
        
        assert len(signals) == len(klines)
        for signal in signals:
            assert signal['signal'] in ['buy', 'sell', 'hold']
    
    def test_run_momentum(self):
        klines = generate_test_klines(50)
        signals = StrategyLab.run('momentum', klines)
        
        assert len(signals) == len(klines)
        for signal in signals:
            assert signal['signal'] in ['buy', 'sell', 'hold']
    
    def test_run_mean_reversion(self):
        klines = generate_test_klines(50)
        signals = StrategyLab.run('mean_reversion', klines)
        
        assert len(signals) == len(klines)
        for signal in signals:
            assert signal['signal'] in ['buy', 'sell', 'hold']
    
    def test_run_composite(self):
        klines = generate_test_klines(50)
        signals = StrategyLab.run('composite', klines)
        
        assert len(signals) == len(klines)
        for signal in signals:
            assert signal['signal'] in ['buy', 'sell', 'hold']
    
    def test_compare_strategies(self):
        klines = generate_test_klines(50)
        results = StrategyLab.compare(['dual_ma', 'macd', 'kdj'], klines)
        
        assert len(results) == 3
        assert 'dual_ma' in results
        assert 'macd' in results
        assert 'kdj' in results
    
    def test_unknown_strategy(self):
        klines = generate_test_klines(50)
        
        with pytest.raises(ValueError):
            StrategyLab.run('unknown_strategy', klines)