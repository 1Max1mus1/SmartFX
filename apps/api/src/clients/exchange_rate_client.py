import httpx

from src.settings import SETTINGS


class ExchangeRateClient:
    async def latest(self, base_currency: str) -> dict:
        url = (
            f"{SETTINGS.RATE.EXCHANGE_RATE_API_URL}/"
            f"{SETTINGS.RATE.EXCHANGE_RATE_API_KEY}/latest/{base_currency}"
        )
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

