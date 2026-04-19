from fastapi import APIRouter, Query

from src.schemas.format import router_response_handler
from src.services.rate_service import RateService

router = APIRouter()


@router.get("/live")
async def get_live_rates():
    payload, response = await RateService.get_live_rates()
    router_response_handler(response)
    return payload


@router.get("/history")
async def get_rate_history(
    pair: str = Query(..., description="Supported: USD/CNY, HKD/CNY, USD/HKD"),
    days: int = Query(30, description="Supported: 7, 30, 90, 365"),
):
    payload, response = await RateService.get_history(pair=pair, days=days)
    router_response_handler(response)
    return payload


@router.get("/stats")
async def get_rate_stats(
    pair: str = Query(..., description="Supported: USD/CNY, HKD/CNY, USD/HKD"),
    days: int = Query(30, description="Supported: 7, 30, 90, 365"),
):
    payload, response = await RateService.get_stats(pair=pair, days=days)
    router_response_handler(response)
    return payload

