from __future__ import annotations

from fastapi import APIRouter

from motoscrap.schemas import SourceOut
from motoscrap.sources import registry

router = APIRouter(tags=["sources"])


@router.get("/sources", response_model=list[SourceOut])
async def list_sources() -> list[SourceOut]:
    return [
        SourceOut(slug=cls.slug, name=cls.name, base_url=cls.base_url, is_active=True)
        for cls in registry.all()
    ]
