from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass(frozen=True, slots=True)
class BrandDTO:
    external_id: str
    name: str
    slug: str


@dataclass(frozen=True, slots=True)
class ModelDTO:
    external_id: str
    brand: BrandDTO
    name: str
    slug: str
    source_url: str


@dataclass(frozen=True, slots=True)
class SpecsDTO:
    """Year-level specifications for a model.

    `grouped` contains the normalized, English-keyed values, e.g.
    `{"engine": {"bore_mm": 88, "stroke_mm": 66, "power_hp": 87}, ...}`.

    `raw` preserves the source-native key/value pairs so that unmapped
    attributes are never lost and normalization bugs can be debugged later.
    """

    year: int
    display_name: str
    grouped: dict[str, dict[str, Any]] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


class BaseSource(ABC):
    slug: ClassVar[str]
    name: ClassVar[str]
    base_url: ClassVar[str]

    @abstractmethod
    async def list_brands(self) -> Iterable[BrandDTO]: ...

    @abstractmethod
    async def list_models(self, brand: BrandDTO) -> Iterable[ModelDTO]: ...

    @abstractmethod
    async def list_model_years(self, model: ModelDTO) -> Iterable[int]: ...

    @abstractmethod
    async def fetch_specs(self, model: ModelDTO, year: int) -> SpecsDTO: ...

    async def aclose(self) -> None:
        """Release any resources. Default implementation is a no-op."""


class SourceRegistry:
    def __init__(self) -> None:
        self._sources: dict[str, type[BaseSource]] = {}

    def register(self, source_cls: type[BaseSource]) -> type[BaseSource]:
        slug = source_cls.slug
        if slug in self._sources:
            raise ValueError(f"Source {slug!r} already registered")
        self._sources[slug] = source_cls
        return source_cls

    def get(self, slug: str) -> type[BaseSource]:
        try:
            return self._sources[slug]
        except KeyError as exc:
            raise KeyError(f"Unknown source {slug!r}") from exc

    def all(self) -> list[type[BaseSource]]:
        return list(self._sources.values())

    def __contains__(self, slug: str) -> bool:
        return slug in self._sources


registry = SourceRegistry()
