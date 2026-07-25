from quantcore.metrics import (
    total_return, annualized_return, volatility, downside_volatility,
    sharpe_ratio, sortino_ratio, max_drawdown, calmar_ratio,
    win_rate, profit_factor, expected_return
)


class Metrics:
    @classmethod
    def calculate(cls, equity_curve, trades=None, options=None):
        options = options or {}
        risk_free_rate = options.get('risk_free_rate', 0.03)
        
        return {
            'total_return': total_return(equity_curve),
            'annualized_return': annualized_return(equity_curve),
            'volatility': volatility(equity_curve),
            'downside_volatility': downside_volatility(equity_curve),
            'sharpe_ratio': sharpe_ratio(equity_curve, risk_free_rate),
            'sortino_ratio': sortino_ratio(equity_curve, risk_free_rate),
            'max_drawdown': max_drawdown(equity_curve),
            'calmar_ratio': calmar_ratio(equity_curve),
            'win_rate': win_rate(trades or []),
            'profit_factor': profit_factor(trades or []),
            'expected_return': expected_return(trades or []),
            'num_trades': len(trades) if trades else 0,
        }
    
    @classmethod
    def self_check(cls):
        test_curve = [100, 105, 108, 112, 115, 120, 125, 130, 135, 140]
        test_trades = [
            {'profit': 100}, {'profit': 200}, {'profit': 150},
            {'profit': -50}, {'profit': -80}
        ]
        
        metrics = cls.calculate(test_curve, test_trades)
        
        assert metrics['total_return'] > 0
        assert metrics['annualized_return'] > 0
        assert metrics['sharpe_ratio'] > 0
        assert metrics['max_drawdown'] >= 0
        assert metrics['win_rate'] >= 0
        assert metrics['profit_factor'] > 0
        
        return True