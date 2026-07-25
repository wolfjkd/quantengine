# QuantEngine

<p align="center">
  <strong>量化研究引擎 · 回测 / 策略 / 因子 / 信号 一体化引擎</strong><br/>
  Python ≥3.10 · 依赖 quantcore · MIT License
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python"/>
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"/>
  <img src="https://img.shields.io/badge/Version-0.1.2-orange.svg" alt="Version"/>
</p>

---

## 项目定位

QuantEngine 是独立的量化研究引擎层，提供完整的回测、策略、因子、信号能力。
基于 [QuantCore](https://github.com/wolfjkd/quantcore) 算法层，对接 [Trader Finance Hub](https://github.com/wolfjkd/trader-finance-hub) 数据层。

**架构关系**：
```
Trader Finance Hub (数据层, MCP)  ←─数据接口─  QuantEngine
       ↓                                            ↓
   AI Agent 调用                              QuantTerminal (应用层)
                                                  ↓
                                            QuantCore (算法层)
```

## 核心模块

| 模块 | 文件 | 功能 |
|------|------|------|
| **回测引擎** | `core/backtest.py` | A股T+1回测，8种策略，止损止盈，基准对比 |
| **策略实验室** | `core/strategy.py` | 策略注册/运行/对比/参数寻优 |
| **信号引擎** | `core/signal.py` | 多指标组合信号，5级评分，批量扫描 |
| **因子引擎** | `core/factor.py` | 多因子综合评分，IC分析，因子库管理 |
| **条件选股** | `core/screener.py` | 多维度条件组合筛选 |
| **数据层** | `data/` | TFH/AKShare/Router 多数据源接入 |

## 安装

```bash
# 本地开发安装
pip install -e .

# 依赖
pip install quantcore>=0.1.0 numpy>=1.24 SQLAlchemy>=2.0
```

## 快速使用

### 1. 策略回测

```python
from quantengine import BacktestEngine

# 准备 K 线数据：list[dict]，每根 K 线包含 date/open/high/low/close/volume
# 多数策略需要至少 slow_period(默认 20) 根 K 线才能产生信号
klines = [
    {'date': '2024-01-01', 'open': 10.0, 'high': 10.2, 'low': 9.8, 'close': 10.0, 'volume': 1000000},
    {'date': '2024-01-02', 'open': 10.1, 'high': 10.3, 'low': 9.9, 'close': 10.1, 'volume': 1100000},
    # ... 至少 20 根 K 线
]

# BacktestEngine(initial_cash, settings) → engine.run(strategy, klines, params)
engine = BacktestEngine(initial_cash=1_000_000)
result = engine.run(
    strategy='dual_ma',
    klines=klines,
    params={'fast_period': 5, 'slow_period': 20}
)

# result.metrics 是 dict（不是属性访问）
m = result.metrics
print(f"总收益: {m['total_return']:.2%}")
print(f"夏普比率: {m['sharpe_ratio']:.4f}")
print(f"最大回撤: {m['max_drawdown']:.2%}")
print(f"交易次数: {m['num_trades']}")

# result.summary() 返回已格式化的字符串 dict
print(result.summary())
```

### 2. 信号扫描

```python
from quantengine import SignalEngine

# stocks_data: dict[stock_code -> list[kline]]
stocks_data = {
    '000001': klines,
    '600519': klines,
}

# SignalEngine.scan 是类方法，min_score 通过 filters 传入
signals = SignalEngine.scan(
    stocks_data,
    filters={'min_score': 60, 'signal': ['buy', 'strong_buy']}
)

# 返回已按 score 降序排序的 TradingSignal 列表
for s in signals:
    print(f"{s.stock_code}: {s.signal} (score={s.score})")  # 字段是 stock_code，不是 code
    if s.trade_plan:
        plan = s.trade_plan
        print(f"  入场={plan.entry_price} 止损={plan.stop_loss} 止盈={plan.take_profit}")
```

### 3. 8 种内置策略示例

```python
from quantengine import BacktestEngine

engine = BacktestEngine(initial_cash=1_000_000)
klines = [...]  # 你的 K 线数据（list[dict]）

# 趋势类
engine.run('dual_ma', klines, params={'fast_period': 5, 'slow_period': 20})      # 双均线交叉
engine.run('macd', klines, params={'fast_period': 12, 'slow_period': 26, 'signal_period': 9})  # MACD 金叉
engine.run('boll', klines, params={'period': 20, 'num_std': 2})                   # 布林带突破

# 动量类
engine.run('momentum', klines, params={'period': 20})                             # 动量策略

# 震荡类
engine.run('kdj', klines, params={'n': 9, 'm1': 3, 'm2': 3})                      # KDJ 超买超卖
engine.run('rsi', klines, params={'period': 14, 'oversold': 30, 'overbought': 70})  # RSI 反弹

# 均值回归类
engine.run('mean_reversion', klines, params={'period': 20, 'threshold': 0.1})     # 均值乖离

# 综合评分（多维度打分）
engine.run('composite', klines, params={})

# 自定义目标仓位（覆盖默认等权分配，0.15 = 15%）
engine.run('dual_ma', klines, params={'fast_period': 5, 'slow_period': 20, 'target_weight': 0.15})
```

### 4. A 股特色规则配置

```python
from quantengine import BacktestEngine

engine = BacktestEngine(
    initial_cash=1_000_000,
    settings={
        'max_weight': 0.2,          # 单票仓位上限 20%
        'max_positions': 10,         # 最大持仓股票数 10
        'stop_loss': 0.05,           # 止损比例 5%
        'take_profit': 0.10,         # 止盈比例 10%
        'commission_rate': 0.00025,  # 佣金万 2.5
        'min_commission': 5.0,       # 单笔最低佣金 5 元
        'stamp_tax_rate': 0.0005,    # 印花税千 0.5（仅卖出）
        'slippage_bps': 10,          # 滑点 10bps
    }
)

# 引擎内置 A 股交易规则：
# - T+1：买入当日 frozen=True，下一个交易日解冻才能卖出
# - 涨跌停限制（按股票代码前缀自动判断）：
#   * ST/*ST 股票：5%（需在 kline 传 name 或 is_st 字段）
#   * 创业板 300/301、科创板 688：20%
#   * 其他普通股票：10%
#   * 涨停 → 跳过买入；跌停 → 跳过卖出
# - 仓位管理：等权分配（total_equity / max_positions），且单票不超过 max_weight * total_equity
```

## A股特色规则

| 规则 | 实现 |
|------|------|
| **T+1交易** | 买入当日冻结，次日可卖 |
| **涨跌停限制** | ST 5% / 普通 10% / 创业板科创板 20% |
| **交易费用** | 佣金万2.5（最低5元）+ 印花税千0.5（仅卖出）+ 滑点 |
| **仓位管理** | 等权分配、目标仓位、单票上限、最大持仓数 |
| **止损止盈** | 固定比例 / ATR动态 / 移动止盈 |

## 内置策略

| 策略 | 代码 | 类型 |
|------|------|------|
| 双均线交叉 | `dual_ma` | 趋势 |
| MACD金叉 | `macd` | 动量 |
| KDJ超买超卖 | `kdj` | 震荡 |
| 布林带突破 | `boll` | 趋势 |
| RSI反弹 | `rsi` | 均值回归 |
| 动量策略 | `momentum` | 动量 |
| 均值回归 | `mean_reversion` | 均值回归 |
| 综合评分 | `composite` | 多维度 |

## 项目结构

```
quantengine/
├── quantengine/
│   ├── __init__.py
│   ├── __version__.py
│   ├── core/                  # 核心引擎
│   │   ├── backtest.py        # 回测引擎
│   │   ├── strategy.py        # 策略实验室
│   │   ├── signal.py          # 信号引擎
│   │   ├── factor.py          # 因子引擎
│   │   ├── screener.py        # 条件选股
│   │   ├── indicators.py      # 技术指标（包装 quantcore）
│   │   ├── metrics.py         # 绩效指标
│   │   └── money.py           # 资金计算
│   └── data/                  # 数据层
│       ├── loader.py          # 数据加载器（TFH/Router/AKShare）
│       ├── storage.py         # 本地存储
│       └── sync.py            # 数据同步
├── tests/
│   ├── test_backtest.py
│   ├── test_strategy.py
│   ├── test_signal.py
│   ├── test_factor.py
│   ├── test_screener.py
│   └── test_data.py
├── docs/
│   └── phase2-report.md       # 阶段2测试报告
├── pyproject.toml
├── requirements.txt
└── LICENSE
```

## 性能基准

| 场景 | 数据量 | 平均耗时 |
|------|--------|---------|
| 单票回测（1年） | 250根K线 | < 100ms |
| 单票回测（5年） | 1250根K线 | < 400ms |
| 多票回测（10只） | 2500根K线 | < 1s |
| 信号扫描（全市场） | 5000只 | < 30s |

## 版本历史

详见 [CHANGELOG.md](CHANGELOG.md)

| 版本 | 发布日期 | 主要变更 |
|------|---------|---------|
| v0.1.2 | 2026-07-26 | 修复：补齐22因子+43条件、T+1真正生效、涨跌停三档、信号小写命名、仓位管理落地、补打 v0.1.0 tag |
| v0.1.1 | 2026-07-25 | 完成阶段2：回测引擎 + 策略实验室 + 信号/因子/选股 |
| v0.1.0 | 2026-07-25 | 初始版本：项目骨架 + 核心模块设计 |

## License

MIT License © 2026 [wolfjkd](https://github.com/wolfjkd)
