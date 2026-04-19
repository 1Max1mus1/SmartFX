# SmartFX

SmartFX 是一个桌面网页优先的 AI 外汇参考平台，面向有跨境收款、换汇、结算判断需求的用户，提供实时汇率、AI 简报、AI 对话、专业版结算分析与结算报告等能力。

当前项目采用前后端分离结构：

- 前端：`Next.js 15` + `React 19` + `TypeScript` + `Tailwind CSS`
- 后端：`FastAPI` + `SQLAlchemy 2` + `Pydantic Settings`
- 数据库：`Supabase PostgreSQL`
- 汇率数据：`ExchangeRate API`
- AI 能力：`Moonshot / Kimi`

## 核心功能

- 实时汇率、历史汇率、统计区间分析
- AI 每日外汇简报
- AI 对话助手
- 专业版结算计算器
- 专业版结算报告
- 回测能力页面
- 半自动规则与提醒历史
- 健康检查、请求追踪、CI 检查脚本

## 当前体验说明

- 网站为桌面网页布局，不是手机页或小程序壳。
- 登录与注册当前为演示模式，不校验真实数据库账号密码，便于直接体验 AI 简报、AI 对话和专业版能力。
- 演示身份默认开放专业版能力。

## 项目结构

```text
SmartFX/
├─ apps/
│  ├─ api/                     # FastAPI 后端
│  └─ web/                     # Next.js 前端
├─ docs/                       # 上线与交付文档
├─ scripts/                    # 仓库级检查脚本
├─ .github/workflows/ci.yml    # GitHub Actions CI
├─ SmartFX_PRD_v1.1.md
└─ SmartFX_AI_Coding_Plan_Harness_Engineer.md
```

## 本地运行

### 1. 启动后端

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8010
```

后端默认访问地址：

- `http://127.0.0.1:8010`
- 健康检查：`http://127.0.0.1:8010/api/health`

### 2. 启动前端

```powershell
cd apps/web
npm install
Copy-Item .env.example .env.local
npm run dev -- --hostname 127.0.0.1 --port 3100
```

前端默认访问地址：

- `http://127.0.0.1:3100`

## 环境变量

后端请配置 `apps/api/.env`：

- `DB_URL`：Supabase PostgreSQL 连接串
- `RATE_PROVIDER` / `RATE_EXCHANGE_RATE_API_KEY`
- `AI_PROVIDER` / `AI_API_KEY` / `AI_BASE_URL`
- `APP_SECRET_KEY`

前端请配置 `apps/web/.env.local`：

- `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8010/api`

注意：

- `.env` 已被 `.gitignore` 忽略，不会被提交到仓库。
- 提交代码时建议只保留 `.env.example` 作为模板，不要上传真实密钥。

## 常用页面

- 首页：`/`
- AI 简报：`/report`
- AI 对话：`/assistant`
- 专业版结算计算器：`/pro/settlement`
- 专业版结算报告：`/pro/report`

## 检查脚本

仓库级检查：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_phase7_checks.ps1
```

API 侧检查：

```powershell
cd apps/api
powershell -ExecutionPolicy Bypass -File .\scripts\run_phase7_checks.ps1
```

## API 健康接口

- `GET /api/health`
- `GET /api/health/live`
- `GET /api/health/ready`

所有 API 响应都会附带：

- `x-request-id`
- `x-process-time-ms`

## CI

GitHub Actions 已配置在 `.github/workflows/ci.yml`，会执行仓库级检查流程，用于基础构建与回归验证。

## 后续可扩展方向

- 接入真实用户鉴权而不是演示登录
- 扩展更多外汇对与结算场景
- 强化 AI 报告模板与风控说明
- 接入真实通知渠道
- 部署正式生产环境
