from datetime import UTC, datetime

from src.schemas.format import ResponseFormatter
from src.services.cache import CACHE
from src.services.db import check_database
from src.settings import SETTINGS

RESPONSE = ResponseFormatter(prefix="[HealthService]")


class HealthService:
    @staticmethod
    async def health_check(include_details: bool = True) -> tuple[dict, object]:
        database_ok = await check_database()
        cache_ok = CACHE.ping()
        status_code = 200 if database_ok and cache_ok else 500
        payload = {
            "status": "ok" if status_code == 200 else "degraded",
            "app": {
                "name": SETTINGS.APP.NAME,
                "version": SETTINGS.APP.VERSION,
                "env": SETTINGS.APP.ENV,
            },
            "checked_at": datetime.now(UTC).isoformat(),
            "components": {
                "database": database_ok,
                "cache": cache_ok,
            },
        }
        if not include_details:
            payload = {"status": payload["status"]}
        response = RESPONSE.ok("healthy") if status_code == 200 else RESPONSE.error(status_code, "degraded")
        return payload, response

    @staticmethod
    async def liveness_check() -> tuple[dict, object]:
        payload = {
            "status": "ok",
            "app": {
                "name": SETTINGS.APP.NAME,
                "version": SETTINGS.APP.VERSION,
                "env": SETTINGS.APP.ENV,
            },
            "checked_at": datetime.now(UTC).isoformat(),
        }
        return payload, RESPONSE.ok("live")

    @staticmethod
    async def readiness_check() -> tuple[dict, object]:
        return await HealthService.health_check(include_details=True)
