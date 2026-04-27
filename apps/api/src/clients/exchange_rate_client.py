from __future__ import annotations

from datetime import date

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

    async def historical(self, base_currency: str, target_day: date) -> dict:
        url = (
            f"{SETTINGS.RATE.EXCHANGE_RATE_API_URL}/"
            f"{SETTINGS.RATE.EXCHANGE_RATE_API_KEY}/history/{base_currency}/"
            f"{target_day.year}/{target_day.month}/{target_day.day}"
        )
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def frankfurter_latest(self, base_currency: str, quotes: list[str]) -> list[dict]:
        quote_list = ",".join(quotes)
        url = f"https://api.frankfurter.dev/v2/rates?base={base_currency}&quotes={quote_list}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def frankfurter_series(
        self,
        base_currency: str,
        quote_currency: str,
        *,
        from_day: date,
        to_day: date | None = None,
    ) -> list[dict]:
        params = [
            f"base={base_currency}",
            f"quotes={quote_currency}",
            f"from={from_day.isoformat()}",
        ]
        if to_day:
            params.append(f"to={to_day.isoformat()}")

        url = f"https://api.frankfurter.dev/v2/rates?{'&'.join(params)}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
