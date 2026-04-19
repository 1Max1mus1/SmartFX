# FastAPI 异步微服务 — 通用架构模板

> 从 `task-api` 项目提炼，适用于：**Python + FastAPI + MongoDB + 异步后台任务** 类型的微服务。
> 下次 AI coding 时，直接把底部的「快速启动 Prompt」发给 AI。

---

## 目录骨架

```
{project-name}/
├── src/
│   ├── main.py               # uvicorn 启动入口
│   ├── application.py        # FastAPI 实例 + lifespan 生命周期
│   ├── settings.py           # Pydantic Settings 多级配置
│   ├── utils.py              # 工具函数（外部服务调用等）
│   ├── routers/
│   │   ├── __init__.py       # 聚合所有 router，统一注册
│   │   ├── health.py         # 健康检查路由
│   │   └── {feature}.py      # 按业务功能拆分路由
│   ├── services/
│   │   ├── health.py         # 健康检查服务
│   │   ├── {feature}.py      # 核心业务逻辑
│   │   └── {db}_cnt.py       # 数据库连接管理（单例）
│   ├── schemas/
│   │   ├── format.py         # 通用 Response 模型 + ResponseFormatter
│   │   ├── {feature}.py      # 业务 Pydantic 模型
│   │   └── {db}_doc.py       # MongoEngine / ORM 文档定义
│   ├── logger/
│   │   └── log_handler.py    # get_logger() 工厂函数
│   └── config/
│       └── settings.env      # 环境变量配置文件
├── .github/workflows/
│   ├── dev.yml
│   ├── uat.yml
│   └── prd.yml
├── Dockerfile
└── requirements.txt
```

---

## 代码模板

### `src/main.py`
```python
import uvicorn
from src.application import app
from src.settings import SETTINGS

if __name__ == "__main__":
    uvicorn.run("src.main:app", host=SETTINGS.BASE.HOST, port=SETTINGS.BASE.PORT, reload=False)
```

---

### `src/application.py`
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import router
from src.settings import SETTINGS
from src.services.mongodb_cnt import init_mongodb_cnt, close_mongodb_cnt

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_mongodb_cnt()      # 启动：建立 DB 连接
    # 可在此预热模型、下载资源
    yield
    close_mongodb_cnt()     # 关闭：优雅断开

app = FastAPI(title=SETTINGS.BASE.NAME, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
app.include_router(router, prefix=SETTINGS.BASE.ENDPOINT_PREFIX)
```

---

### `src/settings.py`（多级配置）
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import os

SETTING_FILE = "src/config/settings.env"

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=SETTING_FILE, env_prefix="APP_")
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    NAME: str = "my-service"
    ENDPOINT_PREFIX: str = ""
    PRODUCTION: bool = False

class MongoSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=SETTING_FILE, env_prefix="MONGO_")
    HOST: str = "localhost"
    PORT: int = 27017
    DB: str = "mydb"
    USER: str = ""
    PASSWORD: str = ""

    @field_validator("PASSWORD", mode="before")
    @classmethod
    def load_secret(cls, v):
        # 生产：从 /etc/secrets/ 读取；开发：从 env var 读取
        path = "/etc/secrets/mongo"
        return open(path).read().strip() if os.path.exists(path) else v

class Config:
    BASE = AppSettings()
    MONGO = MongoSettings()
    # 按需添加 AzureStorageSettings、LogSettings 等

SETTINGS = Config()
```

---

### `src/schemas/format.py`（统一响应格式）
```python
from pydantic import BaseModel
from fastapi import HTTPException

class Response(BaseModel):
    status_code: int
    detail: str

class ResponseFormatter(BaseModel):
    prefix: str = ""

    def ok(self, detail: str = "success") -> Response:
        return Response(status_code=200, detail=f"{self.prefix} {detail}")

    def error(self, code: int, detail: str) -> Response:
        return Response(status_code=code, detail=f"{self.prefix} {detail}")

def router_response_handler(response: Response):
    if response.status_code >= 300:
        raise HTTPException(status_code=response.status_code, detail=response.detail)
```

---

### `src/schemas/{db}_doc.py`（MongoEngine 文档定义）
```python
from mongoengine import Document, EmbeddedDocument, StringField, DateTimeField, EmbeddedDocumentField
import uuid, datetime

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class ResultInfo(EmbeddedDocument):
    res_path    = StringField()
    images_path = StringField()

class JobStatus(Document):
    job_id      = StringField(default=lambda: str(uuid.uuid4()), unique=True)
    job_status  = StringField(choices=["running", "failed", "done"], required=True)
    file_path   = StringField(required=True)
    result_info = EmbeddedDocumentField(ResultInfo)
    created_at  = DateTimeField(default=utcnow)
    updated_at  = DateTimeField(default=utcnow)
    meta        = {"collection": "job_status"}
```

---

### `src/services/{db}_cnt.py`（DB 连接管理）
```python
import mongoengine
from src.settings import SETTINGS

def init_mongodb_cnt():
    conn_str = (
        f"mongodb://{SETTINGS.MONGO.USER}:{SETTINGS.MONGO.PASSWORD}"
        f"@{SETTINGS.MONGO.HOST}:{SETTINGS.MONGO.PORT}/{SETTINGS.MONGO.DB}"
        f"?ssl=true&replicaSet=globaldb"
    )
    mongoengine.connect(host=conn_str)

def close_mongodb_cnt():
    mongoengine.disconnect()
```

---

### `src/services/{feature}.py`（服务层）
```python
import asyncio, os, shutil
from src.schemas.format import ResponseFormatter, Response
from src.logger.log_handler import get_logger

logger = get_logger(__name__)
RESPONSE = ResponseFormatter(prefix="[FeatureService]")

class FeatureService:

    @staticmethod
    async def create(request) -> tuple[dict, Response]:
        try:
            # 1. 写入 DB（初始状态 "running"）
            job_id = ...
            # 2. 派发后台异步任务，立即返回
            asyncio.get_running_loop().create_task(
                FeatureService._run_job(job_id, request)
            )
            return {"job_id": job_id}, RESPONSE.ok()
        except Exception as e:
            logger.error(e, exc_info=True)
            return {}, RESPONSE.error(500, str(e))

    @staticmethod
    async def get(job_id: str) -> tuple[dict, Response]:
        try:
            doc = JobStatus.objects(job_id=job_id).first()
            if not doc:
                return {}, RESPONSE.error(404, f"job_id {job_id} not found")
            return doc.to_dict(), RESPONSE.ok()
        except Exception as e:
            logger.error(e, exc_info=True)
            return {}, RESPONSE.error(500, str(e))

    @staticmethod
    async def _run_job(job_id: str, request):
        try:
            result = await FeatureService._process(job_id, request)
            # 更新 DB: status="done", result_info=result
        except Exception as e:
            logger.error(e, exc_info=True)
            # 更新 DB: status="failed"

    @staticmethod
    async def _process(job_id: str, request):
        tmp_dir = f"app-process/tmp-data/{job_id}"
        try:
            os.makedirs(tmp_dir, exist_ok=True)
            # ... 核心逻辑 ...
            return result
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)  # 保证清理临时文件
```

---

### `src/routers/{feature}.py`（路由层）
```python
from fastapi import APIRouter
from src.schemas.format import router_response_handler
from src.services.{feature} import FeatureService

router = APIRouter()

@router.post("/create")
async def create(request: JobRequest):
    response, res = await FeatureService.create(request)
    router_response_handler(res)
    return response

@router.get("/status")
async def get_status(job_id: str):
    response, res = await FeatureService.get(job_id)
    router_response_handler(res)
    return response
```

---

### `src/routers/__init__.py`（路由聚合）
```python
from fastapi import APIRouter
from src.routers import health, {feature}

router = APIRouter()
router.include_router(health.router)
router.include_router({feature}.router, prefix="/{feature}")
```

---

### `src/services/health.py`（健康检查）
```python
from src.schemas.format import ResponseFormatter

RESPONSE = ResponseFormatter(prefix="[HealthService]")

class HealthService:
    @staticmethod
    async def health_check():
        mongodb_ok = _check_mongodb()
        storage_ok = _check_storage()
        code = 200 if (mongodb_ok and storage_ok) else 500
        return {"status_code": code, "mongodb": mongodb_ok, "storage": storage_ok}

def _check_mongodb() -> bool:
    try:
        from src.schemas.mongo_doc import JobStatus
        JobStatus.objects.count()
        return True
    except Exception:
        return False
```

---

## 设计原则速查

| 原则 | 实现方式 |
|------|---------|
| **关注点分离** | Router → Service → Schema，禁止跨层直接调用 |
| **统一响应格式** | 所有 service 返回 `(data, Response)` tuple，路由统一拦截错误 |
| **异步任务 + 轮询** | POST 立即返回 job_id，GET 轮询状态，避免 HTTP 超时 |
| **临时文件隔离** | 每个任务独立目录 `tmp/{job_id}/`，`finally` 保证清理 |
| **配置分层** | 按资源拆分 Settings 类，secrets 从文件/env 双模式注入 |
| **DB 事务原子性** | 写操作用 `session.start_transaction()`，失败时 abort |
| **健康检查完备** | 每个外部依赖单独检查，返回具体失败组件名 |
| **生命周期管理** | lifespan 管理 DB 连接 + 模型预热，保证优雅启动/关闭 |

---

## 快速启动 Prompt（复制给 AI 使用）

```
请使用以下架构创建一个 FastAPI 异步微服务：

技术栈：Python + FastAPI + Pydantic Settings + MongoEngine + uvicorn + Docker

目录结构：
- src/main.py: uvicorn 入口
- src/application.py: FastAPI 实例 + lifespan（DB连接 + 启动预热）
- src/settings.py: Pydantic 多级配置，按资源拆分 Settings 类，支持 /etc/secrets/ 文件注入
- src/routers/: 按功能拆分路由，__init__.py 聚合注册
- src/services/: 业务逻辑，所有方法返回 tuple[data, Response]
- src/schemas/format.py: ResponseFormatter + router_response_handler
- src/schemas/{feature}.py: 请求响应 Pydantic 模型
- src/schemas/{db}_doc.py: MongoEngine 文档定义
- src/logger/log_handler.py: get_logger() 工厂函数

核心模式：
1. 耗时操作 → asyncio 后台任务 + job_id 轮询状态
2. 所有 service 方法 → 返回 (result, Response) tuple，路由层统一错误处理
3. 临时文件 → tmp/{job_id}/ 隔离，finally 块清理
4. DB 写操作 → MongoEngine session 事务
5. 健康检查 → 覆盖所有外部依赖，返回具体失败组件

业务功能：[在此描述你的具体需求]
```
