# SmartFX AI Coding Plan · Harness Engineer

## 1. 文档目标

本计划用于指导 AI Coding 以可执行、可验证、可分阶段交付的方式落地 SmartFX。

规划依据：

- `SmartFX_PRD_v1.1.md`
- `FASTAPI_ASYNC_TEMPLATE.md`
- 当前补充约束：前端只参考示例图的设计语言，不参考其手机壳、小程序栏位、移动端结构

本计划默认采用 Harness Engineer 风格：

- 先搭骨架，再逐模块填充
- 每次只做一个清晰闭环
- 每个任务都必须有输入、输出、验收标准
- 每个阶段完成后都要保持项目可运行、可测试、可继续扩展

---

## 2. 总体交付目标

SmartFX 要落地为一个 Web 形态的 AI 外汇参考平台，不是移动端壳层复刻。

核心目标分三层：

1. 普通版 MVP
   - 实时汇率
   - 历史走势
   - AI 每日简报
   - AI 对话助手
   - 换汇记录

2. 专业版能力
   - 结算计算器
   - AI 结算报告
   - 回测系统
   - 半自动决策工具 Stage 1

3. 工程质量目标
   - 后端遵循 FastAPI 异步模板的分层结构
   - 前端具备统一设计系统与响应式网页布局
   - AI 能力、定时任务、异步任务、缓存、权限、审计可持续扩展

---

## 3. AI Coding 工作原则

### 3.1 输出原则

- 优先产出能运行的代码，而不是停留在讨论
- 每次 AI 实现只覆盖一个明确模块
- 每次提交后必须说明：
  - 改了哪些文件
  - 提供了哪些能力
  - 如何验证
  - 还剩哪些未完成点

### 3.2 拆分原则

- 不做跨 4 个以上域的大爆炸式改动
- 先公共基础层，再做业务能力层
- 先只读能力，再做写入能力
- 先同步接口，再上异步任务
- 先核心路径，再做 Pro 能力

### 3.3 合规原则

- 所有 AI 输出统一带免责声明
- 文案使用“参考信号”“参考方向”，避免“投资建议”“保证收益”
- 回测页面统一写“历史统计吻合率/历史假设模拟”
- 系统不得自动执行任何资金操作

---

## 4. 目标技术架构

## 4.1 前端

- 框架：Next.js 14+ App Router
- 语言：TypeScript
- 样式：Tailwind CSS
- 组件：shadcn/ui
- 图表：
  - 普通统计图：Recharts
  - 汇率趋势与 K 线：TradingView Lightweight Charts

## 4.2 后端

- 框架：FastAPI
- 语言：Python 3.11+
- 配置：Pydantic Settings
- 数据库：PostgreSQL
- 缓存：Redis
- ORM：SQLAlchemy 2.x + Alembic
- 定时任务：APScheduler
- AI：Kimi API 封装层
- 邮件：Resend

## 4.3 模板继承策略

后端严格参考 `FASTAPI_ASYNC_TEMPLATE.md` 的结构思想，但做以下适配：

- 保留 `main.py / application.py / settings.py / routers / services / schemas / logger`
- 将模板里的 Mongo 连接层改为 PostgreSQL + Redis 连接层
- 将模板里的“异步任务 + job_id 轮询”模式用于：
  - AI 结算报告生成
  - 个人回测任务
  - 历史数据回填任务

---

## 5. 推荐目录结构

```text
smartfx/
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── lib/
│   │   ├── styles/
│   │   └── hooks/
│   └── api/
│       ├── src/
│       │   ├── main.py
│       │   ├── application.py
│       │   ├── settings.py
│       │   ├── utils.py
│       │   ├── routers/
│       │   ├── services/
│       │   ├── schemas/
│       │   ├── models/
│       │   ├── repositories/
│       │   ├── clients/
│       │   ├── jobs/
│       │   ├── logger/
│       │   └── config/
│       ├── alembic/
│       ├── tests/
│       ├── requirements.txt
│       └── Dockerfile
├── packages/
│   ├── ui/
│   ├── config/
│   └── types/
└── docs/
```

说明：

- `routers` 负责 HTTP 边界
- `services` 负责业务逻辑
- `repositories` 负责数据库读写
- `clients` 负责第三方 API
- `jobs` 负责定时和后台任务
- `schemas` 负责请求响应模型
- `models` 负责 SQLAlchemy 模型

---

## 6. 后端模块蓝图

## 6.1 基础模块

- `routers/health.py`
- `services/health.py`
- `services/postgres_cnt.py`
- `services/redis_cnt.py`
- `schemas/format.py`
- `logger/log_handler.py`
- `settings.py`

## 6.2 核心业务模块

- `routers/auth.py`
- `routers/rates.py`
- `routers/report.py`
- `routers/ai_chat.py`
- `routers/records.py`
- `routers/alerts.py`
- `routers/pro_settlement.py`
- `routers/pro_backtest.py`
- `routers/auto_rules.py`

对应服务层：

- `services/auth_service.py`
- `services/rate_service.py`
- `services/history_service.py`
- `services/report_service.py`
- `services/chat_service.py`
- `services/record_service.py`
- `services/alert_service.py`
- `services/settlement_service.py`
- `services/backtest_service.py`
- `services/auto_rule_service.py`

第三方客户端：

- `clients/exchange_rate_client.py`
- `clients/pboc_client.py`
- `clients/fred_client.py`
- `clients/news_client.py`
- `clients/kimi_client.py`
- `clients/resend_client.py`

后台任务：

- `jobs/rate_sync_job.py`
- `jobs/daily_report_job.py`
- `jobs/report_backfill_job.py`
- `jobs/alert_eval_job.py`
- `jobs/policy_radar_job.py`

---

## 7. 数据模型规划

必须优先落地以下表：

- `users`
- `exchange_records`
- `daily_reports`
- `alerts`
- `backtest_cache`
- `auto_decision_rules`
- `alert_history`
- `job_runs`
- `chat_sessions`
- `chat_messages`

建议补充的工程型表：

- `rate_snapshots`
- `macro_snapshots`
- `policy_events`
- `report_jobs`
- `audit_logs`

说明：

- `daily_reports` 既是内容存储，也是回测基础数据源
- `job_runs` 用于异步任务统一状态管理
- `rate_snapshots` 用于趋势图、回测、统计计算复用
- `audit_logs` 用于专业版关键动作留痕

---

## 8. API 规划

优先按 PRD 落地以下接口。

公开接口：

- `GET /api/health`
- `GET /api/rates/live`
- `GET /api/rates/history`
- `GET /api/rates/stats`

普通版登录后接口：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/report/daily`
- `POST /api/ai/chat`
- `GET /api/records`
- `POST /api/records`
- `PATCH /api/records/{id}`
- `DELETE /api/records/{id}`

专业版接口：

- `POST /api/pro/settlement`
- `POST /api/pro/report/generate`
- `GET /api/pro/report/status/{job_id}`
- `GET /api/pro/backtest/overview`
- `POST /api/pro/backtest/personal`
- `GET /api/pro/backtest/result/{job_id}`
- `GET /api/pro/auto-rules`
- `POST /api/pro/auto-rules`
- `PATCH /api/pro/auto-rules/{id}`
- `DELETE /api/pro/auto-rules/{id}`
- `GET /api/pro/auto-rules/history`

工程约束：

- 所有 service 返回 `(data, Response)` tuple
- 所有 router 统一用 `router_response_handler`
- 所有异步任务统一返回 `job_id`

---

## 9. 前端产品结构

## 9.1 网页端页面清单

公共页面：

- 首页 Dashboard
- 汇率走势页
- AI 每日简报页
- 登录 / 注册页

登录后页面：

- 我的换汇记录
- AI 对话助手
- 账户设置

专业版页面：

- 专业仪表盘
- 结算计算器
- AI 结算报告
- 回测系统
- 半自动决策规则中心
- 预警历史页
- 政策雷达

## 9.2 页面布局原则

- 必须是网页布局，不复刻手机界面
- 使用桌面端双栏或三栏信息布局
- 保持 `1440px` 左右的最大内容宽度
- 主要信息卡片放在首屏上半区
- 趋势图与分析卡片采用网页级留白和栅格系统
- 禁止加入手机状态栏、底部 tab、小程序胶囊按钮

---

## 10. 前端视觉方向

示例图只参考设计语言，不参考终端形态。

### 10.1 视觉关键词

- 清透金融感
- 翡翠绿主背景
- 金色渐变强调卡
- 大圆角白色面板
- 轻盈、可信、非交易所式高压界面

### 10.2 建议设计 Token

- 主色：`#2FB36C`
- 深绿：`#179356`
- 浅绿雾化层：`rgba(47, 179, 108, 0.12)`
- 金色高亮：`#E7C36A`
- 金色渐变：`linear-gradient(135deg, #F8EFCF 0%, #F2D98B 100%)`
- 主背景渐变：`linear-gradient(180deg, #32B56D 0%, #27A860 100%)`
- 卡片底色：`#FFFFFF`
- 辅助灰：`#8C8C8C`
- 正文黑：`#111111`

### 10.3 组件风格

- Hero 汇率卡：白底大卡 + 金色顶栏
- 汇率币种卡：左侧旗帜或币种徽标，右侧大号数值
- 筛选器：圆角胶囊按钮，但作为网页筛选控件使用
- 图表区：白底大面板 + 顶部摘要 + 区间切换
- AI 简报模块：卡片分段展示，重点句高亮

### 10.4 字体建议

- 中文：`Noto Sans SC`
- 英文数字：`Plus Jakarta Sans`

### 10.5 动效建议

- 页面首屏卡片淡入上浮
- 数值更新做轻量滚动或渐变
- 图表切换使用 180-240ms 的平滑过渡

---

## 11. 分阶段 AI Coding 计划

## Phase 0：工程初始化

目标：

- 搭建 monorepo 或双应用仓结构
- 初始化 Web 与 API 工程
- 完成基础配置、环境变量、Lint、Format、Test、CI

输出：

- 前端可启动
- 后端可启动
- `GET /api/health` 可用

验收标准：

- 本地一键启动成功
- 前后端环境变量模板齐全
- 基础 README 可运行

## Phase 1：汇率数据底座

目标：

- 接入实时汇率与历史数据
- 建立 `rate_snapshots` 存储与缓存策略
- 实现公开查询接口

输出：

- `GET /api/rates/live`
- `GET /api/rates/history`
- `GET /api/rates/stats`
- 首页 Dashboard 第一版
- 趋势页第一版

验收标准：

- 数据可缓存 5 分钟
- 历史区间统计可正确返回高低均值与分位数
- 图表可切换 7/30/90/365 天

## Phase 2：认证与换汇记录

目标：

- 完成用户注册登录
- 完成换汇记录 CRUD
- 完成用户侧基础数据面板

输出：

- Auth 流程
- 记录列表页
- 记录新建/编辑/删除

验收标准：

- 非登录用户无法写入记录
- 用户只能读写自己的记录
- 记录页可展示参考损益

## Phase 3：AI 每日简报与 AI 对话

目标：

- 接入 Kimi API
- 实现每日简报生成与存储
- 实现基础 AI 对话助手

输出：

- `GET /api/report/daily`
- `POST /api/ai/chat`
- 每日 07:30 快照 + 08:30 简报任务

验收标准：

- 简报生成结果可持久化
- AI 输出统一追加免责声明
- 对话可保存最近上下文

## Phase 4：专业版结算计算器

目标：

- 实现专业版权限
- 实现结算计算器与 AI 分析
- 实现报告异步生成

输出：

- `POST /api/pro/settlement`
- `POST /api/pro/report/generate`
- `GET /api/pro/report/status/{job_id}`
- 结算计算器页面
- AI 报告页面

验收标准：

- 报告生成使用异步任务
- 任务状态可轮询
- 页面能展示结构化结论与风险提示

## Phase 5：回测系统

目标：

- 构建信号历史吻合率看板
- 构建个人换汇回测引擎
- 回填 7 日/14 日信号后验数据

输出：

- `GET /api/pro/backtest/overview`
- `POST /api/pro/backtest/personal`
- `GET /api/pro/backtest/result/{job_id}`
- 专业版回测页面

验收标准：

- 看板可切换 30/60/90 天
- 个人回测可返回实际均价、模拟均价、差异金额
- 页面文案只使用“历史吻合率/历史模拟”

## Phase 6：半自动决策工具 Stage 1

目标：

- 实现规则配置
- 实现触发判断
- 实现邮件通知与触发历史

输出：

- `GET /api/pro/auto-rules`
- `POST /api/pro/auto-rules`
- `PATCH /api/pro/auto-rules/{id}`
- `DELETE /api/pro/auto-rules/{id}`
- `GET /api/pro/auto-rules/history`

验收标准：

- 支持汇率条件 + AI 信号条件
- 支持静默时段与频率限制
- 只发送通知，不执行任何实际换汇

## Phase 7：稳定性与上线准备

目标：

- 增加测试覆盖
- 完成监控、日志、错误告警
- 完成部署与上线前检查

输出：

- CI/CD
- 基础监控
- 部署配置
- 上线检查清单

验收标准：

- 核心 API 有集成测试
- 关键异步任务有 smoke test
- 环境隔离明确

---

## 12. 异步任务设计

以下任务必须采用后台任务模型：

- AI 结算报告生成
- 个人回测计算
- 历史信号回填
- 周报生成

统一任务表字段建议：

- `job_id`
- `job_type`
- `job_status`
- `input_payload`
- `result_payload`
- `error_message`
- `created_at`
- `updated_at`

状态枚举：

- `pending`
- `running`
- `done`
- `failed`

---

## 13. 测试计划

单元测试：

- 汇率转换与区间统计
- 回测核心计算函数
- AI 输出后处理与免责声明追加
- 规则触发判断逻辑

集成测试：

- rates API
- records API
- report API
- pro settlement API
- pro backtest API

前端测试：

- 核心页面渲染
- 表单交互
- 权限守卫

验收测试：

- 从首页查看实时汇率
- 注册并新增换汇记录
- 查看 AI 每日简报
- 生成专业版结算报告
- 发起一次个人回测
- 创建一次半自动提醒规则

---

## 14. AI Coding 任务卡模板

后续每次交给 AI 的任务，统一按以下格式下发：

### Task Card

- 任务名称：
- 所属阶段：
- 目标：
- 输入文档：
- 涉及目录：
- 必做项：
- 非目标：
- 输出文件：
- 接口变更：
- 数据库变更：
- 验收标准：
- 验证命令：

示例：

- 任务名称：实现 `GET /api/rates/live`
- 所属阶段：Phase 1
- 目标：返回 USD/CNY、HKD/CNY、USD/HKD 最新汇率与更新时间
- 输入文档：PRD F-001、技术架构、API 规范
- 涉及目录：`routers/` `services/` `schemas/` `clients/` `tests/`
- 必做项：接第三方汇率源、Redis 缓存、响应格式统一
- 非目标：不做图表、不做登录
- 验收标准：接口 200 返回结构稳定，缓存生效，测试通过

---

## 15. 完成定义

一个模块只有同时满足以下条件才算完成：

- 代码已写入
- 路由可访问
- 基本测试通过
- 异常路径有处理
- 文案符合合规要求
- 前端已接入真实或 mock 数据
- 关键行为已写入日志

---

## 16. 当前建议的第一轮 AI Coding 顺序

建议按以下顺序逐步实施：

1. 初始化前后端工程骨架
2. 先完成 FastAPI 基础模板迁移
3. 做公开汇率接口和首页 Dashboard
4. 做历史数据和趋势图
5. 做登录与换汇记录
6. 做 AI 每日简报
7. 做 AI 对话
8. 做专业版结算计算器
9. 做回测系统
10. 做半自动决策工具 Stage 1

---

## 17. 关键约束结论

- 后端结构必须遵守 FastAPI 异步模板的分层思路
- 数据库选型以 PRD 为准，使用 PostgreSQL，不沿用模板中的 Mongo 实现
- 前端只吸收参考图的配色、卡片气质、金绿层次和留白风格
- 页面必须是桌面网页信息架构，不得写成手机页、小程序页或套壳式 H5
- 回测与半自动能力必须从一开始就按合规边界设计

---

## 18. 下一步执行建议

如果直接进入开发，建议第一条 AI 指令是：

> 按本计划创建 SmartFX 的前后端工程骨架，其中后端严格遵循 FastAPI 异步模板的分层结构，前端创建网页端 Dashboard 基础布局和设计 Token，不要生成手机端布局。

