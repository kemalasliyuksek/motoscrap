from __future__ import annotations

import asyncio
import json

import typer

from motoscrap.db import SessionLocal
from motoscrap.services.scraper import scrape_model
from motoscrap.sources import registry

app = typer.Typer(
    name="motoscrap",
    help="motoscrap command-line interface",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)


@app.command("sources")
def sources_cmd() -> None:
    """List registered scraper sources."""
    for cls in registry.all():
        typer.echo(f"{cls.slug:12s} {cls.name:24s} {cls.base_url}")


@app.command("scrape-model")
def scrape_model_cmd(
    source: str = typer.Argument(..., help="Source slug, e.g. 1000ps"),
    model_external_id: str = typer.Argument(..., help="Source-native model ID"),
    slug: str = typer.Option(None, "--slug", help="Model slug on the source (optional)"),
) -> None:
    """Scrape all available years for a single model and print the result."""

    async def _run() -> None:
        async with SessionLocal() as session:
            result = await scrape_model(session, source, model_external_id, slug)
            typer.echo(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(_run())


if __name__ == "__main__":
    app()
