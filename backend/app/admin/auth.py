from __future__ import annotations

from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

from app.models import UserRecord


class SessionAdminAuth(AuthenticationBackend):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        secret_key: str,
    ) -> None:
        super().__init__(secret_key=secret_key)
        self.session_factory = session_factory

    async def login(self, request: Request) -> bool:
        return False

    async def logout(self, request: Request) -> Response | bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Response | bool:
        user_id = request.session.get("user_id")
        if not user_id:
            return PlainTextResponse(
                "Admin access requires a signed-in admin user.", status_code=403
            )

        session_factory = getattr(request.app.state, "admin_session_factory", self.session_factory)
        async with session_factory() as session:
            user = await session.get(UserRecord, user_id)

        if user is None or not user.is_admin:
            return PlainTextResponse(
                "Admin access requires a signed-in admin user.", status_code=403
            )

        return True
