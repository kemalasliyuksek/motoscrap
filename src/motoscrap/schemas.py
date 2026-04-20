from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    base_url: str
    is_active: bool


class BrandOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_slug: str
    external_id: str
    name: str
    slug: str


class ModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_slug: str
    brand_slug: str
    external_id: str
    name: str
    slug: str
    source_url: str


class ModelYearOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_slug: str
    brand_name: str
    model_name: str
    model_external_id: str
    year: int
    display_name: str
    specs: dict[str, Any]
    scraped_at: datetime


RefreshScope = Literal["all", "brand", "model"]


class RefreshRequest(BaseModel):
    source: str = Field(description="Source slug, e.g. '1000ps'")
    scope: RefreshScope
    brand_slug: str | None = None
    model_external_id: str | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_slug: str
    scope: str
    params: dict[str, Any]
    status: str
    result: dict[str, Any]
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
