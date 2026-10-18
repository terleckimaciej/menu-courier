# Operations

Everyday commands for the deployed service. They assume `gcloud` is authenticated and pointed at the project.

## Run the Job manually

```bash
gcloud run jobs execute menu-courier --region europe-central2 --wait
```

This is a real run: if there is a new post that has not been delivered, it is sent.

## Check recent runs and logs

```bash
gcloud run jobs executions list --job menu-courier --region europe-central2 --limit 5

gcloud logging read \
  'resource.type="cloud_run_job" AND resource.labels.job_name="menu-courier"' \
  --freshness 12h --limit 30 --format="value(timestamp,textPayload)"
```

Each run logs one line per subscription (`outcome=sent|failed|already_sent|no_matching_post|fetch_failed`) and a `Run finished` summary. The `RUN_BY` column of the execution list shows whether Cloud Scheduler or a person started it.

## Pause or resume the schedule

```bash
gcloud scheduler jobs pause menu-courier-run --location europe-central2
gcloud scheduler jobs resume menu-courier-run --location europe-central2
```

Terraform tracks the schedule itself, not its paused state, so pausing does not show up as drift.

## Release a new version

1. Bump `version` in `pyproject.toml` (the pull request check requires it when application code changes) and merge.
2. Tag the merge commit; the tag must match the version:

   ```bash
   git tag v1.2.1 && git push origin v1.2.1
   ```

3. Wait for the Release workflow. It publishes the image and updates the Job.
4. Optionally publish release notes once it succeeded:

   ```bash
   gh release create v1.2.1 --verify-tag --generate-notes
   ```

## Roll back

Point the Job at an earlier image that is still in Artifact Registry:

```bash
gcloud run jobs update menu-courier --region europe-central2 \
  --image europe-central2-docker.pkg.dev/<project-id>/menu-courier/menu-courier:<tag>
```

The next release replaces it again. If the version was already removed by the cleanup policy, pull it from GHCR, tag it for Artifact Registry and push it:

```bash
docker pull ghcr.io/terleckimaciej/menu-courier:<tag>
docker tag  ghcr.io/terleckimaciej/menu-courier:<tag> \
  europe-central2-docker.pkg.dev/<project-id>/menu-courier/menu-courier:<tag>
docker push europe-central2-docker.pkg.dev/<project-id>/menu-courier/menu-courier:<tag>
```

## Rotate a secret

The Job reads `latest` at the start of every run, so a new version is picked up by the next execution.

```bash
read -rs VALUE
printf %s "$VALUE" | gcloud secrets versions add APIFY_API_TOKEN --data-file=-
unset VALUE

gcloud secrets versions list APIFY_API_TOKEN
gcloud secrets versions destroy <old-version> --secret APIFY_API_TOKEN
```

Destroy the old version rather than disabling it: disabled versions still count toward the free tier's active-version limit.

## Admin commands against production

Run them with a one-off `DATABASE_URL` override; see the project README.

## Infrastructure changes

Edit the Terraform in `infra/`, then `terraform plan` and `terraform apply`. See [`infra/README.md`](../infra/README.md).
