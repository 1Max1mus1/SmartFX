import math
from datetime import UTC, date, datetime, timedelta

from src.clients.exchange_rate_client import ExchangeRateClient
from src.logger.log_handler import get_logger
from src.schemas.format import ResponseFormatter
from src.schemas.rates import RateHistoryPayload, RateHistoryPoint, RateQuote, RateStatsPayload
from src.services.cache import CACHE
from src.settings import SETTINGS

logger = get_logger(__name__)

RESPONSE = ResponseFormatter(prefix="[RateService]")
SUPPORTED_PAIRS = ("USD/CNY", "HKD/CNY", "USD/HKD")
BASE_RATES = {
    "USD/CNY": 7.18,
    "HKD/CNY": 0.918,
    "USD/HKD": 7.82,
}


def _validate_pair(pair: str) -> str:
    normalized = pair.upper()
    if normalized not in SUPPORTED_PAIRS:
        raise ValueError(f"unsupported pair: {pair}")
    return normalized


def _validate_days(days: int) -> int:
    if days not in {7, 30, 60, 90, 365}:
        raise ValueError(f"unsupported days window: {days}")
    return days


def _seed(pair: str) -> float:
    return float(sum(ord(char) for char in pair))


def _series(pair: str, days: int) -> list[RateHistoryPoint]:
    base_rate = BASE_RATES[pair]
    seed = _seed(pair)
    end_day = date.today()
    points: list[RateHistoryPoint] = []
    for index in range(days):
        day = end_day - timedelta(days=days - index - 1)
        wave = math.sin((index + seed) / 9.5) * 0.018
        drift = math.cos((index + seed) / 13.0) * 0.007
        trend = ((index / max(days, 1)) - 0.5) * 0.012
        rate = round(base_rate * (1 + wave + drift + trend), 4)
        points.append(RateHistoryPoint(day=day, rate=max(rate, 0.0001)))
    return points


def _percentile(current: float, values: list[float]) -> float:
    if not values:
        return 0.0
    below = sum(1 for value in values if value <= current)
    return round((below / len(values)) * 100, 2)


def get_conversion_rate(from_currency: str, to_currency: str) -> float:
    base = from_currency.upper()
    quote = to_currency.upper()
    if base == quote:
        return 1.0

    direct_key = f"{base}/{quote}"
    inverse_key = f"{quote}/{base}"
    if direct_key in BASE_RATES:
        return BASE_RATES[direct_key]
    if inverse_key in BASE_RATES:
        return round(1 / BASE_RATES[inverse_key], 6)

    if base == "HKD" and quote == "USD":
        return round(1 / BASE_RATES["USD/HKD"], 6)
    if base == "CNY" and quote == "USD":
        return round(1 / BASE_RATES["USD/CNY"], 6)
    if base == "CNY" and quote == "HKD":
        return round(1 / BASE_RATES["HKD/CNY"], 6)

    via_usd = None
    if base != "USD" and quote != "USD":
        base_to_usd = get_conversion_rate(base, "USD")
        usd_to_quote = get_conversion_rate("USD", quote)
        via_usd = round(base_to_usd * usd_to_quote, 6)

    if via_usd is not None:
        return via_usd

    raise ValueError(f"unsupported conversion pair: {from_currency}/{to_currency}")


def get_rate_series(pair: str, days: int) -> list[RateHistoryPoint]:
    normalized_pair = _validate_pair(pair)
    if days <= 0:
        raise ValueError("days must be positive")
    return _series(normalized_pair, days)


def _pair_map_from_provider_payload(payload: dict) -> tuple[dict[str, float], datetime]:
    conversion_rates = payload.get("conversion_rates") or {}
    usd_cny = round(float(conversion_rates["CNY"]), 4)
    usd_hkd = round(float(conversion_rates["HKD"]), 4)
    hkd_cny = round(usd_cny / usd_hkd, 4)
    updated_at = datetime.now(UTC)
    return (
        {
            "USD/CNY": usd_cny,
            "USD/HKD": usd_hkd,
            "HKD/CNY": hkd_cny,
        },
        updated_at,
    )


class RateService:
    @staticmethod
    async def _get_live_pair_map() -> tuple[dict[str, float], datetime]:
        if SETTINGS.RATE.PROVIDER == "mock":
            updated_at = datetime.now(UTC)
            return {pair: _series(pair, 2)[-1].rate for pair in SUPPORTED_PAIRS}, updated_at

        payload = await ExchangeRateClient().latest("USD")
        return _pair_map_from_provider_payload(payload)

    @staticmethod
    async def get_live_rates() -> tuple[dict, object]:
        cache_key = "rates:live"
        cached = CACHE.get(cache_key)
        if cached:
            return cached, RESPONSE.ok("live rates cached")

        try:
            pair_map, updated_at = await RateService._get_live_pair_map()
        except Exception:
            logger.exception("live rate provider request failed, falling back to synthetic quotes")
            pair_map = {pair: _series(pair, 2)[-1].rate for pair in SUPPORTED_PAIRS}
            updated_at = datetime.now(UTC)

        pairs: list[RateQuote] = []
        for pair in SUPPORTED_PAIRS:
            previous = _series(pair, 2)[-2].rate
            current = pair_map[pair]
            change_pct = round(((current - previous) / previous) * 100, 4)
            pairs.append(
                RateQuote(
                    pair=pair,
                    rate=current,
                    change_pct_24h=change_pct,
                    updated_at=updated_at,
                    source=SETTINGS.RATE.PROVIDER,
                )
            )

        payload = {
            "updated_at": updated_at.isoformat(),
            "pairs": [pair.model_dump(mode="json") for pair in pairs],
        }
        CACHE.set(cache_key, payload, SETTINGS.RATE.CACHE_TTL_SECONDS)
        return payload, RESPONSE.ok("live rates ready")

    @staticmethod
    async def get_history(pair: str, days: int) -> tuple[dict, object]:
        try:
            normalized_pair = _validate_pair(pair)
            normalized_days = _validate_days(days)
        except ValueError as exc:
            return {}, RESPONSE.error(400, str(exc))

        try:
            pair_map, _ = await RateService._get_live_pair_map()
            BASE_RATES[normalized_pair] = pair_map[normalized_pair]
        except Exception:
            logger.exception("history base rate refresh failed, using synthetic base")

        payload_model = RateHistoryPayload(
            pair=normalized_pair,
            days=normalized_days,
            points=_series(normalized_pair, normalized_days),
        )
        return payload_model.model_dump(mode="json"), RESPONSE.ok("history ready")

    @staticmethod
    async def get_stats(pair: str, days: int) -> tuple[dict, object]:
        try:
            normalized_pair = _validate_pair(pair)
            normalized_days = _validate_days(days)
        except ValueError as exc:
            return {}, RESPONSE.error(400, str(exc))

        try:
            pair_map, _ = await RateService._get_live_pair_map()
            BASE_RATES[normalized_pair] = pair_map[normalized_pair]
        except Exception:
            logger.exception("stats base rate refresh failed, using synthetic base")

        history = _series(normalized_pair, normalized_days)
        rates = [point.rate for point in history]
        current = rates[-1]
        previous = rates[-2]
        payload_model = RateStatsPayload(
            pair=normalized_pair,
            days=normalized_days,
            current=current,
            high=max(rates),
            low=min(rates),
            average=round(sum(rates) / len(rates), 4),
            percentile=_percentile(current, rates),
            change_pct_24h=round(((current - previous) / previous) * 100, 4),
        )
        return payload_model.model_dump(mode="json"), RESPONSE.ok("stats ready")
