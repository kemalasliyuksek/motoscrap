from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from motoscrap import models
from motoscrap.sources import registry
from motoscrap.sources.base import BaseSource, BrandDTO, ModelDTO

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    cleaned = "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned


async def _upsert_source(session: AsyncSession, source_cls: type[BaseSource]) -> models.Source:
    stmt = select(models.Source).where(models.Source.slug == source_cls.slug)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        return existing
    row = models.Source(
        slug=source_cls.slug, name=source_cls.name, base_url=source_cls.base_url, is_active=True
    )
    session.add(row)
    await session.flush()
    return row


async def _upsert_brand(
    session: AsyncSession, source_row: models.Source, brand: BrandDTO
) -> models.Brand:
    stmt = select(models.Brand).where(
        models.Brand.source_id == source_row.id, models.Brand.external_id == brand.external_id
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        existing.name = brand.name
        existing.slug = brand.slug
        return existing
    row = models.Brand(
        source_id=source_row.id,
        external_id=brand.external_id,
        name=brand.name,
        slug=brand.slug,
    )
    session.add(row)
    await session.flush()
    return row


async def _upsert_model(
    session: AsyncSession,
    source_row: models.Source,
    brand_row: models.Brand,
    model: ModelDTO,
) -> models.Model:
    stmt = select(models.Model).where(
        models.Model.source_id == source_row.id, models.Model.external_id == model.external_id
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        existing.brand_id = brand_row.id
        existing.name = model.name
        existing.slug = model.slug
        existing.source_url = model.source_url
        return existing
    row = models.Model(
        source_id=source_row.id,
        brand_id=brand_row.id,
        external_id=model.external_id,
        name=model.name,
        slug=model.slug,
        source_url=model.source_url,
    )
    session.add(row)
    await session.flush()
    return row


async def _upsert_model_year(
    session: AsyncSession,
    model_row: models.Model,
    year: int,
    display_name: str,
    specs: dict[str, Any],
    raw_specs: dict[str, Any],
) -> None:
    stmt = insert(models.ModelYear).values(
        model_id=model_row.id,
        year=year,
        display_name=display_name,
        specs=specs,
        raw_specs=raw_specs,
        scraped_at=datetime.now(UTC),
    )
    stmt = stmt.on_conflict_do_update(
        constraint="uq_model_year",
        set_={
            "display_name": stmt.excluded.display_name,
            "specs": stmt.excluded.specs,
            "raw_specs": stmt.excluded.raw_specs,
            "scraped_at": stmt.excluded.scraped_at,
        },
    )
    await session.execute(stmt)


async def scrape_model(
    session: AsyncSession,
    source_slug: str,
    model_external_id: str,
    model_slug: str | None = None,
) -> dict[str, Any]:
    """Scrape all available years of a single model and persist them."""
    source_cls = registry.get(source_slug)
    source: BaseSource = source_cls()
    try:
        from motoscrap.sources.onethousandps.source import OneThousandPSSource

        if not isinstance(source, OneThousandPSSource):
            raise NotImplementedError(
                f"scrape_model currently only supports 1000ps, got {source_slug}"
            )

        if model_slug is None:
            meta = await source.fetch_model_metadata(model_external_id, slug="_")
        else:
            meta = await source.fetch_model_metadata(model_external_id, slug=model_slug)

        brand_external_id = str(meta["brand_id"])
        brand_name = str(meta["brand_name"])
        resolved_model_name = str(meta["model_name"])
        resolved_model_slug = model_slug or slugify(resolved_model_name)
        raw_years = meta["existing_model_years"]
        years: list[int] = [int(y) for y in raw_years] if isinstance(raw_years, list) else []

        from motoscrap.sources.onethousandps.urls import model_url

        source_url = model_url(model_external_id, resolved_model_slug)

        brand_dto = BrandDTO(
            external_id=brand_external_id, name=brand_name, slug=slugify(brand_name)
        )
        model_dto = ModelDTO(
            external_id=model_external_id,
            brand=brand_dto,
            name=resolved_model_name,
            slug=resolved_model_slug,
            source_url=source_url,
        )

        source_row = await _upsert_source(session, source_cls)
        brand_row = await _upsert_brand(session, source_row, brand_dto)
        model_row = await _upsert_model(session, source_row, brand_row, model_dto)

        scraped_years: list[int] = []
        errors: list[dict[str, Any]] = []
        for year in years:
            try:
                specs = await source.fetch_specs(model_dto, year)
                await _upsert_model_year(
                    session,
                    model_row,
                    year=specs.year,
                    display_name=specs.display_name,
                    specs=specs.grouped,
                    raw_specs=specs.raw,
                )
                scraped_years.append(specs.year)
            except Exception as exc:
                logger.exception("Failed to scrape year %s for model %s", year, model_external_id)
                errors.append({"year": year, "error": str(exc)})

        await session.commit()
        return {
            "source": source_slug,
            "brand": brand_name,
            "model": resolved_model_name,
            "model_id": model_row.id,
            "years_scraped": scraped_years,
            "errors": errors,
        }
    finally:
        await source.aclose()


async def run_refresh_task(
    session: AsyncSession,
    task_id: str,
    source_slug: str,
    scope: str,
    params: dict[str, Any],
) -> None:
    task_stmt = select(models.Task).where(models.Task.id == task_id)
    task = (await session.execute(task_stmt)).scalar_one()
    task.status = "running"
    task.started_at = datetime.now(UTC)
    await session.commit()

    try:
        if scope == "model":
            external_id = params["model_external_id"]
            slug = params.get("model_slug")
            result = await scrape_model(session, source_slug, external_id, slug)
        else:
            raise NotImplementedError(f"scope {scope!r} not implemented yet")

        task.status = "succeeded"
        task.result = result
    except Exception as exc:
        logger.exception("Task %s failed", task_id)
        task.status = "failed"
        task.error = str(exc)[:2000]
    finally:
        task.finished_at = datetime.now(UTC)
        await session.commit()


def new_task_id() -> str:
    return str(uuid.uuid4())
