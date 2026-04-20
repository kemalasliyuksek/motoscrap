from __future__ import annotations

BASE_URL = "https://www.1000ps.com"
DEFAULT_LOCALE = "tr-tr"
SITEMAP_INDEX = "https://static.1000ps.com/5698797_index.xml"


def model_url(
    external_id: str, slug: str, year: int | None = None, locale: str | None = None
) -> str:
    path = f"/{locale or DEFAULT_LOCALE}/model/{external_id}/{slug}"
    if year is not None:
        path = f"{path}/{year}"
    return f"{BASE_URL}{path}"
