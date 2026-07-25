# QuantEngine

<p align="center">
  <strong>量化研究引擎 · 回测 / 策略 / 因子 / 信号 一体化引擎</strong><br/>
  Python ≥3.10 · 依赖 quantcore · MIT License
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python"/>
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"/>
  <img src="https://img.shields.io/badge/Version-0.1.1-orange.svg" alt="Version"/>
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

```python
from quantengine import BacktestEngine, StrategyLab, SignalEngine

# 1. 策略回测
engine = BacktestEngine()
result = engine.run(
    strategy='dual_ma',
    stock_codes=['000001', '600519'],
    start_date='2023-01-01',
    end_date='2024-01-01',
    initial_cash=1_000_000,
    params={'fast_period': 5, 'slow_period': 20}
)
print(f'总收益: {result.metrics.total_return:.2%}')
print(f'夏普比率: {result.metrics.sharpe_ratio:.4f}')

# 2. 信号扫描
signal_engine = SignalEngine()
signals = signal_engine.scan(stocks_data, min_score=60)
for s in signals:
    print(f'{s.code}: {s.signal} (score={s.score})')
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
| v0.1.1 | 2026-07-25 | 完成阶段2：回测引擎 + 策略实验室 + 信号/因子/选股 |
| v0.1.0 | 2026-07-25 | 初始版本：项目骨架 + 核心模块设计 |

## License

MIT License © 2026 [wolfjkd](https://github.com/wolfjkd)
