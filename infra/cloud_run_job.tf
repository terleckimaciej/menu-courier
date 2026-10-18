locals {
  # Order matches the Job as it exists today; the API keeps env order, so a different order would show as a change.
  job_secret_env = ["DATABASE_URL", "FB_PAGE_ACCESS_TOKEN", "APIFY_API_TOKEN"]
}

resource "google_cloud_run_v2_job" "menu_courier" {
  name     = local.job_name
  location = local.region

  # Guards against an accidental terraform destroy removing the Job.
  deletion_protection = true

  template {
    template {
      service_account = google_service_account.job.email
      timeout         = "600s"
      max_retries     = 0

      containers {
        # Initial image only. Releases update it from CI (release.yml), see ignore_changes below.
        image = "${local.region}-docker.pkg.dev/${local.project_id}/${local.artifact_repository}/menu-courier:v1.2.0"

        resources {
          limits = {
            cpu    = "1"
            memory = "1Gi"
          }
        }

        dynamic "env" {
          for_each = local.job_secret_env

          content {
            name = env.value
            value_source {
              secret_key_ref {
                secret  = google_secret_manager_secret.app[env.value].secret_id
                version = "latest"
              }
            }
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      client,
      client_version,
      template[0].template[0].containers[0].image,
    ]
  }

  depends_on = [google_project_service.enabled]
}

# CI deploys new images to the Job.
resource "google_cloud_run_v2_job_iam_member" "deployer_developer" {
  location = google_cloud_run_v2_job.menu_courier.location
  name     = google_cloud_run_v2_job.menu_courier.name
  role     = "roles/run.developer"
  member   = "serviceAccount:${google_service_account.deployer.email}"
}

# Cloud Scheduler starts the Job.
resource "google_cloud_run_v2_job_iam_member" "scheduler_invoker" {
  location = google_cloud_run_v2_job.menu_courier.location
  name     = google_cloud_run_v2_job.menu_courier.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}
