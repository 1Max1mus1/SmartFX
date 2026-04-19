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
DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"
DEMO_USER_EMAIL = "demo@smartfx.ai"


@dataclass
class DemoUser:
    id: str
    email: str
    plan: str
    created_at: datetime


DEMO_USERS: dict[str, DemoUser] = {}


def _demo_user(*, email: str = DEMO_USER_EMAIL, plan: str = "pro", created_at: datetime | None = None) -> DemoUser:
    return DemoUser(
        id=DEMO_USER_ID,
        email=email,
        plan=plan,
        created_at=created_at or datetime.now(UTC),
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
        _ = (session, password)
        if email in DEMO_USERS:
            return {}, RESPONSE.error(409, "email already registered")
        created_at = datetime.now(UTC)
        user = _demo_user(email=email, plan=plan, created_at=created_at)
        DEMO_USERS[email] = user
        payload = AuthPayload(
            access_token=create_access_token(
                DEMO_USER_ID,
                extra_claims={
                    "plan": user.plan,
                    "email": user.email,
                    "created_at": user.created_at.isoformat(),
                },
            ),
            user=_serialize_user(user),
        )
        return payload.model_dump(mode="json"), RESPONSE.ok("demo register ready")

    @staticmethod
    async def login(session: AsyncSession, email: str, password: str) -> tuple[dict, object]:
        _ = (session, email, password, hash_password)
        user = DEMO_USERS.get(email) or _demo_user(email=email, plan="pro", created_at=datetime.now(UTC))
        DEMO_USERS[email] = user
        payload = AuthPayload(
            access_token=create_access_token(
                DEMO_USER_ID,
                extra_claims={
                    "plan": user.plan,
                    "email": user.email,
                    "created_at": user.created_at.isoformat(),
                },
            ),
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
        created_at = payload.get("created_at")
        demo_created_at = None
        if isinstance(created_at, str):
            try:
                demo_created_at = datetime.fromisoformat(created_at)
            except ValueError:
                demo_created_at = None
        return _demo_user(
            email=payload.get("email", DEMO_USER_EMAIL),
            plan=payload.get("plan", "pro"),
            created_at=demo_created_at,
        )

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
