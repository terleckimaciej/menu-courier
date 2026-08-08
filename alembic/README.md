# Database migrations (Alembic)

## What this is

[Alembic](https://alembic.sqlalchemy.org) is SQLAlchemy's migration tool. It keeps
a **versioned, linear history** of schema changes as small Python scripts in
`versions/`, instead of the schema drifting silently via ad-hoc `ALTER TABLE`
statements run by hand.

## Why it matters here

This project runs against two independent Postgres instances — a local one (via
`docker-compose.yml`) and production (Neon). Alembic lets both be brought to the
exact same, known schema state with one command (`alembic upgrade head`),
regardless of which one you point it at. Each database tracks its own progress
through the migration history in a small `alembic_version` table that Alembic
manages automatically — you never touch it directly.

## How it's wired in this repo

- **`src/menu_courier/storage/models.py`** is the source of truth for what the
  schema *should* look like — plain SQLAlchemy model classes.
- **`alembic/env.py`** is patched to pull the actual connection string from our
  own `menu_courier.config.settings` (i.e. `.env`/`.env.production`), not from
  `alembic.ini` — so there's exactly one place a connection string is configured,
  not two that could drift apart. It also points `target_metadata` at
  `Base.metadata` from `models.py`, which is what makes `--autogenerate` (below)
  work at all.
- **`alembic/versions/*.py`** is the actual history — each file is one incremental
  step, chained to the previous one via `down_revision`.

## Common commands

Generate a migration from a model change (this only *writes a file* — it does not
touch any database):

```bash
poetry run alembic revision --autogenerate -m "describe the change"
```

**Always read the generated file before applying it.** Autogenerate is a diff
tool, not magic — it compares the live database to `models.py` and writes what it
thinks the difference is, but it gets some things wrong in predictable ways (see
Gotchas below).

Apply all pending migrations to whichever database `DATABASE_URL` currently
points at:

```bash
poetry run alembic upgrade head
```

## Gotchas worth knowing

- **Renaming a column is not detected as a rename.** Autogenerate compares by
  column name, so a rename shows up as "drop old column, add new column" — which
  silently discards any existing data in that column. Fine on an empty table;
  dangerous on one with real rows. If it's a genuine rename, rewrite the
  generated migration to use `op.alter_column(..., new_column_name=...)` instead.
- **Adding a `NOT NULL` column to a non-empty table fails** unless you give it a
  `server_default` in the migration — SQLAlchemy's `default=` in `models.py` is
  a Python-side/ORM default, applied only on new inserts, and doesn't help
  Postgres decide what to backfill into existing rows.
- **Migrations are for schema, not data.** One-off data fixes (typo in a row,
  deleting a stray test record) are just plain SQL against the database — they
  don't need a migration. Migrations *can* include data-moving logic when it's
  tied to a schema change (e.g. backfilling a new column before making it
  `NOT NULL`), but that's the exception, not the rule.
