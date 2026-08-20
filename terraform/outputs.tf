output "cloud_run_url" {
  description = "Public URL of the deployed FastAPI Gateway"
  value       = google_cloud_run_v2_service.api_gateway.uri
}

output "pubsub_topic_id" {
  description = "ID of the created Pub/Sub telemetry topic"
  value       = google_pubsub_topic.telemetry_topic.id
}

output "bigquery_table_id" {
  description = "Fully qualified BigQuery table ID"
  value       = "${google_bigquery_dataset.telemetry_dataset.dataset_id}.${google_bigquery_table.telemetry_table_optimized.table_id}"
}