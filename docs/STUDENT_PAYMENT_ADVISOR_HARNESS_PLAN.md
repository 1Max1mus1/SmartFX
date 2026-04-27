# SmartFX 留学生缴费助手 AI Coding Plan

## 1. 文档目标

本计划用于指导在现有 SmartFX 代码库中，以 Harness 风格落地“留学生缴费助手”。

目标不是重做一套新系统，而是在现有 AI 助手、汇率服务和结算分析能力基础上，新增一个：

- 结构化输入
- 规则可控
- AI 可解释
- 可测试

的留学生缴费时机建议模块。

---

## 2. 范围定义

### 2.1 本次范围

- 入口放在 `apps/web/app/assistant/page.tsx`
- 只支持 `USD / HKD / CNY`
- 新增专用后端接口
- 输出结构化建议结果
- 支持把结果延伸到现有聊天区继续追问

### 2.2 不在本次范围

- 不改动支付渠道
- 不改动数据库结构作为上线前置条件
- 不做自动提醒
- 不扩币种
- 不引入预测模型

---

## 3. 当前代码现状与复用点

### 3.1 已有前端

- `apps/web/app/assistant/page.tsx`
- 已有自由聊天页面与请求提交逻辑

### 3.2 已有后端

- `apps/api/src/routers/ai_chat.py`
- `apps/api/src/services/chat_service.py`
- `apps/api/src/services/rate_service.py`
- `apps/api/src/services/settlement_service.py`
- `apps/api/src/clients/kimi_client.py`

### 3.3 可直接复用的能力

- 当前实时汇率查询
- 7/30/90 天分位统计
- AI fallback 机制
- disclaimer 追加逻辑

### 3.4 本次建议新增的独立模块

- `apps/api/src/schemas/student_payment.py`
- `apps/api/src/services/student_payment_advice_service.py`
- `apps/api/src/routers/student_payment_advice.py`

前端建议新增：

- `apps/web/components/student-payment-advisor-card.tsx`

如需拆分更细，也可拆为：

- `student-payment-advisor-form.tsx`
- `student-payment-advice-result.tsx`

---

## 4. Harness 工作原则

### 4.1 先搭边界，再填 AI

优先顺序：

1. 明确 request/response schema
2. 落规则判断
3. 加 fallback
4. 再加 AI 文案增强
5. 最后接前端 UI

### 4.2 AI 只做解释，不做最终裁决

最终动作建议必须由后端规则先给出，AI 只负责：

- 用户可读解释
- 风险提示
- 可继续追问的分析文案

### 4.3 每阶段必须可验证

每一阶段都应满足：

- 能运行
- 能测试
- 失败时可回退

---

## 5. 目标输出

最终交付应包括：

1. AI 助手页中的留学生缴费助手 UI
2. 新 API：`POST /api/ai/student-payment-advice`
3. 规则化建议结果
4. AI 增强解释
5. 单元测试与集成测试
6. 文案合规检查

---

## 6. 接口规划

### 6.1 新增接口

- `POST /api/ai/student-payment-advice`

### 6.2 请求字段

- `deadline_date`
- `amount`
- `source_currency`
- `target_currency`
- `can_split_payment`
- `risk_preference`
- `notes`

### 6.3 响应字段

- `decision`
- `decision_level`
- `decision_reason`
- `rate_assessment`
- `deadline_pressure`
- `suggested_action`
- `split_payment_plan`
- `market_snapshot`
- `analysis_markdown`
- `disclaimer`

---

## 7. 分阶段实施计划

## Phase 1：后端结构与规则底座

### 目标

先把不依赖 AI 的结构化建议链路跑通。

### 必做项

- 新增 `student_payment.py` schema
- 新增 `student_payment_advice_service.py`
- 新增 router 并挂载到 `/api/ai`
- 完成输入校验
- 完成汇率位置判断
- 完成截止压力判断
- 完成动作建议与分批建议
- 输出固定 disclaimer

### 规则建议

- 用 `RateService.get_live_conversion_rate`
- 用 `RateService.get_stats` 获取 30 天和 90 天分位
- 用日期差计算截止压力
- 先输出纯规则版本 `analysis_markdown`

### 交付结果

- 新接口可返回稳定 JSON
- 即使 AI 关闭，也能完整使用

### 验收标准

- 输入合法时返回 200
- 输入非法币种时返回 400
- 输出中必须含 `decision`
- 输出中必须含 `rate_assessment`
- 输出中必须含 `disclaimer`

---

## Phase 2：AI 文案增强

### 目标

在不改变规则结论的前提下，让结果更自然、更像顾问式解释。

### 必做项

- 在 `KimiClient` 中新增专用方法
  - 建议名：`generate_student_payment_advice`
- 增加 fallback 逻辑
- 确保 AI 返回失败时仍使用规则文案
- 加入合规语言约束

### Prompt 要求

- 不能承诺未来涨跌
- 不能输出“稳赚”“抄底”“最佳买点”
- 必须解释“为什么建议今天交/分批交/先观察”
- 必须保留 disclaimer

### 验收标准

- AI 可用时返回更自然的 `analysis_markdown`
- AI 不可用时 fallback 仍完整
- 不出现违禁表达

---

## Phase 3：前端 AI 助手页集成

### 目标

把结构化模块接入现有 AI 助手页，而不破坏自由聊天体验。

### 必做项

- 在 `assistant/page.tsx` 中加入留学生缴费助手区域
- 新增本地状态管理
- 接入 `POST /api/ai/student-payment-advice`
- 增加结果卡片展示
- 增加 loading/error 状态
- 增加“继续追问”按钮

### UI 展示建议

- 左侧为介绍与快捷问题
- 中部为结构化输入表单
- 右侧或下方为结果卡片

结果卡片建议固定模块：

- 今日建议
- 当前汇率位置
- 截止日压力
- 推荐动作
- 分批方案
- 说明与免责声明

### 验收标准

- 页面可正常渲染
- 提交表单后能看到结构化结果
- 错误时有清晰提示
- 原有聊天表单仍可使用

---

## Phase 4：结果与聊天联动

### 目标

让结构化建议不成为信息孤岛，用户可在聊天区继续追问。

### 实现建议

选一种简单稳定的方式：

1. 点击 `继续追问`
2. 将一段摘要文本写入聊天输入框
3. 用户直接发送或编辑后发送

示例摘要：

`我刚拿到一个缴费建议：当前 USD/CNY 处于近 30 天较低位置，建议先支付 70%，剩余 30% 观察 1-2 天。请你进一步解释为什么这样安排。`

### 验收标准

- 点击按钮后聊天输入框自动填入摘要
- 用户仍可修改内容
- 不需要改动历史消息持久化结构

---

## Phase 5：测试与合规加固

### 目标

确保此功能不是“看起来能用”，而是真的稳定可回归。

### 后端测试

建议新增：

- `apps/api/tests/test_student_payment_advice.py`

测试点：

- 正常返回结构化结果
- 不同截止日期得到不同紧迫度
- 不同 30d 分位映射到正确标签
- `can_split_payment=false` 时不输出分批方案
- AI 失败时 fallback 生效
- disclaimer 一定存在

### 前端测试

如当前仓库暂未引入前端测试框架，可至少保证：

- 手工 smoke 测试清单
- 关键交互可复现

建议验证：

- 初始渲染
- 提交成功
- 提交失败
- 继续追问

### 合规检查项

- 搜索输出文案是否含“保证”“稳赚”“抄底”
- 确保页面说明中使用“建议”“参考”

---

## 8. 任务卡拆分

## Task 1：Schema 与 Router

- 目标：新增请求响应模型与接口挂载
- 涉及文件：
  - `apps/api/src/schemas/student_payment.py`
  - `apps/api/src/routers/student_payment_advice.py`
  - `apps/api/src/routers/__init__.py`
- 验收：
  - 接口路由可访问
  - request 校验生效

## Task 2：规则服务

- 目标：实现建议引擎
- 涉及文件：
  - `apps/api/src/services/student_payment_advice_service.py`
- 验收：
  - 可输出 `decision`
  - 可输出 `market_snapshot`
  - 可输出 fallback 文本

## Task 3：Kimi 客户端增强

- 目标：新增留学生缴费专用 AI 生成方法
- 涉及文件：
  - `apps/api/src/clients/kimi_client.py`
- 验收：
  - AI 与 fallback 都可工作
  - 输出追加 disclaimer

## Task 4：后端测试

- 目标：补齐接口和规则测试
- 涉及文件：
  - `apps/api/tests/test_student_payment_advice.py`
- 验收：
  - 关键路径测试通过

## Task 5：前端模块集成

- 目标：在 AI 页面加入结构化助手
- 涉及文件：
  - `apps/web/app/assistant/page.tsx`
  - `apps/web/components/student-payment-advisor-card.tsx`
- 验收：
  - 可提交
  - 可展示结果
  - 不影响原聊天

## Task 6：联动聊天

- 目标：结果可带入聊天上下文
- 涉及文件：
  - `apps/web/app/assistant/page.tsx`
- 验收：
  - 点击按钮后输入框填充摘要

---

## 9. 建议实现细节

### 9.1 响应生成顺序

建议服务层按以下顺序组织：

1. 解析输入
2. 计算 `days_to_deadline`
3. 获取实时汇率
4. 获取 30d/90d stats
5. 计算 `rate_assessment`
6. 计算 `deadline_pressure`
7. 计算 `decision_level`
8. 生成 `split_payment_plan`
9. 构造 fallback 文案
10. 调用 Kimi 增强
11. 返回 payload

### 9.2 分位解释方向

由于用户通常关心“用人民币买美元/港币是否划算”，前端展示文案必须清楚描述：

- 当前是从哪个方向看汇率
- “偏低”到底对缴费者意味着什么

建议统一解释为：

- 当目标是 `USD/HKD` 且来源是 `CNY` 时，目标外币价格更低通常更有利于缴费

### 9.3 结果卡片优先级

不要一上来塞太多指标。

首屏只露出：

- 建议
- 当前汇率是否偏低
- 最晚执行建议

再用折叠或次级区块展示：

- 30d 分位
- 90d 分位
- 24h 变化
- 详细说明

---

## 10. 风险控制

### 技术风险

- 现有 `SettlementService` 与新服务边界重叠
- 解决方式：新服务独立，后期再考虑抽公共函数

### 产品风险

- 用户误以为系统能预测具体未来价格
- 解决方式：结果页明确写“参考建议”

### 体验风险

- 如果结果太长，用户读不完
- 解决方式：首屏结构化，长文折叠

---

## 11. Definition of Done

一个阶段只有同时满足以下条件才算完成：

- 代码已落地
- 本地服务可运行
- 关键路径可人工验证
- 后端测试通过
- fallback 正常
- disclaimer 存在
- 文案通过合规检查

---

## 12. 推荐执行顺序

建议按以下顺序开发：

1. 后端 schema/router
2. 后端规则 service
3. Kimi client 专用增强
4. 后端测试
5. 前端结构化模块
6. 聊天联动
7. 手工回归与文案校对

---

## 13. 首条 AI Coding 指令建议

如果进入开发，建议第一条实施指令是：

> 在现有 SmartFX 代码库中，为 AI 助手页新增“留学生缴费助手”能力。先从后端开始，新增 `POST /api/ai/student-payment-advice`，实现结构化 request/response schema、规则化建议引擎和 fallback 文案；只支持 `USD/HKD/CNY`，输出必须包含 `decision`、`rate_assessment`、`deadline_pressure` 和统一 disclaimer，并为该接口补充测试。
