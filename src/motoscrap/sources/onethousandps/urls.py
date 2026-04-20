from __future__ import annotations

BASE_URL = "https://www.1000ps.com"
LOCALE = "tr-tr"
SITEMAP_INDEX = "https://static.1000ps.com/5698797_index.xml"


def model_url(external_id: str, slug: str, year: int | None = None) -> str:
    path = f"/{LOCALE}/model/{external_id}/{slug}"
    if year is not None:
        path = f"{path}/{year}"
    return f"{BASE_URL}{path}"
