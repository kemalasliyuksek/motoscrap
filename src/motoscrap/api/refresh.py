from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from motoscrap import models
from motoscrap.api.deps import require_api_key, session_dependency
from motoscrap.db import SessionLocal
from motoscrap.schemas import RefreshRequest, TaskOut
from motoscrap.services.scraper import new_task_id, run_refresh_task
from motoscrap.sources import registry

router = APIRouter(tags=["refresh"])


@router.post(
    "/refresh", status_code=202, response_model=TaskOut, dependencies=[Depends(require_api_key)]
)
async def trigger_refresh(
    payload: RefreshRequest,
    background: BackgroundTasks,
    session: AsyncSession = Depends(session_dependency),
) -> TaskOut:
    if payload.source not in registry:
        raise HTTPException(status_code=400, detail=f"Unknown source {payload.source!r}")

    if payload.scope != "model":
        raise HTTPException(
            status_code=501,
            detail=f"scope={payload.scope!r} is not implemented yet",
        )
    if not payload.model_external_id:
        raise HTTPException(status_code=400, detail="model_external_id required for scope=model")

    task_id = new_task_id()
    task = models.Task(
        id=task_id,
        source_slug=payload.source,
        scope=payload.scope,
        params=payload.model_dump(exclude={"source", "scope"}, exclude_none=True),
        status="pending",
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)

    background.add_task(
        _run_task,
        task_id=task_id,
        source_slug=payload.source,
        scope=payload.scope,
        params=payload.model_dump(exclude={"source", "scope"}, exclude_none=True),
    )

    return TaskOut.model_validate(task)


@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(session_dependency),
) -> TaskOut:
    stmt = select(models.Task).where(models.Task.id == task_id)
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut.model_validate(row)


async def _run_task(task_id: str, source_slug: str, scope: str, params: dict[str, object]) -> None:
    async with SessionLocal() as session:
        try:
            await run_refresh_task(session, task_id, source_slug, scope, params)
        except Exception:
            stmt = select(models.Task).where(models.Task.id == task_id)
            task = (await session.execute(stmt)).scalar_one_or_none()
            if task is not None:
                task.status = "failed"
                task.finished_at = datetime.now(UTC)
                await session.commit()
            raise


async def _noop_shutdown() -> None:
    await asyncio.sleep(0)
