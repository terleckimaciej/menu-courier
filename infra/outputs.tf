# Values for the repository variables read by .github/workflows/release.yml.
# Set them with: terraform output -json github_actions_variables
output "github_actions_variables" {
  description = "GitHub repository variables (Settings > Secrets and variables > Actions > Variables)."
  value = {
    GCP_PROJECT_ID                 = local.project_id
    GCP_REGION                     = local.region
    AR_REPOSITORY                  = google_artifact_registry_repository.images.repository_id
    CLOUD_RUN_JOB                  = google_cloud_run_v2_job.menu_courier.name
    GCP_DEPLOY_SERVICE_ACCOUNT     = google_service_account.deployer.email
    GCP_WORKLOAD_IDENTITY_PROVIDER = google_iam_workload_identity_pool_provider.github.name
  }
}
