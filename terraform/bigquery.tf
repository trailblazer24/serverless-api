resource "google_bigquery_dataset" "telemetry_dataset" {
  dataset_id                  = var.bigquery_dataset_id
  friendly_name               = "Telemetry Data Warehouse"
  description                 = "Dataset containing streaming telemetry and error logs"
  location                    = var.region
  default_table_expiration_ms = null

  labels = {
    environment = "production"
    managed_by  = "terraform"
  }
}

resource "google_bigquery_table" "telemetry_table_optimized" {
  dataset_id          = google_bigquery_dataset.telemetry_dataset.dataset_id
  table_id            = var.bigquery_table_id
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["device_type", "event_type"]

  schema = jsonencode([
    {
      name = "event_id"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "device_id"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "device_type"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "event_type"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "metadata"
      type = "STRING"
      mode = "NULLABLE"
    }
  ])
}