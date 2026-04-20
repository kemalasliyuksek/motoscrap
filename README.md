# motoscrap

**Self-hostable motorcycle catalog scraper with a clean REST API.**

motoscrap scrapes motorcycle aggregator sites (starting with [1000ps.com](https://www.1000ps.com/)), normalizes the data into a consistent shape, and exposes it through a REST API. Point your own application at it and stop hand-building motorcycle dropdowns.

- One Docker image, one command to self-host.
- Pluggable source system — add a new site by implementing one class.
- Year-level technical specifications (engine, suspension, brakes, dimensions).
- MIT-licensed.

## Quickstart

```bash
git clone https://github.com/kemalasliyuksek/motoscrap.git
cd motoscrap
cp .env.example .env
# Optional: edit .env and set MOTOSCRAP_API_KEY to protect /refresh
docker compose up -d
```

The API is now on `http://localhost:8000`. The OpenAPI docs are at `/docs`.

Trigger the first scrape:

```bash
curl -X POST http://localhost:8000/refresh \
     -H "Content-Type: application/json" \
     -H "X-API-Key: $MOTOSCRAP_API_KEY" \
     -d '{"source": "1000ps", "scope": "model", "model_external_id": "4952"}'
```

Read the result:

```bash
curl "http://localhost:8000/specs?source=1000ps&model_external_id=4952&year=2014" | jq
```

## Using the pre-built image

```yaml
# docker-compose.yml
services:
  motoscrap:
    image: ghcr.io/kemalasliyuksek/motoscrap:latest
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql+asyncpg://motoscrap:motoscrap@postgres:5432/motoscrap
      MOTOSCRAP_API_KEY: change-me
    depends_on: [postgres]
  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: motoscrap
      POSTGRES_PASSWORD: motoscrap
      POSTGRES_DB: motoscrap
    volumes: [motoscrap_data:/var/lib/postgresql/data]
volumes:
  motoscrap_data:
```

## API overview

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/health` | Liveness probe |
| `GET`  | `/sources` | List registered scrapers |
| `GET`  | `/brands?source=1000ps` | Cached brand list |
| `GET`  | `/models?source=1000ps&brand=ducati` | Cached model list |
| `GET`  | `/model-years?source=1000ps&model_external_id=4952` | Available years |
| `GET`  | `/specs?source=1000ps&model_external_id=4952&year=2014` | Full year-level specs |
| `GET`  | `/search?q=monster` | Fuzzy search over cached models |
| `POST` | `/refresh` | Trigger a background scrape (requires API key) |
| `GET`  | `/tasks/{id}` | Check scrape task status |

Read endpoints are public by default. `/refresh` requires an API key when `MOTOSCRAP_API_KEY` is set and is disabled (503) when it is not, so deployments cannot be accidentally turned into public scrapers.

See [`docs/api.md`](docs/api.md) for full request/response schemas.

## Configuration

All configuration is via environment variables. See [`.env.example`](.env.example).

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | `postgresql+asyncpg://…` connection string |
| `MOTOSCRAP_API_KEY` | *(empty)* | If set, `/refresh` requires `X-API-Key`. If empty, `/refresh` is disabled. |
| `HTTP_USER_AGENT` | `motoscrap/<version>` | User-Agent sent to source sites |
| `HTTP_RATE_LIMIT_PER_SEC` | `1` | Max requests per second per source |
| `HTTP_TIMEOUT_SECONDS` | `20` | Per-request timeout |
| `LOG_LEVEL` | `INFO` | Python logging level |

## Development

```bash
uv sync --extra dev
uv run motoscrap --help
uv run pytest
uv run ruff check
uv run mypy
```

Run the API locally against Postgres:

```bash
docker compose up -d postgres
uv run alembic upgrade head
uv run uvicorn motoscrap.main:app --reload
```

## Adding a new source

Drop a package under `src/motoscrap/sources/<yourslug>/` that subclasses `BaseSource`. See [`docs/adding-a-source.md`](docs/adding-a-source.md).

## License

[MIT](LICENSE).

## Disclaimer

motoscrap is a research and integration tool. Respect the terms of service of each source site. The project self-imposes rate limits and honours `robots.txt`, but you are responsible for your deployment. The authors are not liable for misuse.
