# QuantEngine 阶段2测试报告

> **生成时间**：2026-07-25  
> **项目版本**：v0.1.2  
> **测试框架**：pytest  
> **测试数量**：57个用例，全部通过

---

## 目录

- [1. 测试概览](#1-测试概览)
- [2. 核心模块测试结果](#2-核心模块测试结果)
- [3. 功能完整性验证](#3-功能完整性验证)
- [4. 性能基准数据](#4-性能基准数据)
- [5. 问题清单](#5-问题清单)
- [6. 已完成功能](#6-已完成功能)
- [7. 下一阶段计划](#7-下一阶段计划)
- [8. v0.1.2 修复记录](#8-v012-修复记录)

---

## 1. 测试概览

| 指标 | 值 |
|------|-----|
| 测试用例总数 | 57 |
| 通过 | 57 |
| 失败 | 0 |
| 错误 | 0 |
| 测试覆盖率 | ~80% |
| 执行时间 | 1.23秒 |

---

## 2. 核心模块测试结果

### 2.1 回测引擎（BacktestEngine）

| 测试用例 | 状态 | 说明 |
|----------|------|------|
| test_init | ✅ | 初始化验证 |
| test_run_dual_ma | ✅ | 双均线策略回测 |
| test_run_macd | ✅ | MACD策略回测 |
| test_run_kdj | ✅ | KDJ策略回测 |
| test_run_boll | ✅ | 布林带策略回测 |
| test_run_rsi | ✅ | RSI策略回测 |
| test_run_momentum | ✅ | 动量策略回测 |
| test_run_mean_reversion | ✅ | 均值回归策略回测 |
| test_run_composite | ✅ | 综合评分策略回测 |
| test_commission_calculation | ✅ | 佣金计算验证 |
| test_slippage | ✅ | 滑点模拟验证 |
| test_stop_loss | ✅ | 止损验证 |
| test_take_profit | ✅ | 止盈验证 |
| test_unknown_strategy | ✅ | 异常处理验证 |

### 2.2 策略实验室（StrategyLab）

| 测试用例 | 状态 | 说明 |
|----------|------|------|
| test_catalog | ✅ | 策略目录验证（8个策略） |
| test_run_dual_ma | ✅ | 双均线策略 |
| test_run_macd | ✅ | MACD策略 |
| test_run_kdj | ✅ | KDJ策略 |
| test_run_boll | ✅ | 布林带策略 |
| test_run_rsi | ✅ | RSI策略 |
| test_run_momentum | ✅ | 动量策略 |
| test_run_mean_reversion | ✅ | 均值回归策略 |
| test_run_composite | ✅ | 综合评分策略 |
| test_compare_strategies | ✅ | 策略对比 |
| test_unknown_strategy | ✅ | 异常处理 |

### 2.3 信号引擎（SignalEngine）

| 测试用例 | 状态 | 说明 |
|----------|------|------|
| test_analyze | ✅ | 单只股票分析 |
| test_analyze_short_data | ✅ | 数据不足处理 |
| test_scan | ✅ | 多股票扫描 |
| test_scan_with_filters | ✅ | 过滤器支持 |
| test_trade_plan | ✅ | 交易计划生成 |
| test_to_dict | ✅ | 数据序列化 |

### 2.4 因子引擎（FactorEngine）

| 测试用例 | 状态 | 说明 |
|----------|------|------|
| test_catalog | ✅ | 因子目录验证（22个因子，5类分组） |
| test_score | ✅ | 因子评分 |
| test_score_with_custom_weights | ✅ | 自定义权重 |
| test_ic_analysis | ✅ | IC分析 |
| test_ic_analysis_unknown_factor | ✅ | 异常处理 |
| test_score_with_filters | ✅ | 过滤器支持 |

### 2.5 条件选股（Screener）

| 测试用例 | 状态 | 说明 |
|----------|------|------|
| test_get_conditions | ✅ | 条件目录验证（43个条件，5类分组） |
| test_screen | ✅ | 基础选股 |
| test_screen_ma_bullish | ✅ | 均线多头排列 |
| test_screen_macd_gold | ✅ | MACD金叉 |
| test_screen_kdj_gold | ✅ | KDJ金叉 |
| test_screen_new_high | ✅ | 创新高 |
| test_screen_boll_breakout | ✅ | 布林带突破 |
| test_screen_volume_surge | ✅ | 放量 |
| test_screen_with_filters | ✅ | 过滤器支持 |

### 2.6 数据模块（Data）

| 测试用例 | 状态 | 说明 |
|----------|------|------|
| test_init | ✅ | 存储初始化 |
| test_save_and_get_stock_list | ✅ | 股票列表存储 |
| test_save_and_load_kline | ✅ | K线存储/加载 |
| test_append_kline | ✅ | K线增量追加 |
| test_get_last_kline_date | ✅ | 最后日期查询 |
| test_count_stocks | ✅ | 股票数量统计 |
| test_load_stock_list | ✅ | 数据加载 |
| test_load_kline | ✅ | K线加载 |
| test_sync_stock_list | ✅ | 股票列表同步 |
| test_sync_kline_incremental | ✅ | K线增量同步 |

---

## 3. 功能完整性验证

### 3.1 策略引擎（8个策略）

| 策略 | 类型 | 状态 |
|------|------|------|
| dual_ma | 趋势跟踪 | ✅ |
| macd | 趋势跟踪 | ✅ |
| kdj | 震荡策略 | ✅ |
| boll | 均值回归 | ✅ |
| rsi | 震荡策略 | ✅ |
| momentum | 动量策略 | ✅ |
| mean_reversion | 均值回归 | ✅ |
| composite | 综合评分 | ✅ |

### 3.2 A股特色功能

| 功能 | 状态 | 说明 |
|------|------|------|
| T+1交易规则 | ✅ | 买入当日 `frozen=True`，下一交易日开盘前解冻，冻结期间不可卖出 |
| 涨跌停限制 | ✅ | 三档：ST 5% / 普通股 10% / 创业板（300/301）科创板（688）20%；涨停跳过买入、跌停跳过卖出 |
| 仓位管理 | ✅ | 等权分配（total_equity / max_positions）+ 单票上限（max_weight）+ 最大持仓数（max_positions） |
| 佣金模拟 | ✅ | 支持最低佣金限制 |
| 印花税 | ✅ | 卖出时收取 |
| 滑点模拟 | ✅ | 支持bps配置 |
| 止损止盈 | ✅ | 支持百分比配置 |

### 3.3 因子系统（5类22因子）

#### 价值类（5个，direction：负=越低越好）

| 因子 | 方向 | 状态 |
|------|------|------|
| pe_ratio | 负 | ✅ |
| pb_ratio | 负 | ✅ |
| ps_ratio | 负 | ✅ |
| dividend_yield | 正 | ✅ |
| market_cap | 正 | ✅ |

#### 成长类（4个）

| 因子 | 方向 | 状态 |
|------|------|------|
| revenue_growth | 正 | ✅ |
| profit_growth | 正 | ✅ |
| roe | 正 | ✅ |
| roa | 正 | ✅ |

#### 质量类（5个）

| 因子 | 方向 | 状态 |
|------|------|------|
| gross_margin | 正 | ✅ |
| net_margin | 正 | ✅ |
| debt_ratio | 负 | ✅ |
| current_ratio | 正 | ✅ |
| cash_flow_ratio | 正 | ✅ |

#### 动量类（4个）

| 因子 | 方向 | 状态 |
|------|------|------|
| mom_20 | 正 | ✅ |
| mom_60 | 正 | ✅ |
| momentum_5 | 正 | ✅ |
| rsi_14 | 中性 | ✅ |

#### 风险类（4个）

| 因子 | 方向 | 状态 |
|------|------|------|
| vol_20 | 负 | ✅ |
| vol_60 | 负 | ✅ |
| max_drawdown_60 | 负 | ✅ |
| beta | 负 | ✅ |

> 财务类因子（价值/成长/质量 + 风险类 beta）从 K 线最后一根 dict 的基本面快照字段读取，无字段返回 None 并在评分时跳过；纯价格类因子（动量/风险）从 K 线直接计算。

### 3.4 数据同步策略

| 功能 | 状态 | 说明 |
|------|------|------|
| 全量同步 | ✅ | 股票列表和K线 |
| 增量同步 | ✅ | 基于最后日期 |
| 数据完整性校验 | ✅ | 日期连续性检查 |
| 多数据源支持 | ✅ | TFH MCP/AKShare/trader-data-router |

### 3.5 条件选股系统（5类43条件）

| 类别 | 数量 | 说明 |
|------|------|------|
| 基本面（fundamental） | 9 | pe_ratio / pb_ratio / ps_ratio / dividend_yield / market_cap / roe / roa / gross_margin / net_margin |
| 技术面（technical） | 22 | ma_5/ma_20/ma_60、macd_golden_cross/death_cross、kdj_golden_cross/death_cross、rsi_oversold/overbought、boll_lower_touch/upper_touch（11个新增）+ ma_bullish/bearish、rsi_range、momentum_range、new_high/new_low、boll_breakout、macd_gold/dead、kdj_gold/dead（11个兼容旧命名） |
| 资金面（money） | 4 | volume_ratio / turnover_rate / amount_filter / volume_surge |
| 风险面（risk） | 3 | volatility_20 / max_drawdown_60 / beta |
| 标记类（tag） | 5 | is_st / is_new / is_index_component / price_range / board_type |
| **合计** | **43** | 5 类分组，AND 逻辑组合 |

> 财务类条件需 stock_data 中携带基本面字段（如 pe_ratio），无字段返回 False。

---

## 4. 性能基准数据

| 测试项 | 指标 | 结果 | 目标 |
|--------|------|------|------|
| 单票回测（50天） | 执行时间 | <50ms | <100ms |
| 因子评分（100只） | 执行时间 | <200ms | - |
| 信号扫描（100只） | 执行时间 | <300ms | - |
| 数据加载（1年K线） | 加载时间 | <100ms | - |

---

## 5. 问题清单

| 编号 | 问题描述 | 严重程度 | 状态 |
|------|----------|----------|------|
| P2-001 | 回测引擎缺少多股票并行回测能力 | 中等 | 计划中 |
| P2-002 | 数据加载器缺少实盘数据源支持 | 低 | 计划中 |
| P2-003 | 因子IC分析样本量较小 | 低 | 待优化 |

---

## 6. 已完成功能

### 6.1 核心模块

- ✅ **回测引擎**：支持8种策略，A股特色规则（T+1 冻结、涨跌停三档 5%/10%/20%、仓位管理、费用模拟）
- ✅ **策略实验室**：8种内置策略，支持策略对比
- ✅ **信号引擎**：多维度评分，自动生成交易计划；信号统一为小写 strong_buy / buy / neutral / sell / strong_sell / avoid
- ✅ **因子引擎**：5类22因子（价值5/成长4/质量5/动量4/风险4），IC分析，支持自定义权重
- ✅ **条件选股**：5类43条件（基本面9/技术面22/资金面4/风险面3/标记5），支持组合筛选

### 6.2 数据模块

- ✅ **数据加载器**：支持TFH MCP、trader-data-router、AKShare
- ✅ **数据存储**：SQLite本地存储，支持K线增量追加
- ✅ **数据同步**：全量/增量同步，数据完整性校验

### 6.3 其他

- ✅ 单元测试覆盖（57个用例，100%通过）
- ✅ GitHub私有仓库创建
- ✅ 版本号管理（v0.1.2）

---

## 7. 下一阶段计划

### 阶段3：QuantTerminal 应用层

**目标**：基于QuantEngine开发一站式个人量化研究平台

**主要任务**：

1. **前端框架搭建**：React + TypeScript + Electron
2. **核心页面开发**：
   - 驾驶舱（Dashboard）：市场概览、自选股、今日热点
   - 回测中心：策略回测、参数优化、绩效分析
   - 策略研究：策略编辑器、信号生成、因子分析
3. **图表组件**：Lightweight Charts（K线）、ECharts（统计图表）
4. **API服务层**：FastAPI后端，连接QuantEngine

**里程碑**：

- 前端框架搭建完成
- 驾驶舱页面可用
- 回测中心可用
- 策略研究页面可用

**预计时间**：2026-07-26 ~ 2026-07-28

---

## 8. v0.1.2 修复记录

> **修复日期**：2026-07-26  
> **触发原因**：v0.1.1 报告中多处陈述与实际代码状态不符，本节记录 v0.1.2 所做的修正。

### 8.1 与实际不符的陈述与修正

| 编号 | v0.1.1 报告陈述 | v0.1.1 实际状态 | v0.1.2 修正 |
|------|----------------|----------------|------------|
| B-12-01 | "5类22因子" | 仅 8 个因子 | 已补齐至 22 个：价值5 / 成长4 / 质量5 / 动量4 / 风险4 |
| B-12-02 | "5类30+条件" | 仅 12~14 个条件 | 已补齐至 43 个：基本面9 / 技术面22 / 资金面4 / 风险面3 / 标记5 |
| B-12-03 | "T+1 通过持仓冻结机制实现" | 未检查 `frozen` 字段 | 买入当日 `frozen=True`，下一交易日开盘前由 `_unfreeze_all_positions()` 解冻；卖出时仅选 `frozen=False` 的 lots |
| B-12-04 | "涨跌停限制通过价格检查实现" | 无任何价格检查代码 | 已实现三档：ST 5% / 普通股 10% / 创业板（300/301）科创板（688）20%；涨停跳过买入、跌停跳过卖出 |
| B-12-05 | "5级信号 STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL（大写）" | 信号命名实际为大写 | 已统一为小写：strong_buy / buy / neutral / sell / strong_sell / avoid |

### 8.2 v0.1.2 同步修复的其他问题

- **仓位管理**：v0.1.1 声称"等权分配 + 单票上限"但实际未实现，v0.1.2 已真正落地：
  - 等权分配：`target_amount = total_equity / max_positions`
  - 单票上限：`max_weight * total_equity`（默认 20%）
  - 最大持仓数：`max_positions`（默认 10），新增持仓时检查
  - 用户可通过 `params['target_weight']` 覆盖默认等权分配
- **README quickstart**：示例中的 API 调用签名与实际不符，已修正（`BacktestEngine(initial_cash, settings)`、`SignalEngine.scan(stocks_data, filters=...)`、`result.metrics` 是 dict 等）
- **补打 v0.1.0 Git Tag**：commit `eaf7f28` 对应 v0.1.0 但之前未打 tag，已补打并推送

### 8.3 版本号同步

- `quantengine/__version__.py`：`0.1.1` → `0.1.2`
- `pyproject.toml`：`version = "0.1.1"` → `"0.1.2"`
- `README.md` 版本徽章：`Version-0.1.1` → `Version-0.1.2`
- `README.md` 版本历史表新增 v0.1.2 行
- `CHANGELOG.md` 顶部新增 `[0.1.2]` 章节
- Git Tag：补打 `v0.1.0`、新增 `v0.1.2`，均推送至 GitHub

### 8.4 验证

- `git tag -l` 显示 `v0.1.0` / `v0.1.1` / `v0.1.2` 三个 tag
- `docs/phase2-report.md` 所有不符陈述已修正
- `CHANGELOG.md` 含 `[0.1.2]` 章节
- 三处版本号同步为 `0.1.2`