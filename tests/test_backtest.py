import pytest
from quantengine.core.backtest import BacktestEngine


def generate_test_klines(count=100):
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


class TestBacktestEngine:
    def test_init(self):
        engine = BacktestEngine(initial_cash=1000000)
        assert engine.cash == 1000000
        assert engine.positions == {}
        assert len(engine.equity_curve) == 0
    
    def test_run_dual_ma(self):
        klines = generate_test_klines(50)
        engine = BacktestEngine(initial_cash=1000000)
        result = engine.run('dual_ma', klines)
        
        assert result is not None
        assert len(result.equity_curve) == len(klines)
        assert result.metrics['total_return'] >= -1
    
    def test_run_macd(self):
        klines = generate_test_klines(50)
        engine = BacktestEngine(initial_cash=1000000)
        result = engine.run('macd', klines)
        
        assert result is not None
        assert len(result.equity_curve) == len(klines)
    
    def test_run_kdj(self):
        klines = generate_test_klines(50)
        engine = BacktestEngine(initial_cash=1000000)
        result = engine.run('kdj', klines)
        
        assert result is not None
        assert len(result.equity_curve) == len(klines)
    
    def test_run_boll(self):
        klines = generate_test_klines(50)
        engine = BacktestEngine(initial_cash=1000000)
        result = engine.run('boll', klines)
        
        assert result is not None
        assert len(result.equity_curve) == len(klines)
    
    def test_run_rsi(self):
        klines = generate_test_klines(50)
        engine = BacktestEngine(initial_cash=1000000)
        result = engine.run('rsi', klines)
        
        assert result is not None
        assert len(result.equity_curve) == len(klines)
    
    def test_run_momentum(self):
        klines = generate_test_klines(50)
        engine = BacktestEngine(initial_cash=1000000)
        result = engine.run('momentum', klines)
        
        assert result is not None
        assert len(result.equity_curve) == len(klines)
    
    def test_run_mean_reversion(self):
        klines = generate_test_klines(50)
        engine = BacktestEngine(initial_cash=1000000)
        result = engine.run('mean_reversion', klines)
        
        assert result is not None
        assert len(result.equity_curve) == len(klines)
    
    def test_run_composite(self):
        klines = generate_test_klines(50)
        engine = BacktestEngine(initial_cash=1000000)
        result = engine.run('composite', klines)
        
        assert result is not None
        assert len(result.equity_curve) == len(klines)
    
    def test_commission_calculation(self):
        klines = generate_test_klines(30)
        engine = BacktestEngine(initial_cash=30000)
        result = engine.run('dual_ma', klines)
        
        assert result is not None
        assert len(result.equity_curve) == len(klines)
    
    def test_slippage(self):
        klines = generate_test_klines(30)
        engine = BacktestEngine(initial_cash=1000000, settings={'slippage': 0.001})
        result = engine.run('dual_ma', klines)
        
        assert result is not None
    
    def test_stop_loss(self):
        klines = generate_test_klines(30)
        engine = BacktestEngine(initial_cash=1000000, settings={'stop_loss': 0.05})
        result = engine.run('dual_ma', klines)
        
        assert result is not None
    
    def test_take_profit(self):
        klines = generate_test_klines(30)
        engine = BacktestEngine(initial_cash=1000000, settings={'take_profit': 0.10})
        result = engine.run('dual_ma', klines)
        
        assert result is not None
    
    def test_unknown_strategy(self):
        klines = generate_test_klines(30)
        engine = BacktestEngine(initial_cash=1000000)
        
        with pytest.raises(ValueError):
            engine.run('unknown_strategy', klines)