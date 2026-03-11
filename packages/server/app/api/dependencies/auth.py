import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

_API_KEY_ENV = "API_SECRET_KEY"
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(_api_key_header)) -> None:
    expected = os.getenv(_API_KEY_ENV)
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{_API_KEY_ENV} is not configured.",
        )
    if api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

