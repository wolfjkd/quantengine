import pytest
from quantengine.core.signal import SignalEngine


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


class TestSignalEngine:
    def test_analyze(self):
        klines = generate_test_klines(50)
        signal = SignalEngine.analyze('000001', klines)
        
        assert signal is not None
        assert signal.stock_code == '000001'
        assert signal.signal in ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL', 'AVOID']
        assert 0 <= signal.score <= 100
    
    def test_analyze_short_data(self):
        klines = generate_test_klines(10)
        signal = SignalEngine.analyze('000001', klines)
        
        assert signal.signal == 'AVOID'
        assert signal.score == 0
    
    def test_scan(self):
        stocks_data = {
            '000001': generate_test_klines(50),
            '000002': generate_test_klines(50),
            '000003': generate_test_klines(50),
        }
        
        results = SignalEngine.scan(stocks_data)
        
        assert len(results) == 3
        assert results[0].score >= results[-1].score
    
    def test_scan_with_filters(self):
        stocks_data = {
            '000001': generate_test_klines(50),
            '000002': generate_test_klines(50),
            '000003': generate_test_klines(50),
        }
        
        results = SignalEngine.scan(stocks_data, filters={'min_score': 50})
        
        assert len(results) <= 3
        for result in results:
            assert result.score >= 50
    
    def test_trade_plan(self):
        klines = generate_test_klines(50)
        signal = SignalEngine.analyze('000001', klines)
        
        if signal.score >= 40:
            assert signal.trade_plan is not None
            assert signal.trade_plan.entry_price > 0
            assert signal.trade_plan.stop_loss > 0
            assert signal.trade_plan.take_profit > 0
            assert 0 < signal.trade_plan.position_pct <= 1
        else:
            assert signal.trade_plan is None
    
    def test_to_dict(self):
        klines = generate_test_klines(50)
        signal = SignalEngine.analyze('000001', klines)
        
        data = signal.to_dict()
        assert data['stock_code'] == '000001'
        assert data['signal'] == signal.signal
        assert data['score'] == signal.score