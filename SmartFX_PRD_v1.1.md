# SmartFX产品需求文档 PRD

**AI 智能外汇换汇参考工具 · USD / HKD / CNY**

| 项目 | 内容 |
|------|------|
| 产品名称 | SmartFX|
| 文档版本 | v1.1 |
| 产品负责人 | Victor Wu |
| 目标发布 | 普通版 MVP：T+10周；专业版：T+18周 |
| 前端框架 | Next.js (React) |
| 后端框架 | FastAPI (Python) |
| AI 模型 | Kimi API (moonshot-v1-8k / 32k) |
| 汇率数据 | ExchangeRate-API (Free Tier) + PBOC 官方接口 |
| 新增功能 | F-010 回测系统；F-011 半自动决策工具 |
| 文档状态 | v1.1 更新版，待评审 |

> ⚠️ **合规声明**：本文档所描述产品中所有 AI 生成内容均仅供信息参考，不构成任何投资建议。

---

## 目录

1. [产品概述](#1-产品概述)
2. [目标用户与核心痛点](#2-目标用户与核心痛点)
3. [产品信息架构](#3-产品信息架构ia)
4. [功能需求详述](#4-功能需求详述)
5. [技术架构](#5-技术架构)
6. [数据源与宏观指标体系](#6-数据源与宏观指标体系)
7. [AI 分析逻辑设计](#7-ai-分析逻辑设计)
8. [合规设计与风险控制](#8-合规设计与风险控制)
9. [开发路线图](#9-开发路线图)
10. [核心 API 接口规范](#10-核心-api-接口规范)
11. [非功能需求](#11-非功能需求)
12. [风险与应对策略](#12-风险与应对策略)
13. [附录：术语表](#附录术语表)

**v1.1 新增功能**
- [F-010 回测系统（Backtesting System）](#f-010-回测系统-backtesting-system--专业版专属)
- [F-011 半自动决策工具（Semi-Auto Decision Tool）](#f-011-半自动决策工具--专业版专属)

---

## 1. 产品概述

### 1.1 背景与动机

当前市场上的外汇查询工具（如 XE、货币换算小程序等）普遍存在同一核心缺陷：用户查完汇率后不知道"现在换合不合适"，工具只提供数字而不提供决策支持。

SmartFX旨在解决这一问题，将汇率工具从"查询工具"升级为"AI 辅助换汇决策参考平台"，覆盖留学生、跨境电商、外贸企业三大核心用户群。

> **核心定位**：换汇效率工具 + AI 辅助决策参考平台（非投资顾问，所有内容仅供参考）

### 1.2 产品目标

- **短期（MVP 阶段）**：上线普通版，提供实时汇率查询 + AI 每日换汇参考简报 + 对话式 AI 助手
- **中期**：上线专业版，提供成本/利润结算计算器 + AI 结算报告
- **长期**：打通小程序端，支持消息推送，成为跨境业务财务管理入口工具

### 1.3 产品版本与核心差异

| 功能维度 | 普通版（免费）| 专业版（SaaS 月付）|
|---------|------------|----------------|
| 目标用户 | 留学生、个人换汇 | 跨境电商、外贸企业 |
| 汇率计算器 | ✅ | ✅ |
| 近期区间雷达 | ✅ | ✅ |
| AI 每日简报 | ✅（查看）| ✅（邮件推送 + 查看）|
| AI 对话助手 | ✅（基础问答）| ✅（深度分析）|
| 持仓/换汇记录 | ✅（登录后）| ✅（多账户管理）|
| 成本/利润计算器 | ❌ | ✅ |
| 结算时机优化 | ❌ | ✅ |
| AI 结算分析报告 | ❌ | ✅（周报 + 即时生成）|
| 政策变动雷达 | ❌ | ✅ |
| **回测系统** | ❌ | ✅（AI 信号历史准确率 + 个人换汇回测）|
| **半自动决策工具** | ❌（仅基础预警）| ✅（条件预警 + 一键跳转执行）|
| 账户管理 | 需登录查看详情 | 必须登录，企业账户 |
| 推送方式 | 邮件（Web 阶段）| 邮件优先，后续小程序 |

---

## 2. 目标用户与核心痛点

| 用户群体 | 核心场景 | 深层痛点 | 优先级 |
|---------|---------|---------|-------|
| 跨境电商卖家（大陆）| 美元/港元收款后 → 结算为人民币 | 不知道何时结算利润最大化，汇损直接吃掉利润率 | P0 最高 |
| 外贸公司（大陆）| 报价/收款/结汇全周期管理 | 报价期到收款周期长，汇率波动导致利润不确定 | P0 最高 |
| 留学生 & 海外华人 | 家长换汇支付学费/生活费 | 不知现在是高点还是低点，总感觉时机没踩对 | P1 次高 |
| 个人理财用户 | 用汇率波动赚取差价 | 缺乏专业判断能力，需要简单化的参考信号 | P2 |

### 2.1 典型用户旅程

#### 普通版用户（留学生小陈）

1. 打开 SmartFX 首页，直接用计算器查今天美元换人民币汇率
2. 看到 AI 每日简报：「当前美元处于近 90 天区间中位，近两周小幅走弱，建议小额分批换入」
3. 点击查看详细分析（需登录）
4. 注册账号，保存本次换汇记录
5. 开启邮件订阅，每日接收换汇参考简报

#### 专业版用户（跨境电商公司财务王姐）

1. 登录专业版仪表盘，查看三货币实时汇率及近期波动图
2. 进入「结算计算器」：输入 "50,000 美元应收款，预计 14 天后到账，目标最大化人民币收入"
3. AI 输出结算时机分析：「当前汇率处于近 30 天高位，建议收款后 3-5 天内结算，预期比等待 2 周多获约 ¥3,200」
4. 下载/查阅 AI 生成的《本周外汇结算参考报告》
5. 设置汇率预警：当 USD/CNY 达到 7.35 时邮件通知

---

## 3. 产品信息架构（IA）

### 3.1 普通版页面结构

| 页面/模块 | 核心内容 | 登录要求 |
|---------|---------|---------|
| 首页 / 汇率仪表盘 | 三货币实时汇率、涨跌幅、汇率计算器、AI 每日简报摘要 | 无需登录 |
| 汇率计算器 | USD/HKD/CNY 任意方向互转，支持金额输入 | 无需登录 |
| 趋势图表 | 近 7/30/90 天折线图，区间高低点标注，RSI 指示器 | 无需登录（详细数据需登录）|
| AI 每日简报 | 今日换汇参考信号、宏观要闻摘要、短期趋势判断 | 需登录查看完整版 |
| AI 对话助手 | 自然语言问答，支持提问换汇相关问题 | 需登录 |
| 持仓/换汇记录 | 用户手动记录换汇行为，查看收益/损失参考 | 需登录 |
| 条件预警（基础版）| 设置目标汇率触发邮件通知 | 需登录 |
| 账户设置 | 邮件订阅管理、推送频率设置、偏好货币对 | 需登录 |

### 3.2 专业版页面结构（在普通版基础上新增）

| 页面/模块 | 核心内容 |
|---------|---------|
| 专业仪表盘 | 多货币组合概览、风险敞口热力图、待结算金额汇总 |
| 结算计算器 | 结构化输入（金额/到账日/目标）+ AI 结算时机分析输出 |
| AI 结算报告 | 周度/即时生成，包含趋势分析+政策解读+结算建议 |
| **回测系统** | AI 信号历史统计准确率展示 + 个人换汇决策回测分析 |
| **半自动决策工具** | 条件预警 + AI 建议推送 + 一键跳转执行（Stage 2）|
| 政策雷达 | PBOC/Fed/HKMA 政策动态 AI 摘要，实时更新 |
| 汇率预警系统 | 设置目标汇率区间，触发后邮件通知 |
| 企业账户管理 | 多成员管理、权限设置、历史报告归档 |

---

## 4. 功能需求详述

### F-001 汇率计算器

**优先级**：P0 · 版本：普通版 + 专业版 · 无需登录

**功能描述**：
- 支持货币对：USD ↔ CNY、HKD ↔ CNY、USD ↔ HKD（共6个方向）
- 实时汇率数据（刷新频率：每 5 分钟）
- 输入金额自动实时换算，支持反向计算
- 同时显示银行牌价参考范围（高/低区间提示）
- 计算结果可一键保存到换汇记录（需登录）

**输入/输出规格**：

| 字段 | 类型 | 说明 |
|-----|-----|-----|
| 源货币 | Select | USD / HKD / CNY |
| 目标货币 | Select | USD / HKD / CNY（不能与源货币相同）|
| 金额 | Number Input | 支持小数，最大 10 位 |
| 换算结果 | Display | 实时更新，保留4位小数 |
| 当前汇率 | Display | 来源标注 + 更新时间 |
| 参考范围 | Display | 近30天高/低点参考（灰色小字）|

---

### F-002 汇率走势图表

**优先级**：P0 · 版本：普通版 + 专业版 · 无需登录（完整数据需登录）

- 时间维度切换：7天 / 30天 / 90天 / 1年
- 图表类型：折线图（默认）+ 蜡烛图（专业版可切换）
- 关键标注：近期最高点（红色标记）、近期最低点（绿色标记）、当前价格位置
- 技术指标叠加（专业版）：RSI(14)、布林带(20)、MA7/MA30
- 区间定位标签：「当前处于近 90 天区间的 [X]% 位置」文字说明
- 图表右侧显示区间统计：最高、最低、均值、当前、区间位置百分比

---

### F-003 AI 每日简报

**优先级**：P0 · 版本：普通版（查看）/ 专业版（查看 + 邮件推送）

**触发逻辑**：
- 每日北京时间 **08:30** 自动生成（对应香港/内地开盘前），节假日不中断
- 数据锁定时间：07:30 快照，防止生成后数据变动

**内容结构**：

| 模块 | 内容 | AI 生成方式 |
|-----|-----|-----------|
| 今日汇率摘要 | 三对货币当前汇率 + 24h 涨跌幅 | 结构化数据填充（非 AI 生成）|
| 区间信号 | 各货币当前处于近30/90天区间位置 | AI 判断并生成文字 |
| 短期趋势判断 | 未来 1-2 周参考方向 | Kimi API 生成 |
| 宏观要闻摘要 | 影响外汇的 3 条关键新闻摘要 | Kimi API 摘要 |
| 换汇参考信号 | 「建议观望 / 可小额换入 / 建议结算」三档 + 理由 | Kimi API 生成 |
| 免责声明 | 固定模板 | 固定文本 |

**Kimi Prompt 设计规范**：

```
系统角色：
你是一个外汇走势分析助手，专注于 USD/CNY、HKD/CNY、USD/HKD 三对货币
走势分析。你的所有输出仅供信息参考，不构成投资建议。
请用简洁、专业、通俗易懂的中文输出。

数据输入结构：
【当前汇率数据】{rates_json}
【近90天价格统计】{stats_json}（最高/最低/均值/当前/区间分位数）
【主要宏观指标】{macro_json}（Fed利率/PBOC LPR/CPI/DXY/CNH-CNY价差）
【最新相关新闻标题】{news_list}（3-5条）
【用户类型】{user_type}（留学生/跨境电商/外贸公司）

输出要求：
- 区间信号：高位 / 中性 / 低位
- 短期趋势：看涨倾向 / 震荡 / 看跌倾向（附简短理由）
- 换汇参考信号：建议观望 / 可小额换入 / 建议结算
- 末尾固定输出：「⚠️ 以上内容仅供信息参考，不构成任何投资建议。」
```

---

### F-004 AI 对话助手

**优先级**：P1 · 版本：普通版（基础）/ 专业版（深度）· 需登录

- 对话界面：右下角浮动按钮 + 全屏对话页面两种模式
- 上下文维护：在同一会话内保持连续对话上下文（最多 20 轮）
- 数据感知：AI 可访问当日最新汇率数据和用户的换汇记录（脱敏后）
- 典型支持问题：
  - "现在美元高还是低？" → 基于区间分析回答
  - "我要换1万美元，现在换合适吗？" → 结合区间位置给出参考
  - "最近美联储开会对汇率有什么影响？" → 宏观解读
  - "帮我算一下我上个月换汇亏了多少" → 查询用户记录计算
- 每次回答末尾固定附加免责声明

---

### F-005 持仓/换汇记录

**优先级**：P1 · 版本：普通版 + 专业版 · 需登录

| 字段 | 类型 | 必填 |
|-----|-----|-----|
| 换汇日期 | DatePicker | 是 |
| 源货币 & 金额 | Select + Number | 是 |
| 目标货币 & 金额 | Select + Number | 是 |
| 成交汇率 | Number | 是（可从当日汇率自动填入）|
| 换汇目的 | Select（学费/生活/收款结算/其他）| 否 |
| 备注 | Text | 否 |
| 参考损益 | Computed | 与当前汇率比较，显示浮动收益/损失 |

- 支持列表视图和时间轴视图
- 汇总统计：总换汇量、平均换汇率、与当前汇率比较的参考损益
- 数据导出：CSV 格式（专业版支持 Excel）

---

### F-006 结算计算器 ⭐ 专业版专属

**优先级**：P0（专业版）· 需登录

#### 输入模式一：目标驱动型

| 输入字段 | 类型 | 示例 |
|---------|-----|-----|
| 应收款金额 | Number + 货币选择 | 50,000 USD |
| 预计到账日期 | DatePicker | 2025-03-15 |
| 结算目标货币 | Select | CNY |
| 优化目标 | Radio | 最大化人民币收入 / 最小化成本 |

#### 输入模式二：目标汇率型

| 输入字段 | 类型 | 示例 |
|---------|-----|-----|
| 应收款金额 | Number + 货币选择 | 50,000 USD |
| 预计到账日期 | DatePicker | 2025-03-15 |
| 目标汇率 | Number | 7.35（USD/CNY）|
| 最晚结算日期 | DatePicker（可选）| 2025-04-01 |

#### AI 分析输出结构

- 当前汇率 vs 近期区间：当前处于近 30 天高位/中位/低位
- 立即结算 vs 等待预估：「立即结算可得 ¥348,250，若等待至区间高位可能增加 ¥3,200（基于历史波动区间估算）」
- 建议结算窗口：「建议在 X 天内结算，当前汇率属于较优区间」
- 风险提示（固定）
- 一键生成完整分析报告（可下载 PDF）

---

### F-007 AI 结算分析报告 ⭐ 专业版专属

**优先级**：P1（专业版）· 需登录

**报告类型**：
- **即时报告**：用户点击"生成报告"后由 Kimi API 生成，约 30-60 秒
- **周度订阅报告**：每周一 08:30 自动生成发送到注册邮箱

**报告内容模块**：

| 章节 | 内容 |
|-----|-----|
| 本周汇率走势回顾 | 三对货币涨跌幅、关键事件对汇率的影响 |
| 宏观政策动态 | PBOC/Fed/HKMA 最新政策动态及影响分析 |
| 技术面信号 | RSI/布林带/均线信号综合判断 |
| 下周换汇参考展望 | 基于综合信号的换汇时机参考分析 |
| 外汇政策合规提示 | 当期外汇管制/结汇政策变化摘要（如有）|
| 免责声明 | 固定合规声明文本 |

---

### F-008 政策雷达 ⭐ 专业版专属

**优先级**：P2（专业版）· 需登录

- 监控来源：PBOC 官网、美联储 FOMC 声明、HKMA 港金管局、国家外汇管理局（SAFE）
- AI 处理：Kimi 自动摘要并标注「对 CNY/HKD 的潜在影响：利好 / 利空 / 中性」
- 展示方式：时间轴信息流，最新优先
- 推送规则：重大政策变化触发即时邮件推送

---

### F-009 汇率预警系统 ⭐ 专业版专属

**优先级**：P1（专业版）· 需登录

- 设置目标汇率区间或触发价格，达到条件时发送邮件通知
- 支持多条预警同时设置（最多10条）
- 预警类型：高于目标价、低于目标价、进入区间、离开区间
- 通知方式：邮件（Web 阶段），微信小程序推送（后续版本）

---

### F-010 回测系统（Backtesting System）⭐ 专业版专属

**优先级**：P1（专业版）· 需登录
**设计目标**：用历史数据证明 AI 信号的统计有效性，将用户的「盲目信任」转化为「基于统计的理性参考」，显著提升付费转化率与产品公信力。

> ⚠️ **合规说明**：所有回测数据以「历史统计吻合率」表述，严禁使用「准确率」「预测成功率」等字眼。任何展示数据均附注：「历史表现不代表未来，仅供参考」。

#### 子功能一：AI 信号历史吻合率看板（面向所有专业版用户）

展示 SmartFX 过去 N 天每日换汇参考信号与事后实际汇率走势的统计对比，量化信号的参考价值。

**展示内容**：

| 指标 | 说明 | 示例 |
|-----|-----|-----|
| 统计周期 | 近 30 / 60 / 90 天可切换 | 近 90 天 |
| 信号总数 | 各类信号的发出次数 | 买入 32 次 / 持有 30 次 / 结算 28 次 |
| 7日吻合率 | 信号后 7 天内走势与信号方向一致的比例 | 买入信号：68% |
| 14日吻合率 | 信号后 14 天内走势吻合率 | 买入信号：64% |
| 综合参考指数 | 三类信号加权平均吻合率 vs 随机基准（50%）| 67.4% vs 50%（基准）|
| 最佳信号类型 | 吻合率最高的信号类别 | 「结算信号」近 90 天吻合率 71% |

**数据采集规则**：
- 系统从上线第一天起自动存储每日 AI 信号到 `daily_reports` 表
- 60 天后自动解锁回测看板（数据量不足时显示「数据积累中，预计 XX 天后开放」）
- 冷启动方案：上线前基于历史汇率数据预运行信号逻辑，生成 90 天「模拟历史基线」，页面注明「以下数据为产品上线前基于历史数据的模拟运行结果，非真实信号记录」

#### 子功能二：个人换汇决策回测（面向有换汇记录的专业版用户）

用户导入或已有的换汇记录，系统模拟「若每次都参考 SmartFX 信号操作」的假设结果，直观展示潜在损益改善。

**交互流程**：
1. 用户进入「我的回测」页面，选择回测时间范围
2. 系统读取该用户在此期间的换汇记录
3. 对每笔记录，查找当天 SmartFX 的信号及事后 7/14 天汇率
4. 计算「实际换汇均价」vs「若遵循信号的假设换汇均价」
5. 展示参考损益差异

**输出示例**：
```
您的换汇回测报告（2024-10 至 2025-01）

实际换汇记录：5 笔，总金额 50,000 USD
实际平均换汇率：7.2134

假设参考 SmartFX 信号操作（历史模拟）：
模拟平均换汇率：7.2489
参考差异：+¥17,750

⚠️ 以上为历史假设模拟，不代表未来表现，不构成任何投资建议。
```

**技术实现**：

```python
# 回测核心逻辑（伪代码）
def personal_backtest(user_records: list, signals: dict, prices: dict, window: int = 7):
    actual_rates = [r['rate_used'] for r in user_records]
    simulated_rates = []

    for record in user_records:
        date = record['exchange_date']
        signal = signals.get(date, {}).get('signal_usd_cny')
        
        # 若当日信号为「可换入」且用户确实换入，视为信号一致
        # 若当日信号为「建议观望」，模拟推迟至 signal 变为「可换入」的最近日期
        optimal_date = find_next_buy_signal(date, signals)
        simulated_rates.append(prices[optimal_date])

    return {
        'actual_avg': sum(actual_rates) / len(actual_rates),
        'simulated_avg': sum(simulated_rates) / len(simulated_rates),
        'diff_pct': (sum(simulated_rates) - sum(actual_rates)) / sum(actual_rates)
    }
```

**新增数据库表**：

```sql
-- 每日信号快照（在原 daily_reports 表基础上扩展）
ALTER TABLE daily_reports ADD COLUMN signal_hkd_usd ENUM('buy','hold','sell');
ALTER TABLE daily_reports ADD COLUMN rates_7d_after JSONB;   -- 7天后汇率快照（定时回填）
ALTER TABLE daily_reports ADD COLUMN rates_14d_after JSONB;  -- 14天后汇率快照（定时回填）

-- 回测结果缓存表（避免重复计算）
CREATE TABLE backtest_cache (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    pair            VARCHAR(7) NOT NULL,
    actual_avg_rate DECIMAL(10,6),
    simulated_avg_rate DECIMAL(10,6),
    diff_amount     DECIMAL(18,2),
    base_amount     DECIMAL(18,4),
    base_currency   VARCHAR(3),
    generated_at    TIMESTAMP DEFAULT NOW()
);
```

---

### F-011 半自动决策工具 ⭐ 专业版专属

**优先级**：P1 / Stage 1（专业版）· 需登录
**设计目标**：在 AI 分析和实际换汇行为之间建立「最短路径」，将「看完建议还要去银行操作」的体验断层最小化。分三个阶段落地，每个阶段独立交付价值。

> ⚠️ **合规红线**：用户必须主动确认每笔换汇操作。系统永远不得在未经用户明确指令的情况下自动执行任何资金操作，否则触碰「代客理财」监管红线。

#### 三阶段落地路径

| 阶段 | 功能描述 | 合规风险 | 技术难度 | 版本目标 |
|------|---------|---------|---------|---------|
| Stage 1：智能条件预警 | AI 信号 + 用户自定义条件触发推送通知，用户手动去外部平台执行 | 低 | 低 | v1.0 专业版 |
| Stage 2：一键跳转执行 | 通知内含深度链接，点击直跳银行/理财通换汇页，金额汇率预填充 | 低 | 中 | v2.0 |
| Stage 3：平台内执行闭环 | 接入理财通/微众银行 API，在 SmartFX 内完成换汇，结果自动同步记录 | 高（需牌照）| 高 | v3.0（长期）|

#### Stage 1 详细设计（当前版本实现）

**功能：AI 触发式条件预警**

在 F-009「汇率预警系统」基础上升级，新增 AI 联动触发能力：

**两种触发模式**：

模式 A — 用户自定义条件触发：
```
用户设置：「当 USD/CNY < 7.20 时通知我，我有 10,000 USD 想换入」
系统行为：实时监控 → 条件满足 → 推送邮件/通知
通知内容：「您设置的换汇条件已触发！
           当前汇率：7.1988（低于您的目标 7.20）
           参考金额：10,000 USD → 约 ¥71,988
           [查看今日 AI 分析] [去银行换汇]」
```

模式 B — AI 信号主动推送（新增）：
```
用户设置：开启「AI 信号主动推送」，并填写持仓信息
          （「我持有 20,000 USD，关注换入时机」）
系统行为：当 AI 每日简报生成「可换入」信号时，
          额外推送个性化通知给开启该功能的用户
通知内容：「SmartFX AI 今日参考信号：USD/CNY 可换入
           当前：7.2156 | 近90天区间：低位（35th percentile）
           RSI(14)：38（偏弱，历史参考吻合率 68%）
           ⚠️ 仅供参考，不构成投资建议
           [查看完整分析] [去换汇]」
```

**输入配置界面**：

| 配置项 | 类型 | 说明 |
|-------|-----|-----|
| 监控货币对 | Multi-select | USD/CNY、HKD/CNY、USD/HKD |
| 触发模式 | Radio | 自定义条件 / AI 信号推送 / 两者都要 |
| 自定义条件 | 条件构建器 | 货币对 + 方向（高于/低于）+ 目标价 |
| 关注金额（可选）| Number | 填写后推送通知中自动计算换汇参考金额 |
| 推送方式 | Checkbox | 邮件（必选）/ 浏览器通知（可选）|
| 推送频率限制 | Select | 每日最多 1 次 / 3 次 / 不限 |
| 静默时段 | TimePicker | 设置不接收通知的时段（如 22:00-08:00）|

**通知模板（邮件）**：

```
主题：[SmartFX] 您的换汇参考条件已触发 · USD/CNY 7.1988

您好，

您设置的换汇参考条件「USD/CNY 低于 7.20」已满足。

当前汇率：1 USD = 7.1988 CNY（更新于 14:32）
近 90 天区间位置：较低区间（第 34 百分位）
今日 AI 参考信号：可换入
参考理由：当前汇率处于近期区间低位，RSI(14)=38，
          历史上此区间换入后7日走强概率约 68%。

您可查看完整分析后自行决定是否操作。

[查看完整 AI 分析报告]

⚠️ 免责声明：以上内容由 AI 基于公开数据生成，仅供信息参考，
不构成任何投资建议。汇率存在波动风险，操作风险请自行评估。

SmartFX 团队
```

#### Stage 2 预研（v2.0 规划，非当前实现）

当触发通知时，在通知和产品内新增「一键跳转换汇」按钮：
- 按钮点击后，构建目标银行/理财通的深度链接 URL，预填充货币对和金额参数
- 需要与招商银行、建设银行、理财通等平台签订合作协议，获取其开放 API 或 URL Scheme

```
深度链接示例（预研，非实际 API）：
weixin://dl/business/?appid=wx_lctong&amount=10000&from=USD&to=CNY&rate=7.1988
```

#### Stage 3 预研（v3.0 长期规划，非当前实现）

接入理财通/微众银行换汇服务 API，在 SmartFX 内完成完整换汇闭环：
- 换汇执行结果自动同步到「持仓/换汇记录」
- 商业模式升级为交易抽佣（每笔换汇收取 0.05%-0.1% 手续费分润）
- 需要：理财通内部资源协调 + SAFE 合规审查 + 资金安全体系建设

**新增数据库表（Stage 1）**：

```sql
-- 半自动决策规则表
CREATE TABLE auto_decision_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    rule_name       VARCHAR NOT NULL,           -- 用户自定义规则名称
    pair            VARCHAR(7) NOT NULL,        -- USD/CNY 等
    trigger_mode    ENUM('custom', 'ai_signal', 'both') NOT NULL,
    condition_type  ENUM('above','below','enter_range','exit_range'),
    target_rate     DECIMAL(10,6),
    watch_amount    DECIMAL(18,4),              -- 关注金额（可选）
    watch_currency  VARCHAR(3),
    notify_email    BOOLEAN DEFAULT true,
    notify_browser  BOOLEAN DEFAULT false,
    max_daily_alerts INTEGER DEFAULT 3,
    quiet_start     TIME,                       -- 静默时段开始
    quiet_end       TIME,                       -- 静默时段结束
    is_active       BOOLEAN DEFAULT true,
    last_triggered  TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 触发历史表
CREATE TABLE alert_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id         UUID REFERENCES auto_decision_rules(id),
    user_id         UUID REFERENCES users(id),
    triggered_at    TIMESTAMP DEFAULT NOW(),
    trigger_rate    DECIMAL(10,6),              -- 触发时汇率
    trigger_type    ENUM('custom_condition','ai_signal'),
    ai_signal       ENUM('buy','hold','sell'),
    notification_sent BOOLEAN DEFAULT false,
    user_action     ENUM('viewed','clicked_exchange','ignored'),  -- 用户后续行为追踪
    actioned_at     TIMESTAMP
);
```

---

## 5. 技术架构

### 5.1 整体架构

```
用户层（浏览器 / 未来小程序）
    ↕ HTTPS
前端层：Next.js (React) + Tailwind CSS  ← Vercel
    ↕ REST API
后端层：FastAPI (Python)  ← Railway
    ├── 汇率数据服务（ExchangeRate-API + PBOC 接口）
    ├── AI 服务（Kimi API 封装层）
    ├── 定时任务（APScheduler：每日简报 + 周报）
    ├── 邮件服务（Resend）
    └── 数据存储（PostgreSQL + Redis 缓存）
```

### 5.2 技术选型

| 层级 | 技术 | 选型理由 |
|-----|-----|---------|
| 前端框架 | Next.js 14 (App Router) | SSR + CSR 混合，SEO 友好 |
| UI 组件库 | Tailwind CSS + shadcn/ui | 快速构建专业界面 |
| 图表库 | Recharts + TradingView Lightweight Charts | Recharts 统计图，TradingView 蜡烛图 |
| 后端框架 | FastAPI (Python) | 异步性能好，AI/数据处理生态完善 |
| AI 模型 | Kimi API (moonshot-v1-8k) | 中文理解优秀，长上下文，成本可控 |
| 汇率数据（免费）| ExchangeRate-API Free Tier | 1500次/月免费额度，MVP 够用 |
| PBOC 数据 | 人民银行官方 RSS/接口 | 权威中间价来源，免费 |
| 数据库 | PostgreSQL (Railway) | 关系型，适合用户/记录/报告存储 |
| 缓存 | Redis (Railway) | 汇率数据缓存，减少 API 调用 |
| 定时任务 | APScheduler (FastAPI 内置) | 每日简报/周报定时生成 |
| 邮件服务 | Resend | 开发者友好，免费层够 MVP |
| 部署 | Vercel (前端) + Railway (后端) | 免费层可用于 MVP，CI/CD 集成简单 |
| 认证 | NextAuth.js + JWT | 支持邮箱注册 + Google OAuth（后续）|

### 5.3 数据库模型（核心表）

#### users

```sql
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR UNIQUE NOT NULL,
    plan        ENUM('free', 'pro') DEFAULT 'free',
    created_at  TIMESTAMP DEFAULT NOW(),
    notification_pref JSONB DEFAULT '{}'
);
```

#### exchange_records（换汇记录）

```sql
CREATE TABLE exchange_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    from_currency   VARCHAR(3) NOT NULL,   -- USD/HKD/CNY
    to_currency     VARCHAR(3) NOT NULL,
    from_amount     DECIMAL(18,4) NOT NULL,
    to_amount       DECIMAL(18,4) NOT NULL,
    rate_used       DECIMAL(10,6) NOT NULL,
    exchange_date   DATE NOT NULL,
    purpose         VARCHAR,               -- 学费/生活/收款结算/其他
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

#### daily_reports（每日 AI 简报）

```sql
CREATE TABLE daily_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_date     DATE UNIQUE NOT NULL,
    rates_snapshot  JSONB NOT NULL,        -- 生成时的汇率快照
    ai_content      TEXT NOT NULL,         -- Kimi 生成的完整内容
    signal_usd_cny  ENUM('buy','hold','sell'),
    signal_hkd_cny  ENUM('buy','hold','sell'),
    created_at      TIMESTAMP DEFAULT NOW()
);
```

#### alerts（汇率预警，专业版）

```sql
CREATE TABLE alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    pair            VARCHAR(7) NOT NULL,   -- USD/CNY 等
    condition       ENUM('above','below','enter_range','exit_range'),
    target_rate     DECIMAL(10,6),
    range_low       DECIMAL(10,6),
    range_high      DECIMAL(10,6),
    is_active       BOOLEAN DEFAULT true,
    triggered_at    TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

## 6. 数据源与宏观指标体系

### 6.1 数据源清单

| 数据类型 | 来源 | 接入方式 | 更新频率 | 费用 |
|---------|-----|---------|---------|-----|
| USD/HKD/CNY 实时汇率 | ExchangeRate-API | REST API | 每5分钟 | 免费（1500次/月）|
| PBOC 人民币中间价 | 人民银行官网 | RSS/网页抓取 | 每日09:15 | 免费 |
| CNH（离岸人民币）| ExchangeRate-API | REST API | 每15分钟 | 免费 |
| 美元指数 DXY | Alpha Vantage 免费层 | REST API | 每日 | 免费（500次/日）|
| Fed 基准利率 | FRED API（美联储）| REST API | 按会议更新 | 免费 |
| 美国 CPI / PCE | FRED API | REST API | 月度 | 免费 |
| 中国 CPI/PPI | 国家统计局 | 网页抓取 | 月度 | 免费 |
| 中国外汇储备 | SAFE 官网 | 网页抓取 | 月度 | 免费 |
| 相关财经新闻 | NewsAPI.org 免费层 | REST API | 每小时 | 免费（100次/日）|

### 6.2 四层宏观指标框架

#### 第一层：价格数据（必接）

- USD/CNY 现货汇率
- USD/HKD 现货汇率（联系汇率 7.75-7.85 区间）
- CNH/CNY 价差：离岸与在岸差值，>200bp 信号意义显著
- 近 7/30/90 天历史价格（本地数据库存储）

#### 第二层：政策利率（核心驱动）

- 美联储基准利率（Fed Funds Rate）+ 下次会议预期（CME FedWatch）
- PBOC LPR（贷款市场报价利率）+ MLF 操作情况
- 中美利差（10年期国债收益率差）

#### 第三层：通胀与经济数据（月度）

- 美国 CPI YoY + 核心 PCE
- 美国非农就业（NFP，每月第一个周五）
- 中国 CPI + PPI
- 中国贸易顺差/逆差数据

#### 第四层：技术指标（本地计算）

| 指标 | 参数 | 用途 |
|-----|-----|-----|
| RSI | 14日 | 超买(>70) / 超卖(<30) 信号 |
| 布林带 | 20日，2σ | 价格位于带宽内的相对位置 |
| MA | 7日 / 30日 | 短期趋势方向 |
| 区间位置 | 过去90天 | 当前价格在区间内的百分位 |
| CNH-CNY 价差 | 实时计算 | 市场对人民币预期的分歧度 |

---

## 7. AI 分析逻辑设计

### 7.1 每日简报生成流程

```
07:30  系统自动抓取最新数据快照
  ↓
计算各货币对区间分位数、RSI、均线方向
  ↓
从 NewsAPI 抓取最新外汇相关新闻标题（3-5条）
  ↓
组装 Prompt → 调用 Kimi API (moonshot-v1-8k)
  ↓
解析 AI 输出，提取结构化信号（买入/持有/结算）
  ↓
存储到 daily_reports 表
  ↓
08:30  推送邮件给订阅用户
```

### 7.2 结算计算器 AI 分析逻辑

```
输入处理：
1. 计算当前汇率在近30/90天的分位数
2. 计算布林带位置（上轨/中轨/下轨）
3. 预估未来 N 天内到达历史高低区间的统计概率
4. 计算立即结算 vs 等待至区间高点的预期收益差（含概率权重）
5. 将以上数据 + 用户输入 → 组装 Prompt → 调用 Kimi

输出规范：
- 结构化 JSON（供前端展示）
- 自然语言段落（供报告展示）
- 固定附加风险提示和免责声明
```

### 7.3 Kimi API 调用规范

| 场景 | 模型 | 预估 Token | 调用频率 |
|-----|-----|-----------|---------|
| 每日简报生成 | moonshot-v1-8k | ~2,000 tokens/次 | 1次/天 |
| 结算计算器分析 | moonshot-v1-8k | ~3,000 tokens/次 | 按需（用户触发）|
| AI 对话助手（普通）| moonshot-v1-8k | ~1,000 tokens/轮 | 按需 |
| AI 对话助手（专业）| moonshot-v1-32k | ~4,000 tokens/轮 | 按需 |
| 周度结算报告 | moonshot-v1-32k | ~6,000 tokens/次 | 1次/周 |

---

## 8. 合规设计与风险控制

### 8.1 合规定位原则

> **产品定性**：SmartFX 是「换汇效率工具与汇率信息参考平台」，不是「外汇投资顾问」。所有 AI 输出均为基于历史数据和公开信息的参考分析，不构成任何形式的投资建议或理财推荐。

### 8.2 语言规范：禁止 vs 推荐

| ❌ 禁止使用 | ✅ 应替换为 |
|-----------|-----------|
| AI 外汇投资顾问 | AI 汇率参考助手 |
| 我们建议你今天买入美元 | 当前汇率处于近期区间低位，历史上此区间换入胜率约65%，仅供参考 |
| 帮你赚取外汇差价 | 优化换汇时机，减少汇率损耗 |
| 预测明天汇率上涨 | 基于近期技术信号，短期存在走强倾向（历史参考，不代表未来）|
| 建议 | 参考信号 / 参考方向 |
| 保证收益 | 历史区间参考 |

### 8.3 强制合规措施（6项）

1. 全站显著位置放置免责声明，字体不小于正文 80%
2. 所有 AI 生成内容末尾固定添加：`⚠️ 以上内容由 AI 基于公开数据生成，仅供信息参考，不构成任何投资建议。汇率存在波动风险，操作风险请自行评估。`
3. 用户注册时必须勾选「风险告知协议」才能使用 AI 功能
4. AI 输出中"建议"字眼统一替换为"参考信号"或"参考方向"
5. 专业版「结算分析报告」首页加入合规声明页
6. 定期审查 AI 输出内容，确保无违规表述

### 8.4 数据隐私合规

- 用户换汇记录等个人数据仅用于该用户自身的分析，不得用于训练模型或对外共享
- 遵守《个人信息保护法》（PIPL，大陆用户）和《个人资料（私隐）条例》（香港用户）
- 隐私政策中明确说明数据存储位置、用途、保留期限及用户数据删除权利

---

## 9. 开发路线图

### 阶段一：普通版 MVP（T+10周）

| Sprint | 周期 | 交付内容 |
|--------|------|---------|
| Sprint 1 | Week 1-2 | 项目脚手架（Next.js + FastAPI）、数据库初始化、ExchangeRate-API 接入、基础汇率计算器页面 |
| Sprint 2 | Week 3-4 | PBOC 数据接入、汇率走势折线图（7/30/90天）、区间高低点标注、用户注册/登录（NextAuth）|
| Sprint 3 | Week 5-6 | Kimi API 接入、每日简报生成逻辑、简报展示页面、AI 对话助手基础版 |
| Sprint 4 | Week 7-8 | 换汇记录 CRUD、持仓页面、邮件订阅（Resend 接入）、每日简报邮件模板 |
| Sprint 5 | Week 9-10 | 整体 UI 精修（shadcn/ui）、移动端响应式、合规检查、Vercel + Railway 部署上线 |

### 阶段二：专业版（T+18周）

| Sprint | 周期 | 交付内容 |
|--------|------|---------|
| Sprint 6 | Week 11-12 | 专业版账户体系、结算计算器 UI + 计算逻辑、Kimi 结算分析 Prompt 设计 |
| Sprint 7 | Week 13-14 | AI 结算分析报告生成 + PDF 导出、周度报告定时任务、蜡烛图 + 技术指标（TradingView）|
| Sprint 8 | Week 15-16 | **F-010 回测系统**：信号吻合率看板 + 历史信号数据回填 + 个人回测引擎 |
| Sprint 9 | Week 17-18 | **F-011 半自动决策工具 Stage 1**：AI 信号触发规则配置 + 条件预警推送 + 触发历史追踪；政策雷达；专业版上线 |

### V2 规划（T+26周）

| Sprint | 周期 | 交付内容 |
|--------|------|---------|
| Sprint 10-11 | Week 19-22 | 企业版多成员管理、企业微信插件集成、汇率预警系统升级 |
| Sprint 12-13 | Week 23-26 | **F-011 Stage 2**：一键跳转银行/理财通换汇（深度链接 BD 合作）；回测系统升级（用户行为追踪反馈） |

### V3+ 后续规划（长期）

- **F-011 Stage 3**：理财通/微众银行换汇 API 接入，平台内换汇执行闭环，商业模式升级为交易抽佣
- 微信小程序端开发（支持微信推送通知，替代邮件）
- 更多货币对（EUR、JPY、GBP 等）
- 微信支付跨境交易数据接入，AI 信号质量升级
- 银行牌价对比功能

---

## 10. 核心 API 接口规范

| 接口 | 方法 | 路径 | 说明 | 权限 |
|-----|-----|-----|-----|-----|
| 获取实时汇率 | GET | `/api/rates/live` | 返回三对货币最新汇率 | 公开 |
| 获取历史数据 | GET | `/api/rates/history` | 参数：pair, days(7/30/90/365) | 公开 |
| 获取区间统计 | GET | `/api/rates/stats` | 返回高/低/均值/当前/分位数 | 公开 |
| 获取今日简报 | GET | `/api/report/daily` | 返回今日 AI 简报内容 | 需登录 |
| AI 对话 | POST | `/api/ai/chat` | body: {message, history} | 需登录 |
| 结算计算 | POST | `/api/pro/settlement` | body: {amount, currency, days, goal} | 专业版 |
| 生成结算报告 | POST | `/api/pro/report/generate` | body: {settlement_data} | 专业版 |
| 换汇记录列表 | GET | `/api/records` | 用户换汇记录 | 需登录 |
| 新增换汇记录 | POST | `/api/records` | body: exchange record | 需登录 |
| 设置预警 | POST | `/api/alerts` | body: {pair, condition, target_rate} | 专业版 |
| 用户注册 | POST | `/api/auth/register` | body: {email, password} | 公开 |
| 用户登录 | POST | `/api/auth/login` | NextAuth 处理 | 公开 |
| **获取信号吻合率看板** | GET | `/api/pro/backtest/overview` | 参数：pair, days(30/60/90)；返回各信号吻合率统计 | 专业版 |
| **触发个人换汇回测** | POST | `/api/pro/backtest/personal` | body: {period_start, period_end, pair}；异步计算，返回 job_id | 专业版 |
| **查询回测结果** | GET | `/api/pro/backtest/result/{job_id}` | 轮询获取异步回测计算结果 | 专业版 |
| **获取半自动规则列表** | GET | `/api/pro/auto-rules` | 用户已设置的决策规则 | 专业版 |
| **创建半自动规则** | POST | `/api/pro/auto-rules` | body: {pair, trigger_mode, condition, watch_amount, ...} | 专业版 |
| **更新半自动规则** | PATCH | `/api/pro/auto-rules/{id}` | body: 规则更新字段 | 专业版 |
| **删除半自动规则** | DELETE | `/api/pro/auto-rules/{id}` | 软删除（is_active=false）| 专业版 |
| **获取触发历史** | GET | `/api/pro/auto-rules/history` | 参数：rule_id(可选), limit | 专业版 |
| **更新触发行为追踪** | PATCH | `/api/pro/auto-rules/history/{id}` | body: {user_action}；记录用户是否点击执行 | 专业版 |

---

## 11. 非功能需求

| 类别 | 指标 | 目标值 |
|-----|-----|-------|
| 性能 | 首页加载时间（FCP）| < 2 秒（3G 网络）|
| 性能 | 汇率数据刷新延迟 | < 5 分钟（免费 API 限制内）|
| 性能 | AI 对话响应时间 | < 8 秒（Kimi API 典型响应）|
| 可用性 | 系统可用率 | > 99%（Vercel + Railway SLA）|
| 安全性 | 用户密码存储 | bcrypt 加盐哈希，绝不明文存储 |
| 安全性 | API 请求 | HTTPS 加密，JWT 鉴权，Rate Limiting（100次/分钟/用户）|
| 可扩展性 | Redis 缓存策略 | 汇率数据缓存 5 分钟，简报内容缓存 1 天 |
| 移动端 | 响应式适配 | 支持 iOS/Android 浏览器，后续转小程序 |
| SEO | 关键页面 SSR | 首页、汇率页使用 Next.js SSR |

---

## 12. 风险与应对策略

| 风险 | 概率 | 影响 | 应对策略 |
|-----|-----|-----|---------|
| ExchangeRate-API 免费层额度不足 | 中 | 高 | 实施 Redis 缓存，减少 API 调用；MVP 后期迁移付费层 |
| Kimi API 调用成本超预期 | 低 | 中 | 设置每日 Token 预算上限；对话轮次限制（普通版 20 轮/天）|
| AI 生成内容出现合规风险表述 | 中 | 高 | 输出后置过滤器，检测"预测"/"保证"等敏感词；固定免责声明 |
| PBOC 数据抓取被封 IP | 低 | 中 | 使用官方 RSS 接口；增加轮询间隔；备用数据源 |
| 用户量增长导致 Railway 免费层不足 | 中 | 低 | 提前准备付费迁移方案；架构保持水平扩展能力 |
| 政策变化影响产品定位（如外汇新规）| 低 | 高 | 持续监控 SAFE、PBOC 政策；保持产品定性为"参考工具" |

---

## 附录：术语表

| 术语 | 说明 |
|-----|-----|
| USD/CNY | 美元兑人民币（在岸）汇率，PBOC 每日公布中间价 |
| CNH | 离岸人民币，在香港等境外市场自由交易，反映市场预期 |
| HKD | 港元，实行联系汇率制度，与美元挂钩（7.75-7.85 区间）|
| PBOC | 中国人民银行（中国央行）|
| FOMC | 美联储公开市场委员会，决定美国基准利率 |
| HKMA | 香港金融管理局（香港央行）|
| SAFE | 国家外汇管理局，监管中国外汇市场 |
| LPR | 贷款市场报价利率，PBOC 参考利率 |
| RSI | 相对强弱指数，衡量价格超买/超卖程度的技术指标 |
| DXY | 美元指数，衡量美元对一篮子主要货币的综合强弱 |
| CNH-CNY 价差 | 离岸与在岸人民币汇率差值，反映市场对人民币走势分歧 |
| 结算 | 跨境电商/外贸将外币应收款转换为人民币的操作 |
| 牌价 | 商业银行公布的外币兑换价格，通常与中间价存在点差 |
| 布林带 | 以移动均线为中轨，上下各加减2倍标准差的价格通道 |
| APScheduler | Python 定时任务调度库，用于每日/每周自动任务 |

---

*SmartFX PRD v1.1 · 新增 F-010 回测系统 & F-011 半自动决策工具 · 所有内容均不构成投资建议 · 文档结束*
