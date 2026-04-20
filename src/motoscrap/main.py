from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from motoscrap import __version__
from motoscrap.api import catalog, refresh, sources
from motoscrap.config import get_settings

settings = get_settings()
logging.basicConfig(
    level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

app = FastAPI(
    title="motoscrap",
    version=__version__,
    description="Self-hostable motorcycle catalog scraper.",
    default_response_class=ORJSONResponse,
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


app.include_router(sources.router)
app.include_router(catalog.router)
app.include_router(refresh.router)
