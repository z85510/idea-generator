import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


API_SECRET_KEY_ENV = "API_SECRET_KEY"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(api_key_header)) -> None:
    expected_api_key = os.getenv(API_SECRET_KEY_ENV)
    if not expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{API_SECRET_KEY_ENV} is not configured.",
        )

    if api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )