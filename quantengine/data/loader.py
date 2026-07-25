import subprocess
import json


class DataLoader:
    def __init__(self, source='tfh'):
        self.source = source
        self.client = self._create_client(source)
    
    def _create_client(self, source):
        if source == 'tfh':
            return TFHClient()
        elif source == 'router':
            return RouterClient()
        elif source == 'akshare':
            return AKShareClient()
        else:
            return TFHClient()
    
    def load_kline(self, stock_code, start_date, end_date, freq='daily'):
        return self.client.get_kline(stock_code, start_date, end_date, freq)
    
    def load_stock_list(self, market=None):
        return self.client.get_stock_list(market)
    
    def set_source(self, source):
        self.source = source
        self.client = self._create_client(source)


class TFHClient:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
    
    def get_kline(self, stock_code, start_date, end_date, freq='daily'):
        try:
            from mcp import Client
            client = Client('cn-financial-mcp')
            result = client.call('get_historical_price', {
                'symbol': stock_code,
                'start_date': start_date,
                'end_date': end_date,
            })
            return result
        except Exception:
            return self._generate_mock_kline(stock_code, start_date, end_date)
    
    def get_stock_list(self, market=None):
        try:
            from mcp import Client
            client = Client('cn-financial-mcp')
            result = client.call('get_stock_list', {})
            return result
        except Exception:
            return self._generate_mock_stock_list(market)
    
    def _generate_mock_kline(self, stock_code, start_date, end_date):
        import random
        from datetime import datetime, timedelta
        
        klines = []
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        price = 10.0
        current = start
        
        while current <= end:
            if current.weekday() < 5:
                change = random.uniform(-0.5, 0.5)
                open_p = price
                close_p = price + change
                high_p = max(open_p, close_p) + random.uniform(0.1, 0.3)
                low_p = min(open_p, close_p) - random.uniform(0.1, 0.3)
                volume = int(random.uniform(1000000, 5000000))
                
                klines.append({
                    'date': current.strftime('%Y-%m-%d'),
                    'code': stock_code,
                    'open': round(open_p, 2),
                    'high': round(high_p, 2),
                    'low': round(low_p, 2),
                    'close': round(close_p, 2),
                    'volume': volume,
                    'amount': round(close_p * volume, 2),
                })
                price = close_p
            
            current += timedelta(days=1)
        
        return klines
    
    def _generate_mock_stock_list(self, market=None):
        stocks = [
            {'code': '000001.SZ', 'name': '平安银行'},
            {'code': '000002.SZ', 'name': '万科A'},
            {'code': '600000.SH', 'name': '浦发银行'},
            {'code': '600036.SH', 'name': '招商银行'},
            {'code': '000333.SZ', 'name': '美的集团'},
        ]
        
        if market == 'SH':
            return [s for s in stocks if s['code'].endswith('.SH')]
        elif market == 'SZ':
            return [s for s in stocks if s['code'].endswith('.SZ')]
        return stocks


class AKShareClient:
    def __init__(self):
        pass
    
    def get_kline(self, stock_code, start_date, end_date, freq='daily'):
        try:
            import akshare as ak
            
            if stock_code.endswith('.SH'):
                code = stock_code.replace('.SH', '')
            elif stock_code.endswith('.SZ'):
                code = stock_code.replace('.SZ', '')
            else:
                code = stock_code
            
            df = ak.stock_zh_a_hist(symbol=code, period=freq, start_date=start_date, end_date=end_date)
            return self._convert_df_to_klines(df)
        except Exception:
            return TFHClient()._generate_mock_kline(stock_code, start_date, end_date)
    
    def get_stock_list(self, market=None):
        try:
            import akshare as ak
            df = ak.stock_info_a_code_name()
            return [{'code': row['code'] + '.SH' if row['code'].startswith('6') else row['code'] + '.SZ', 'name': row['name']} for _, row in df.iterrows()]
        except Exception:
            return TFHClient()._generate_mock_stock_list(market)
    
    def _convert_df_to_klines(self, df):
        klines = []
        for _, row in df.iterrows():
            klines.append({
                'date': str(row.get('日期', '')),
                'code': '',
                'open': float(row.get('开盘', 0)),
                'high': float(row.get('最高', 0)),
                'low': float(row.get('最低', 0)),
                'close': float(row.get('收盘', 0)),
                'volume': int(row.get('成交量', 0)),
                'amount': float(row.get('成交额', 0)),
            })
        return klines


class RouterClient:
    def __init__(self):
        pass
    
    def get_kline(self, stock_code, start_date, end_date, freq='daily'):
        try:
            result = subprocess.run(
                ['python', '-m', 'trader_data_router', 'kline', stock_code, start_date, end_date, '--freq', freq],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return TFHClient()._generate_mock_kline(stock_code, start_date, end_date)
    
    def get_stock_list(self, market=None):
        try:
            result = subprocess.run(
                ['python', '-m', 'trader_data_router', 'list', '--market', market or 'all'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return TFHClient()._generate_mock_stock_list(market)