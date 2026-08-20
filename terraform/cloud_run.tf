resource "google_cloud_run_v2_service" "api_gateway" {
  name     = "serverless-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    containers {
      image = var.cloud_run_image

      resources {
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "BQ_DATASET"
        value = var.bigquery_dataset_id
      }
      env {
        name  = "BQ_TABLE"
        value = var.bigquery_table_id
      }
    }
  }
}

# Allow public unauthenticated invocations on the API Gateway
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.api_gateway.location
  service  = google_cloud_run_v2_service.api_gateway.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}