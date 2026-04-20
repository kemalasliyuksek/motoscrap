FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --upgrade pip \
    && pip wheel --no-deps --wheel-dir /wheels .


FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

RUN groupadd --system motoscrap \
    && useradd --system --gid motoscrap --home /app motoscrap

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN pip install --no-cache-dir /wheels/*.whl \
    && pip install --no-cache-dir \
        'fastapi>=0.115' 'uvicorn[standard]>=0.32' 'httpx>=0.27' \
        'selectolax>=0.3.21' 'orjson>=3.10' \
        'sqlalchemy[asyncio]>=2.0.35' 'asyncpg>=0.29' 'alembic>=1.13' \
        'pydantic>=2.9' 'pydantic-settings>=2.5' 'typer>=0.12' \
    && rm -rf /wheels \
    && chmod +x /usr/local/bin/entrypoint.sh \
    && chown -R motoscrap:motoscrap /app

USER motoscrap

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request, sys; \
        sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "motoscrap.main:app", "--host", "0.0.0.0", "--port", "8000"]
