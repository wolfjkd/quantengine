# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),

## [0.1.1] - 2026-07-25

### Added - 完成阶段2核心功能
- **回测引擎** (`core/backtest.py`)
  - A股T+1交易规则、涨跌停限制、交易费用计算
  - 8种内置策略：dual_ma / macd / kdj / boll / rsi / momentum / mean_reversion / composite
  - 止损止盈：固定比例 / ATR动态 / 移动止盈
  - 仓位管理：等权分配 / 目标仓位 / 单票上限
  - 基准对比、超额收益计算

- **策略实验室** (`core/strategy.py`)
  - 策略注册机制、参数配置、策略对比

- **信号引擎** (`core/signal.py`)
  - 多指标组合评分（趋势/动量/超买超卖/量能/风险）
  - 5级信号：strong_buy / buy / neutral / sell / strong_sell
  - 批量扫描、按评分排序

- **因子引擎** (`core/factor.py`)
  - 5类22因子：价值/成长/质量/动量/风险
  - Z-Score 标准化、IC分析、加权融合

- **条件选股** (`core/screener.py`)
  - 5类30+条件：基本面/技术面/资金面/风险面/标记
  - AND 逻辑组合、排序输出

- **数据层** (`data/`)
  - `loader.py`: TFH MCP / trader-data-router / AKShare 多数据源
  - `storage.py`: 本地 SQLite 存储
  - `sync.py`: 增量同步、完整性校验

### Tests
- 6个测试文件，57个测试用例全部通过
- 阶段2测试报告：`docs/phase2-report.md`

### Changed
- 依赖 quantcore>=0.1.0（共享算法层）
- 完整的策略注册机制（momentum/mean_reversion/composite）

## [0.1.0] - 2026-07-25

### Added - 初始版本
- 项目骨架搭建
- 核心模块设计：core/ + data/ 双层架构
- pyproject.toml 项目配置
- MIT License
- 初始提交至 GitHub 私有仓库
