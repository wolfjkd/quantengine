import pytest
import tempfile
import os
from quantengine.data.storage import DataStorage
from quantengine.data.loader import DataLoader
from quantengine.data.sync import DataSync


def generate_test_klines(count=20):
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


class TestDataStorage:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.storage = DataStorage(self.db_path)
    
    def teardown_method(self):
        import time
        time.sleep(0.1)
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass
        try:
            os.rmdir(self.temp_dir)
        except:
            pass
    
    def test_init(self):
        assert self.storage is not None
    
    def test_save_and_get_stock_list(self):
        stock_list = [{'code': '000001', 'name': '测试股票'}]
        self.storage.save_stock_list(stock_list)
        
        result = self.storage.get_stock_list()
        assert len(result) == 1
        assert result[0]['code'] == '000001'
    
    def test_save_and_load_kline(self):
        klines = generate_test_klines(20)
        self.storage.save_kline('000001', klines)
        
        result = self.storage.load_kline('000001')
        assert len(result) == 20
    
    def test_append_kline(self):
        klines1 = []
        base_price = 10.0
        for i in range(10):
            base_price *= (1 + (i % 5 - 2) * 0.01)
            klines1.append({
                'date': f'2024-01-{i+1:02d}',
                'open': round(base_price, 2),
                'high': round(base_price * 1.01, 2),
                'low': round(base_price * 0.99, 2),
                'close': round(base_price, 2),
                'volume': 1000000,
                'amount': round(base_price * 1000000, 2),
            })
        
        klines2 = []
        for i in range(10):
            base_price *= (1 + (i % 5 - 2) * 0.01)
            klines2.append({
                'date': f'2024-01-{i+11:02d}',
                'open': round(base_price, 2),
                'high': round(base_price * 1.01, 2),
                'low': round(base_price * 0.99, 2),
                'close': round(base_price, 2),
                'volume': 1000000,
                'amount': round(base_price * 1000000, 2),
            })
        
        self.storage.save_kline('000001', klines1)
        self.storage.append_kline('000001', klines2)
        
        result = self.storage.load_kline('000001')
        assert len(result) == 20
    
    def test_get_last_kline_date(self):
        klines = generate_test_klines(20)
        self.storage.save_kline('000001', klines)
        
        last_date = self.storage.get_last_kline_date('000001')
        assert last_date == '2024-01-20'
    
    def test_count_stocks(self):
        stock_list = [
            {'code': '000001', 'name': '股票1'},
            {'code': '000002', 'name': '股票2'},
        ]
        self.storage.save_stock_list(stock_list)
        
        count = self.storage.count_stocks()
        assert count == 2


class TestDataLoader:
    def test_init(self):
        loader = DataLoader()
        assert loader is not None
    
    def test_load_stock_list(self):
        loader = DataLoader()
        stocks = loader.load_stock_list()
        assert isinstance(stocks, list)
    
    def test_load_kline(self):
        loader = DataLoader()
        klines = loader.load_kline('600519', '2024-01-01', '2024-01-10')
        assert isinstance(klines, list)


class TestDataSync:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.storage = DataStorage(self.db_path)
        self.loader = DataLoader()
        self.sync = DataSync(self.loader, self.storage)
    
    def teardown_method(self):
        import time
        time.sleep(0.1)
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass
        try:
            os.rmdir(self.temp_dir)
        except:
            pass
    
    def test_sync_stock_list(self):
        result = self.sync.sync_stock_list()
        assert 'new' in result
        assert 'deleted' in result
        assert 'total' in result
    
    def test_sync_kline_incremental(self):
        klines = generate_test_klines(20)
        self.storage.save_kline('600519', klines)
        
        result = self.sync.sync_kline('600519', mode='incremental')
        assert 'added' in result