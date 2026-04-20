from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    base_url: Mapped[str] = mapped_column(String(256), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    brands: Mapped[list[Brand]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
    models: Mapped[list[Model]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class Brand(Base, TimestampMixin):
    __tablename__ = "brands"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_brand_source_external"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    source: Mapped[Source] = relationship(back_populates="brands")
    models: Mapped[list[Model]] = relationship(back_populates="brand", cascade="all, delete-orphan")


class Model(Base, TimestampMixin):
    __tablename__ = "models"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_model_source_external"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(String(512), nullable=False)

    source: Mapped[Source] = relationship(back_populates="models")
    brand: Mapped[Brand] = relationship(back_populates="models")
    years: Mapped[list[ModelYear]] = relationship(
        back_populates="model", cascade="all, delete-orphan"
    )


class ModelYear(Base, TimestampMixin):
    __tablename__ = "model_years"
    __table_args__ = (UniqueConstraint("model_id", "year", name="uq_model_year"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_id: Mapped[int] = mapped_column(
        ForeignKey("models.id", ondelete="CASCADE"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(512), nullable=False)
    specs: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    raw_specs: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    model: Mapped[Model] = relationship(back_populates="years")


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
