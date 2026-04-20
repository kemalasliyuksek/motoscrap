# Contributing to motoscrap

Thanks for your interest in contributing. Here is the short version.

## Development setup

```bash
git clone https://github.com/kemalasliyuksek/motoscrap.git
cd motoscrap
uv sync --extra dev
docker compose up -d postgres
uv run alembic upgrade head
uv run uvicorn motoscrap.main:app --reload
```

## Before you open a PR

- `uv run ruff check` and `uv run ruff format` must be clean.
- `uv run mypy` must be clean.
- `uv run pytest` must pass, including any tests you added.
- New features that touch a source should come with fixture HTML under `tests/fixtures/<source>/` and a test that locks down the parsed output.

## Adding a new source

See [`docs/adding-a-source.md`](docs/adding-a-source.md). In short: create a package under `src/motoscrap/sources/<slug>/`, subclass `BaseSource`, register it from the package `__init__.py`.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(1000ps): parse rider-aids group
fix(parser): handle translation objects missing tr locale
docs(readme): document API key behaviour
```

## Code style

- No inline comments that describe _what_ the code does — the code and names already do that.
- Comments only when there is a non-obvious _why_ (invariant, workaround, trade-off).
- No AI-generated boilerplate or placeholder prose.
- Type hints everywhere. `mypy --strict` is the contract.

## Licensing

By contributing you agree that your contributions are licensed under the [MIT License](LICENSE).
