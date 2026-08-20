variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  default     = "flash-gasket-486800-p9"
}

variable "region" {
  description = "Default GCP Region for compute and storage"
  type        = string
  default     = "northamerica-northeast1"
}

variable "pubsub_topic_name" {
  description = "Pub/Sub topic for streaming incoming telemetry"
  type        = string
  default     = "telemetry-stream"
}

variable "bigquery_dataset_id" {
  description = "BigQuery dataset ID for telemetry analytics"
  type        = string
  default     = "telemetry_data"
}

variable "bigquery_table_id" {
  description = "Optimized telemetry table name"
  type        = string
  default     = "telemetry_events_optimized"
}

variable "cloud_run_image" {
  description = "Container image URL hosted on Artifact Registry"
  type        = string
  default     = "northamerica-northeast1-docker.pkg.dev/flash-gasket-486800-p9/api-repo/serverless-api:v2"
}