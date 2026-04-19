from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.schemas.auth import AuthPayload, UserPayload
from src.schemas.format import ResponseFormatter
from src.services.db import get_db_session
from src.services.security import bearer_token_header, create_access_token, decode_access_token, hash_password

RESPONSE = ResponseFormatter(prefix="[AuthService]")
DEMO_USER_ID = "demo-user"
DEMO_USER_EMAIL = "demo@smartfx.ai"


@dataclass
class DemoUser:
    id: str
    email: str
    plan: str
    created_at: datetime


def _demo_user() -> DemoUser:
    return DemoUser(
        id=DEMO_USER_ID,
        email=DEMO_USER_EMAIL,
        plan="pro",
        created_at=datetime.now(UTC),
    )


def _serialize_user(user: User | DemoUser) -> UserPayload:
    return UserPayload(
        id=user.id,
        email=user.email,
        plan=user.plan,
        created_at=user.created_at,
    )


class AuthService:
    @staticmethod
    async def register(session: AsyncSession, email: str, password: str, plan: str = "free") -> tuple[dict, object]:
        _ = (session, email, password, plan)
        user = _demo_user()
        payload = AuthPayload(
            access_token=create_access_token(DEMO_USER_ID),
            user=_serialize_user(user),
        )
        return payload.model_dump(mode="json"), RESPONSE.ok("demo register ready")

    @staticmethod
    async def login(session: AsyncSession, email: str, password: str) -> tuple[dict, object]:
        _ = (session, email, password, hash_password)
        user = _demo_user()
        payload = AuthPayload(
            access_token=create_access_token(DEMO_USER_ID),
            user=_serialize_user(user),
        )
        return payload.model_dump(mode="json"), RESPONSE.ok("demo login ready")


async def get_current_user(
    token: str = Depends(bearer_token_header),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if payload["sub"] == DEMO_USER_ID:
        return _demo_user()

    user = await UserRepository.get_by_id(session, payload["sub"])
    if not user:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="user not found")
    return user


async def get_current_pro_user(user: User = Depends(get_current_user)) -> User:
    from fastapi import HTTPException

    if user.plan != "pro":
        raise HTTPException(status_code=403, detail="pro plan required")
    return user
