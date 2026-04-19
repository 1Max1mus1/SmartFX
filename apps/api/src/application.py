from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.middleware.request_context import RequestContextMiddleware
from src.routers import router
from src.services.cache import CACHE
from src.services.db import close_database, init_database
from src.settings import SETTINGS


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_database()
    CACHE.ping()
    yield
    await close_database()


app = FastAPI(title=SETTINGS.APP.NAME, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=SETTINGS.APP.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)
app.include_router(router, prefix=SETTINGS.APP.ENDPOINT_PREFIX)
