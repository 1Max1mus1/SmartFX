from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Header, HTTPException

from src.settings import SETTINGS


def hash_password(password: str, salt: str | None = None) -> str:
    password_salt = salt or secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        password_salt.encode("utf-8"),
        200_000,
    )
    return f"{password_salt}${base64.urlsafe_b64encode(derived).decode('utf-8')}"


def verify_password(password: str, password_hash: str) -> bool:
    salt, _ = password_hash.split("$", maxsplit=1)
    candidate = hash_password(password, salt=salt)
    return hmac.compare_digest(candidate, password_hash)


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=SETTINGS.APP.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "exp": int(expires_at.timestamp()),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_token = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    signature = hmac.new(
        SETTINGS.APP.SECRET_KEY.encode("utf-8"),
        payload_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    signature_token = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    return f"{payload_token}.{signature_token}"


def decode_access_token(token: str) -> dict:
    try:
        payload_token, signature_token = token.split(".", maxsplit=1)
    except ValueError as exc:
        raise ValueError("invalid token format") from exc

    expected_signature = hmac.new(
        SETTINGS.APP.SECRET_KEY.encode("utf-8"),
        payload_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    expected_signature_token = base64.urlsafe_b64encode(expected_signature).decode("utf-8").rstrip("=")
    if not hmac.compare_digest(signature_token, expected_signature_token):
        raise ValueError("invalid token signature")

    padded_payload = payload_token + "=" * (-len(payload_token) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded_payload.encode("utf-8")).decode("utf-8"))
    if payload["exp"] < int(datetime.now(UTC).timestamp()):
        raise ValueError("token expired")
    return payload


def extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise ValueError("missing authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ValueError("invalid authorization header")
    return token


async def bearer_token_header(authorization: str | None = Header(default=None)) -> str:
    try:
        return extract_bearer_token(authorization)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
