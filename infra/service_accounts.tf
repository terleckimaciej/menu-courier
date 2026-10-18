# Runtime identity of the Cloud Run Job. Its only permission is reading the app secrets (secrets.tf).
resource "google_service_account" "job" {
  account_id   = "menu-courier-job"
  display_name = "menu-courier-job"
  description  = "menu-courier Cloud Run runtime"

  depends_on = [google_project_service.enabled]
}

# Identity Cloud Scheduler uses to start the Job (invoker role is granted on the Job itself).
resource "google_service_account" "scheduler" {
  account_id   = "menu-courier-scheduler"
  display_name = "menu-courier Scheduler invoker"

  depends_on = [google_project_service.enabled]
}

# Identity GitHub Actions assumes through Workload Identity Federation to publish and deploy.
resource "google_service_account" "deployer" {
  account_id   = "gh-deployer"
  display_name = "GitHub Actions deployer"

  depends_on = [google_project_service.enabled]
}

# Deploying a Job that runs as the runtime account requires act-as permission on it.
resource "google_service_account_iam_member" "deployer_acts_as_job" {
  service_account_id = google_service_account.job.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deployer.email}"
}
