locals {
  # Secret name => Secret Manager secret type. Changing a type forces replacement,
  # which would destroy the secret together with its versions.
  secrets = {
    APIFY_API_TOKEN      = "ACCESS_KEY"
    DATABASE_URL         = "OTHER_DB_CREDENTIALS"
    FB_PAGE_ACCESS_TOKEN = "ACCESS_KEY"
  }
}

# Only the secret containers are managed here. Values (versions) are added outside
# Terraform so they never end up in the state.
resource "google_secret_manager_secret" "app" {
  for_each = local.secrets

  secret_id   = each.key
  secret_type = each.value

  replication {
    auto {}
  }

  # Destroying a secret deletes its versions, i.e. the stored tokens.
  lifecycle {
    prevent_destroy = true
  }

  depends_on = [google_project_service.enabled]
}

resource "google_secret_manager_secret_iam_member" "job_accessor" {
  for_each = google_secret_manager_secret.app

  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.job.email}"
}
