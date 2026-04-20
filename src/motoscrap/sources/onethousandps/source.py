from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from motoscrap.sources.base import BaseSource, BrandDTO, ModelDTO, SpecsDTO
from motoscrap.sources.http import RateLimitedClient
from motoscrap.sources.onethousandps import parser, urls


class OneThousandPSSource(BaseSource):
    slug: ClassVar[str] = "1000ps"
    name: ClassVar[str] = "1000PS.com"
    base_url: ClassVar[str] = urls.BASE_URL

    def __init__(self, client: RateLimitedClient | None = None) -> None:
        self._client = client or RateLimitedClient()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def list_brands(self) -> Iterable[BrandDTO]:
        raise NotImplementedError(
            "Full brand listing is not yet implemented for 1000ps. "
            "Use sitemap-driven discovery in a future release."
        )

    async def list_models(self, brand: BrandDTO) -> Iterable[ModelDTO]:
        raise NotImplementedError(
            "Full model listing is not yet implemented for 1000ps. "
            "Use `refresh` with an explicit model_external_id for now."
        )

    async def list_model_years(self, model: ModelDTO) -> Iterable[int]:
        response = await self._client.get(urls.model_url(model.external_id, model.slug))
        return parser.parse_existing_model_years(response.text)

    async def fetch_specs(self, model: ModelDTO, year: int) -> SpecsDTO:
        response = await self._client.get(urls.model_url(model.external_id, model.slug, year))
        return parser.parse_specs(response.text, fallback_year=year)

    async def fetch_model_metadata(self, external_id: str, slug: str) -> dict[str, object]:
        """Fetch brand, model names and list of available years in one request."""
        response = await self._client.get(urls.model_url(external_id, slug))
        return parser.parse_model_metadata(response.text)
