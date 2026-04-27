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
    if days not in {2, 7, 30, 60, 90, 365}:
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


def _split_pair(pair: str) -> tuple[str, str]:
    base, quote = pair.split("/", 1)
    return base, quote


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


def _pair_map_from_frankfurter_payload(payload: list[dict]) -> tuple[dict[str, float], datetime]:
    quote_map = {item["quote"]: round(float(item["rate"]), 4) for item in payload}
    usd_cny = quote_map["CNY"]
    usd_hkd = quote_map["HKD"]
    hkd_cny = round(usd_cny / usd_hkd, 4)
    return (
        {
            "USD/CNY": usd_cny,
            "USD/HKD": usd_hkd,
            "HKD/CNY": hkd_cny,
        },
        datetime.now(UTC),
    )


def _history_points_from_frankfurter_payload(payload: list[dict], pair: str, days: int) -> list[RateHistoryPoint]:
    points = [
        RateHistoryPoint(day=date.fromisoformat(item["date"]), rate=round(float(item["rate"]), 4))
        for item in payload
        if item.get("rate") is not None
    ]
    if len(points) >= days:
        return points[-days:]
    if points:
        return points
    return _series(pair, days)


class RateService:
    @staticmethod
    async def _get_live_pair_map() -> tuple[dict[str, float], datetime, str]:
        if SETTINGS.RATE.PROVIDER == "mock":
            updated_at = datetime.now(UTC)
            pair_map = {pair: _series(pair, 2)[-1].rate for pair in SUPPORTED_PAIRS}
            return pair_map, updated_at, "mock"

        try:
            payload = await ExchangeRateClient().latest("USD")
            pair_map, updated_at = _pair_map_from_provider_payload(payload)
            BASE_RATES.update(pair_map)
            return pair_map, updated_at, SETTINGS.RATE.PROVIDER
        except Exception:
            logger.exception("primary live rate provider failed, falling back to Frankfurter latest rates")
            payload = await ExchangeRateClient().frankfurter_latest("USD", ["CNY", "HKD"])
            pair_map, updated_at = _pair_map_from_frankfurter_payload(payload)
            BASE_RATES.update(pair_map)
            return pair_map, updated_at, "frankfurter"

    @staticmethod
    async def get_live_conversion_rate(from_currency: str, to_currency: str) -> float:
        base = from_currency.upper()
        quote = to_currency.upper()
        if base == quote:
            return 1.0

        pair_map, _, _ = await RateService._get_live_pair_map()
        direct_key = f"{base}/{quote}"
        inverse_key = f"{quote}/{base}"
        if direct_key in pair_map:
            return pair_map[direct_key]
        if inverse_key in pair_map:
            return round(1 / pair_map[inverse_key], 6)

        if base == "CNY" and quote == "USD":
            return round(1 / pair_map["USD/CNY"], 6)
        if base == "CNY" and quote == "HKD":
            return round(1 / pair_map["HKD/CNY"], 6)
        if base == "HKD" and quote == "USD":
            return round(1 / pair_map["USD/HKD"], 6)

        via_usd = None
        if base != "USD" and quote != "USD":
            base_to_usd = await RateService.get_live_conversion_rate(base, "USD")
            usd_to_quote = await RateService.get_live_conversion_rate("USD", quote)
            via_usd = round(base_to_usd * usd_to_quote, 6)

        if via_usd is not None:
            return via_usd

        raise ValueError(f"unsupported conversion pair: {from_currency}/{to_currency}")

    @staticmethod
    async def _get_real_history_points(pair: str, days: int) -> tuple[list[RateHistoryPoint], str]:
        normalized_pair = _validate_pair(pair)
        normalized_days = _validate_days(days)
        if SETTINGS.RATE.PROVIDER == "mock":
            return _series(normalized_pair, normalized_days), "mock"

        cache_key = f"rates:history:{normalized_pair}:{normalized_days}"
        cached = CACHE.get(cache_key)
        if cached:
            return (
                [RateHistoryPoint(day=date.fromisoformat(item["day"]), rate=item["rate"]) for item in cached["points"]],
                cached["source"],
            )

        base_currency, quote_currency = _split_pair(normalized_pair)
        from_day = date.today() - timedelta(days=normalized_days + 7)
        try:
            payload = await ExchangeRateClient().frankfurter_series(
                base_currency,
                quote_currency,
                from_day=from_day,
            )
            points = _history_points_from_frankfurter_payload(payload, normalized_pair, normalized_days)
            if points:
                BASE_RATES[normalized_pair] = points[-1].rate
                CACHE.set(
                    cache_key,
                    {
                        "points": [point.model_dump(mode="json") for point in points],
                        "source": "frankfurter",
                    },
                    SETTINGS.RATE.CACHE_TTL_SECONDS,
                )
                return points, "frankfurter"
        except Exception:
            logger.exception("historical rate provider request failed, falling back to synthetic history")

        return _series(normalized_pair, normalized_days), "synthetic-fallback"

    @staticmethod
    async def get_live_rates() -> tuple[dict, object]:
        cache_key = "rates:live"
        cached = CACHE.get(cache_key)
        if cached:
            return cached, RESPONSE.ok("live rates cached")

        try:
            pair_map, updated_at, source = await RateService._get_live_pair_map()
        except Exception:
            logger.exception("live rate provider request failed, falling back to synthetic quotes")
            pair_map = {pair: _series(pair, 2)[-1].rate for pair in SUPPORTED_PAIRS}
            updated_at = datetime.now(UTC)
            source = "synthetic-fallback"

        pairs: list[RateQuote] = []
        for pair in SUPPORTED_PAIRS:
            history_points, _ = await RateService._get_real_history_points(pair, 2)
            previous = history_points[-2].rate if len(history_points) >= 2 else pair_map[pair]
            current = pair_map[pair]
            change_pct = round(((current - previous) / previous) * 100, 4) if previous else 0.0
            pairs.append(
                RateQuote(
                    pair=pair,
                    rate=current,
                    change_pct_24h=change_pct,
                    updated_at=updated_at,
                    source=source,
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

        points, _ = await RateService._get_real_history_points(normalized_pair, normalized_days)
        payload_model = RateHistoryPayload(
            pair=normalized_pair,
            days=normalized_days,
            points=points,
        )
        return payload_model.model_dump(mode="json"), RESPONSE.ok("history ready")

    @staticmethod
    async def get_stats(pair: str, days: int) -> tuple[dict, object]:
        try:
            normalized_pair = _validate_pair(pair)
            normalized_days = _validate_days(days)
        except ValueError as exc:
            return {}, RESPONSE.error(400, str(exc))

        history, source = await RateService._get_real_history_points(normalized_pair, normalized_days)
        rates = [point.rate for point in history]
        current = rates[-1]
        previous = rates[-2] if len(rates) >= 2 else current

        if source != "mock":
            try:
                pair_map, _, live_source = await RateService._get_live_pair_map()
                current = pair_map[normalized_pair]
                rates[-1] = current
                source = live_source
            except Exception:
                logger.exception("live quote refresh failed while building stats, keeping history tail as current")

        payload_model = RateStatsPayload(
            pair=normalized_pair,
            days=normalized_days,
            current=current,
            high=max(rates),
            low=min(rates),
            average=round(sum(rates) / len(rates), 4),
            percentile=_percentile(current, rates),
            change_pct_24h=round(((current - previous) / previous) * 100, 4) if previous else 0.0,
        )
        payload = payload_model.model_dump(mode="json")
        payload["source"] = source
        return payload, RESPONSE.ok("stats ready")
