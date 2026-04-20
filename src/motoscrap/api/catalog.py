from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from motoscrap import models
from motoscrap.api.deps import session_dependency
from motoscrap.schemas import BrandOut, ModelOut, ModelYearOut

router = APIRouter(tags=["catalog"])


async def _source_row(session: AsyncSession, slug: str) -> models.Source:
    stmt = select(models.Source).where(models.Source.slug == slug)
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Unknown source {slug!r}")
    return row


@router.get("/brands", response_model=list[BrandOut])
async def list_brands(
    source: str = Query(...),
    session: AsyncSession = Depends(session_dependency),
) -> list[BrandOut]:
    source_row = await _source_row(session, source)
    stmt = (
        select(models.Brand)
        .where(models.Brand.source_id == source_row.id)
        .order_by(models.Brand.name)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [
        BrandOut(source_slug=source, external_id=r.external_id, name=r.name, slug=r.slug)
        for r in rows
    ]


@router.get("/models", response_model=list[ModelOut])
async def list_models(
    source: str = Query(...),
    brand: str | None = Query(default=None, description="Brand slug"),
    session: AsyncSession = Depends(session_dependency),
) -> list[ModelOut]:
    source_row = await _source_row(session, source)
    stmt = (
        select(models.Model)
        .options(selectinload(models.Model.brand))
        .where(models.Model.source_id == source_row.id)
        .order_by(models.Model.name)
    )
    if brand is not None:
        stmt = stmt.join(models.Brand).where(models.Brand.slug == brand)
    rows = (await session.execute(stmt)).scalars().all()
    return [
        ModelOut(
            source_slug=source,
            brand_slug=r.brand.slug,
            external_id=r.external_id,
            name=r.name,
            slug=r.slug,
            source_url=r.source_url,
        )
        for r in rows
    ]


@router.get("/model-years", response_model=list[ModelYearOut])
async def list_model_years(
    source: str = Query(...),
    model_external_id: str = Query(...),
    session: AsyncSession = Depends(session_dependency),
) -> list[ModelYearOut]:
    source_row = await _source_row(session, source)
    stmt = (
        select(models.ModelYear)
        .join(models.Model)
        .options(selectinload(models.ModelYear.model).selectinload(models.Model.brand))
        .where(
            models.Model.source_id == source_row.id,
            models.Model.external_id == model_external_id,
        )
        .order_by(models.ModelYear.year)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [_to_year_out(source, r) for r in rows]


@router.get("/specs", response_model=ModelYearOut)
async def get_specs(
    source: str = Query(...),
    model_external_id: str = Query(...),
    year: int = Query(...),
    session: AsyncSession = Depends(session_dependency),
) -> ModelYearOut:
    source_row = await _source_row(session, source)
    stmt = (
        select(models.ModelYear)
        .join(models.Model)
        .options(selectinload(models.ModelYear.model).selectinload(models.Model.brand))
        .where(
            models.Model.source_id == source_row.id,
            models.Model.external_id == model_external_id,
            models.ModelYear.year == year,
        )
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Specs not found. Try POST /refresh first.")
    return _to_year_out(source, row)


@router.get("/search", response_model=list[ModelOut])
async def search_models(
    q: str = Query(..., min_length=2),
    source: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    session: AsyncSession = Depends(session_dependency),
) -> list[ModelOut]:
    pattern = f"%{q.lower()}%"
    stmt = (
        select(models.Model)
        .options(selectinload(models.Model.brand), selectinload(models.Model.source))
        .where(
            or_(
                models.Model.name.ilike(pattern),
                models.Model.slug.ilike(pattern),
            )
        )
        .limit(limit)
    )
    if source is not None:
        stmt = stmt.join(models.Source).where(models.Source.slug == source)
    rows = (await session.execute(stmt)).scalars().all()
    return [
        ModelOut(
            source_slug=r.source.slug,
            brand_slug=r.brand.slug,
            external_id=r.external_id,
            name=r.name,
            slug=r.slug,
            source_url=r.source_url,
        )
        for r in rows
    ]


def _to_year_out(source_slug: str, row: models.ModelYear) -> ModelYearOut:
    return ModelYearOut(
        source_slug=source_slug,
        brand_name=row.model.brand.name,
        model_name=row.model.name,
        model_external_id=row.model.external_id,
        year=row.year,
        display_name=row.display_name,
        specs=row.specs,
        scraped_at=row.scraped_at,
    )
