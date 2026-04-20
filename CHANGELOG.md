# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1]

### Fixed
- Initial Alembic migration no longer calls `op.create_index` for columns already declared with `index=True`, which caused `DuplicateTableError: relation "ix_brands_slug" already exists` on a fresh Postgres volume.

## [0.2.0]

### Added
- Multi-locale scraping. `SCRAPE_LOCALES` env (default `tr-tr,en-gb`) tells the 1000ps source to fetch each year in every configured locale and merge the results.
- Categorical spec values now carry every locale the source exposes under an `_i18n` wrapper: `"cooling": {"_i18n": {"tr-tr": "Hava", "en": "Air", "de": "Luft"}}`.
- `GET /specs` and `GET /model-years` accept `?locale=<bcp47>` to flatten translations to a single string with BCP-47 fallback (e.g. `tr` matches `tr-tr`; unknown locales fall back to `en-gb`, `en`, `tr-tr`, then whatever exists).
- `GET /locales?source=&model_external_id=&year=` enumerates the locale codes available for a cached year.
- Normaliser now keys off 1000ps's stable `translationKey` values (`bikekat#attr#10`) instead of locale-dependent display names, so any locale-prefixed URL parses cleanly.

### Breaking
- `ModelYear.specs` shape changed: categorical fields are now `{"_i18n": {...}}` instead of plain strings. No Alembic migration is needed (JSONB column), but cached data scraped under 0.1.x must be re-fetched via `POST /refresh` to gain multi-locale values.

## [0.1.0]

### Added
- Initial project scaffolding.
- `1000ps.com` source with year-level specifications.
- REST API: `/sources`, `/brands`, `/models`, `/model-years`, `/specs`, `/search`, `/refresh`, `/tasks/{id}`.
- Docker image published to GHCR.
