import sqlite3
import os
from datetime import datetime


class DataStorage:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.path.join(os.path.expanduser('~'), '.quantengine', 'data.db')
        self._ensure_db_dir()
        self._init_schema()
    
    def _ensure_db_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _init_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(16) NOT NULL UNIQUE,
                    name VARCHAR(64) NOT NULL DEFAULT '',
                    market VARCHAR(8) NOT NULL DEFAULT 'SZ',
                    board VARCHAR(16) NOT NULL DEFAULT 'main',
                    industry VARCHAR(64) DEFAULT '',
                    list_date DATE DEFAULT NULL,
                    is_st INTEGER NOT NULL DEFAULT 0,
                    status INTEGER NOT NULL DEFAULT 1,
                    remark VARCHAR(255) DEFAULT '',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_bars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_id INTEGER NOT NULL,
                    trade_date DATE NOT NULL,
                    open DECIMAL(16,4) NOT NULL,
                    high DECIMAL(16,4) NOT NULL,
                    low DECIMAL(16,4) NOT NULL,
                    close DECIMAL(16,4) NOT NULL,
                    volume BIGINT NOT NULL DEFAULT 0,
                    amount DECIMAL(18,4) NOT NULL DEFAULT 0.0000,
                    pre_close DECIMAL(16,4) DEFAULT NULL,
                    adj_factor DECIMAL(16,6) NOT NULL DEFAULT 1.000000,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stock_id, trade_date),
                    FOREIGN KEY(stock_id) REFERENCES stocks(id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_daily_bars_stock_id ON daily_bars(stock_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_daily_bars_date ON daily_bars(trade_date)
            ''')
            
            conn.commit()
    
    def save_stock_list(self, stocks):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for stock in stocks:
                code = stock.get('code', '')
                name = stock.get('name', '')
                market = stock.get('market', 'SZ')
                
                if code.endswith('.SH'):
                    market = 'SH'
                elif code.endswith('.SZ'):
                    market = 'SZ'
                
                cursor.execute('''
                    INSERT OR REPLACE INTO stocks (code, name, market, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (code, name, market))
            
            conn.commit()
    
    def get_stock_list(self, market=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if market:
                cursor.execute('SELECT * FROM stocks WHERE market = ?', (market,))
            else:
                cursor.execute('SELECT * FROM stocks')
            
            return [{'id': row[0], 'code': row[1], 'name': row[2], 'market': row[3]} for row in cursor.fetchall()]
    
    def get_stock_id(self, code):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM stocks WHERE code = ?', (code,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def save_kline(self, stock_code, klines):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stock_id = self.get_stock_id(stock_code)
            if stock_id is None:
                cursor.execute('''
                    INSERT INTO stocks (code, name, market) VALUES (?, ?, ?)
                ''', (stock_code, '', stock_code[-2:] if stock_code.endswith(('.SH', '.SZ')) else 'SZ'))
                conn.commit()
                stock_id = cursor.lastrowid
            
            for kline in klines:
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_bars (
                        stock_id, trade_date, open, high, low, close, volume, amount
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stock_id,
                    kline.get('date', ''),
                    kline.get('open', 0),
                    kline.get('high', 0),
                    kline.get('low', 0),
                    kline.get('close', 0),
                    kline.get('volume', 0),
                    kline.get('amount', 0),
                ))
            
            conn.commit()
    
    def load_kline(self, stock_code, start_date=None, end_date=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stock_id = self.get_stock_id(stock_code)
            if stock_id is None:
                return []
            
            query = 'SELECT trade_date, open, high, low, close, volume, amount FROM daily_bars WHERE stock_id = ?'
            params = [stock_id]
            
            if start_date:
                query += ' AND trade_date >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND trade_date <= ?'
                params.append(end_date)
            
            query += ' ORDER BY trade_date ASC'
            
            cursor.execute(query, params)
            
            return [{
                'date': row[0],
                'open': float(row[1]),
                'high': float(row[2]),
                'low': float(row[3]),
                'close': float(row[4]),
                'volume': int(row[5]),
                'amount': float(row[6]),
                'code': stock_code,
            } for row in cursor.fetchall()]
    
    def get_last_kline_date(self, stock_code):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stock_id = self.get_stock_id(stock_code)
            if stock_id is None:
                return None
            
            cursor.execute('SELECT MAX(trade_date) FROM daily_bars WHERE stock_id = ?', (stock_id,))
            result = cursor.fetchone()
            return result[0] if result and result[0] else None
    
    def count_stocks(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM stocks')
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def append_kline(self, stock_code, klines):
        self.save_kline(stock_code, klines)
    
    def health_check(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM stocks')
                stock_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM daily_bars')
                bar_count = cursor.fetchone()[0]
                
                return {
                    'status': 'healthy',
                    'stock_count': stock_count,
                    'bar_count': bar_count,
                    'last_updated': datetime.now().isoformat(),
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
            }