import logging
from datetime import date, timedelta


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSync:
    def __init__(self, loader, storage):
        self.loader = loader
        self.storage = storage
    
    def sync_stock_list(self, mode='full'):
        logger.info("Starting stock list sync...")
        
        remote_list = self.loader.load_stock_list()
        local_list = self.storage.get_stock_list()
        
        remote_codes = set(s['code'] for s in remote_list)
        local_codes = set(s['code'] for s in local_list)
        
        new_stocks = remote_codes - local_codes
        del_stocks = local_codes - remote_codes
        
        logger.info(f"New stocks: {len(new_stocks)}, Deleted stocks: {len(del_stocks)}")
        
        self.storage.save_stock_list(remote_list)
        
        assert len(remote_codes) == self.storage.count_stocks(), "Stock list sync failed: count mismatch"
        
        logger.info("Stock list sync completed successfully")
        return {'new': len(new_stocks), 'deleted': len(del_stocks), 'total': len(remote_codes)}
    
    def sync_kline(self, stock_code, mode='incremental'):
        logger.info(f"Syncing kline for {stock_code}, mode: {mode}")
        
        if mode == 'incremental':
            last_date = self.storage.get_last_kline_date(stock_code)
            if last_date:
                start_date = (date.fromisoformat(last_date) + timedelta(days=1)).isoformat()
            else:
                start_date = '2020-01-01'
            
            end_date = date.today().isoformat()
            
            if start_date > end_date:
                logger.info(f"No new data to sync for {stock_code}")
                return {'added': 0}
            
            new_klines = self.loader.load_kline(stock_code, start_date, end_date)
            self.storage.append_kline(stock_code, new_klines)
            
            logger.info(f"Added {len(new_klines)} new klines for {stock_code}")
            
            self._validate_kline_continuity(stock_code)
            
            return {'added': len(new_klines)}
        else:
            all_klines = self.loader.load_kline(stock_code, None, date.today().isoformat())
            self.storage.save_kline(stock_code, all_klines)
            
            logger.info(f"Saved {len(all_klines)} klines for {stock_code}")
            
            self._validate_kline_continuity(stock_code)
            
            return {'added': len(all_klines)}
    
    def sync_all_klines(self, mode='incremental'):
        logger.info("Starting sync for all stocks...")
        
        stock_list = self.storage.get_stock_list()
        results = {}
        
        for stock in stock_list:
            code = stock['code']
            try:
                result = self.sync_kline(code, mode)
                results[code] = result
            except Exception as e:
                logger.error(f"Sync failed for {code}: {e}")
                results[code] = {'error': str(e)}
        
        logger.info(f"Sync completed for {len(results)} stocks")
        return results
    
    def _validate_kline_continuity(self, stock_code):
        klines = self.storage.load_kline(stock_code)
        
        if len(klines) < 2:
            return
        
        dates = [k['date'] for k in klines]
        expected_dates = self._get_expected_trading_dates(dates[0], dates[-1])
        
        missing_dates = expected_dates - set(dates)
        
        if missing_dates:
            logger.warning(f"Missing dates for {stock_code}: {sorted(missing_dates)[:10]}")
    
    def _get_expected_trading_dates(self, start_date, end_date):
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        
        expected = set()
        current = start
        
        while current <= end:
            if current.weekday() < 5:
                expected.add(current.isoformat())
            current += timedelta(days=1)
        
        return expected