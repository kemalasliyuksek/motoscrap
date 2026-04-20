from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from typing import ClassVar

import httpx

from motoscrap.config import get_settings
from motoscrap.sources.base import BaseSource, BrandDTO, ModelDTO, SpecsDTO
from motoscrap.sources.http import RateLimitedClient
from motoscrap.sources.onethousandps import parser, urls

logger = logging.getLogger(__name__)


class OneThousandPSSource(BaseSource):
    slug: ClassVar[str] = "1000ps"
    name: ClassVar[str] = "1000PS.com"
    base_url: ClassVar[str] = urls.BASE_URL

    def __init__(
        self,
        client: RateLimitedClient | None = None,
        locales: Sequence[str] | None = None,
    ) -> None:
        self._client = client or RateLimitedClient()
        resolved = list(locales) if locales else get_settings().scrape_locales_list
        self._locales = resolved or [urls.DEFAULT_LOCALE]

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
        per_locale: list[SpecsDTO] = []
        for locale in self._locales:
            url = urls.model_url(model.external_id, model.slug, year, locale=locale)
            try:
                response = await self._client.get(url)
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "Skipping locale %s for %s/%s: HTTP %s",
                    locale,
                    model.external_id,
                    year,
                    exc.response.status_code,
                )
                continue
            per_locale.append(parser.parse_specs(response.text, fallback_year=year))

        if not per_locale:
            raise RuntimeError(
                f"No locale fetch succeeded for model {model.external_id!r} year {year}"
            )
        primary, *secondaries = per_locale
        return parser.merge_specs(primary, secondaries)

    async def fetch_model_metadata(self, external_id: str, slug: str) -> dict[str, object]:
        """Fetch brand, model names and list of available years in one request."""
        response = await self._client.get(urls.model_url(external_id, slug))
        return parser.parse_model_metadata(response.text)
