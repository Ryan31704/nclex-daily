import uuid
from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.schemas.auth import AuthenticatedUser

bearer_scheme = HTTPBearer(auto_error=False)


class SupabaseTokenValidator:
    """Validate access tokens with Supabase Auth without using privileged keys."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._supabase_url = settings.normalized_supabase_url
        self._publishable_key = settings.supabase_publishable_key
        self._transport = transport

    async def validate(self, token: str) -> AuthenticatedUser:
        if not self._supabase_url or not self._publishable_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication is not configured on the server.",
            )

        try:
            async with httpx.AsyncClient(
                timeout=8.0,
                transport=self._transport,
            ) as client:
                response = await client.get(
                    f"{self._supabase_url}/auth/v1/user",
                    headers={
                        "apikey": self._publishable_key,
                        "Authorization": f"Bearer {token}",
                    },
                )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service is temporarily unavailable.",
            ) from exc

        if response.status_code != status.HTTP_200_OK:
            raise _invalid_credentials()

        try:
            payload = response.json()
            auth_user_id = uuid.UUID(payload["id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise _invalid_credentials() from exc

        metadata = payload.get("user_metadata")
        return AuthenticatedUser(
            id=auth_user_id,
            email=payload.get("email"),
            user_metadata=metadata if isinstance(metadata, dict) else {},
        )


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


@lru_cache
def get_token_validator() -> SupabaseTokenValidator:
    return SupabaseTokenValidator(get_settings())


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    validator: SupabaseTokenValidator = Depends(get_token_validator),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _invalid_credentials()

    return await validator.validate(credentials.credentials)
