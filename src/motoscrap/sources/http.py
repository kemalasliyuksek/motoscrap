from __future__ import annotations

import asyncio
import logging

import httpx

from motoscrap.config import get_settings

logger = logging.getLogger(__name__)


class RateLimitedClient:
    """Async HTTPX wrapper that enforces a minimum interval between requests."""

    def __init__(
        self,
        *,
        user_agent: str | None = None,
        rate_per_sec: float | None = None,
        timeout: float | None = None,
    ) -> None:
        settings = get_settings()
        self._interval = 1.0 / (rate_per_sec or settings.http_rate_limit_per_sec)
        self._lock = asyncio.Lock()
        self._last: float = 0.0
        self._client = httpx.AsyncClient(
            timeout=timeout or settings.http_timeout_seconds,
            headers={"User-Agent": user_agent or settings.http_user_agent},
            follow_redirects=True,
        )

    async def get(self, url: str) -> httpx.Response:
        async with self._lock:
            wait = self._interval - (asyncio.get_event_loop().time() - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = asyncio.get_event_loop().time()
        logger.debug("GET %s", url)
        response = await self._client.get(url)
        response.raise_for_status()
        return response

    async def aclose(self) -> None:
        await self._client.aclose()
