# menu-courier

[![CI](https://github.com/terleckimaciej/menu-courier/actions/workflows/ci.yml/badge.svg)](https://github.com/terleckimaciej/menu-courier/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/terleckimaciej/menu-courier)](https://github.com/terleckimaciej/menu-courier/releases)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-0db7ed?logo=docker&logoColor=white)
![Cloud Run](https://img.shields.io/badge/Cloud%20Run-containers-4285F4?logo=googlecloud&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-844FBA?logo=terraform&logoColor=white)
![Postgres](https://img.shields.io/badge/Postgres-Neon-4169E1?logo=postgresql&logoColor=white)

A small, scheduled service that scrapes subscribed Facebook pages and delivers new posts via Messenger — built mainly for Ms. Helena, an elderly family friend who has trouble with her vision and can't check Facebook herself to see the daily menu at her local lunch bars.

It runs as a production-style system rather than a script: a Cloud Run Job started by Cloud Scheduler, secrets in Secret Manager, infrastructure in Terraform, and tests and releases through GitHub Actions with keyless authentication to Google Cloud.

**Documentation:** [Architecture](docs/architecture.md) · [Operations](docs/operations.md) · [Cloud Run migration log](docs/cloud-run-migration.md) · [Infrastructure (Terraform)](infra/README.md)

## How it works

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/architecture-dark.svg">
    <img src="docs/images/architecture-light.svg" width="100%" alt="Architecture: Cloud Scheduler starts the app container (a Cloud Run Job), which reads secrets from Secret Manager, fetches the latest post through a Facebook scraper API, checks and records delivery in Postgres on Neon, and sends it through the Messenger API to the recipient. Terraform defines the Google Cloud resources and GitHub Actions deploys the container.">
  </picture>
</p>

The stack is serverless end to end: Cloud Scheduler starts a containerized Cloud
Run Job a few times a day, and Neon scales to zero between runs. Releases are built
and deployed by GitHub Actions; see [the architecture](docs/architecture.md).
Everything runs within free tiers; the numbers are in
[Costs and limits](docs/cloud-run-migration.md#costs-and-limits).

Subscriptions (which page to watch, who receives it, optional text filter, whether
to include images) are just rows in a table — adding a new restaurant/recipient
pair is one CLI command, not a code change. On each run, the pipeline loops over
every active subscription: it scrapes the latest matching post, skips it if that
exact post has already been delivered, and otherwise sends the text and any
images via Messenger and records the outcome (sent or failed) back in Postgres.

## Why these building blocks

- **[Apify](https://apify.com)'s Facebook Posts Scraper** for scraping: Facebook has
  no practical public API for reading page posts, and maintaining a scraper against
  a platform that fights scrapers is best left to a dedicated service
  (responsibility included).
- **Messenger Send API** called directly with `requests`: a couple of authenticated
  HTTP calls don't justify a wrapper library.
- **Neon (serverless Postgres)** for storage: scales to zero between runs, and the
  free tier covers this footprint.

The hosting decisions are covered in the
[Cloud Run migration log](docs/cloud-run-migration.md).

## CLI

All commands run as `poetry run menu-courier <command>`.

| Command | What it does |
|---|---|
| `run` | Run the pipeline once — check every active subscription and deliver anything new |
| `list-subscriptions` | List all subscriptions and whether they're active |
| `list-recipients` | Look up a PSID from recent Messenger conversations |
| `add-subscription` | Add a new subscription (see flags below) |
| `deactivate-subscription --id N` | Deactivate a subscription without deleting its history |

`add-subscription` takes a few flags:

```bash
poetry run menu-courier add-subscription \
    --platform facebook \
    --source-handle "https://www.facebook.com/..." \
    --recipient-psid ... \
    --recipient-label "..." \
    --text-filter "..." \
    [--no-images]
```

## Local development

Requirements: Python 3.12+, [Poetry](https://python-poetry.org), Docker.

```bash
poetry install
docker compose up -d          # local Postgres for development
cp .env.example .env          # fill in real values, see below
poetry run alembic upgrade head
poetry run pytest
```

### Environment variables

See `.env.example`. In short:

| Variable | What it's for |
|---|---|
| `DATABASE_URL` | Postgres connection string (`postgresql+psycopg://...`) |
| `FB_PAGE_ACCESS_TOKEN` | Page Access Token for the Messenger bot's Facebook Page |
| `APIFY_API_TOKEN` | Apify API token (Facebook Posts Scraper) |

`DATABASE_URL` always points at whatever database you want a given command to hit.
For day-to-day work that's the local Postgres from `docker compose`. Never point
`.env` itself at production — use a one-off override instead:

```bash
DATABASE_URL="..." poetry run menu-courier list-subscriptions
```

Admin commands (`add-subscription`, `deactivate-subscription`) print which
database host they're about to touch and ask for confirmation before writing
anything.

## One-time manual setup (outside the code)

Facebook doesn't let this kind of thing be fully automated from scratch. Once per
project (not per recipient):

1. Create a dedicated Facebook Page for the bot (not the restaurant's page).
2. Create a Facebook App (Development mode — no App Review needed for this use
   case), add the Messenger product, connect it to the Page, generate a Page
   Access Token.

Once per recipient:

1. They register as a Facebook Developer (developers.facebook.com) — required by
   Meta before anyone can be assigned a role on an app.
2. Add them as a Tester on the app (App roles → Roles).
3. They accept the invitation and send any message to the bot's Page once.
4. `poetry run menu-courier list-recipients` to read off their PSID.
5. `add-subscription` with that PSID.

## Testing & code quality

```bash
poetry run pytest
poetry run pre-commit run --all-files
```

Pre-commit runs ruff (lint + format), mypy, and detect-secrets. Tests are unit
tests only — HTTP calls (Apify, Messenger) are mocked via `responses`, and the
pipeline tests mock the storage layer.

## Deployment

- `Dockerfile` builds a multi-stage image (Poetry installs deps in a builder
  stage, only the resulting `.venv` + source ship in the final image).
- CI (`.github/workflows/ci.yml`) lints and tests on every push/PR, and requires a
  version bump when application code changes.
- Releases are deliberate, not automatic on every merge. Pushing a `v*` tag runs
  `.github/workflows/release.yml`: it checks the tag against the `pyproject.toml`
  version, runs the tests, builds the image once, pushes it to GHCR and Artifact
  Registry, and updates the Cloud Run Job.
- Cloud Scheduler starts the Job three times a day; secrets come from Secret
  Manager. The infrastructure is defined in Terraform (`infra/`).

See [docs/operations.md](docs/operations.md) for the release and rollback steps.

## Known limitations

- Scraping a restaurant's public page without their cooperation is, strictly,
  outside Facebook's ToS — accepted here given the low frequency (a few checks a
  day) and assistive purpose. Apify's infrastructure absorbs the actual
  anti-scraping risk rather than this project's own IP.
- The Facebook App stays in Development mode: it can only message people who
  have accepted a Tester/Developer/Admin role on the app. Messaging the general
  public would require Meta's App Review, which is disproportionate for a
  single-recipient personal tool.
- There is no database in CI: tests are unit tests with the storage layer mocked,
  and the live scraping and delivery path is verified manually.
