from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from motoscrap.config import get_settings
from motoscrap.db import SessionLocal


async def session_dependency() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = get_settings().api_key_normalized
    if expected is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="/refresh is disabled: set MOTOSCRAP_API_KEY to enable scraping",
        )
    if x_api_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
