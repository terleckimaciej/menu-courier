resource "google_artifact_registry_repository" "images" {
  location      = local.region
  repository_id = local.artifact_repository
  description   = "menu-courier container images"
  format        = "DOCKER"

  # false = policies actually delete; true = log what they would delete.
  cleanup_policy_dry_run = false

  # Keep wins over Delete: the 5 newest versions are never removed, so the image
  # the Cloud Run Job runs and a few rollback targets always stay available.
  cleanup_policies {
    id     = "keep-5-most-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 5
    }
  }

  cleanup_policies {
    id     = "delete-untagged-after-7d"
    action = "DELETE"
    condition {
      tag_state  = "UNTAGGED"
      older_than = "604800s" # 7 days
    }
  }

  cleanup_policies {
    id     = "delete-any-after-30d"
    action = "DELETE"
    condition {
      tag_state  = "ANY"
      older_than = "2592000s" # 30 days
    }
  }

  depends_on = [google_project_service.enabled]
}

# The deployer pushes images from CI.
resource "google_artifact_registry_repository_iam_member" "deployer_writer" {
  location   = google_artifact_registry_repository.images.location
  repository = google_artifact_registry_repository.images.repository_id
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.deployer.email}"
}
