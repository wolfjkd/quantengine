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