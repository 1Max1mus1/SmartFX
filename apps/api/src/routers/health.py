from fastapi import APIRouter

from src.schemas.format import router_response_handler
from src.services.health import HealthService

router = APIRouter()


@router.get("/health")
async def health_check():
    payload, response = await HealthService.health_check()
    router_response_handler(response)
    return payload


@router.get("/health/live")
async def live_check():
    payload, response = await HealthService.liveness_check()
    router_response_handler(response)
    return payload


@router.get("/health/ready")
async def readiness_check():
    payload, response = await HealthService.readiness_check()
    router_response_handler(response)
    return payload
