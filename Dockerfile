FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./
RUN poetry config virtualenvs.in-project true \
    && poetry install --only main --no-root --no-interaction

COPY src ./src
RUN poetry install --only main --no-interaction


FROM python:3.12-slim AS runtime

RUN useradd --create-home appuser
WORKDIR /app

COPY --from=builder /app/.venv ./.venv
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

CMD ["python", "-m", "menu_courier.cli", "run"]
