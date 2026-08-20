resource "google_pubsub_topic" "telemetry_topic" {
  name = var.pubsub_topic_name

  labels = {
    environment = "production"
    managed_by  = "terraform"
  }
}

resource "google_pubsub_subscription" "telemetry_sub" {
  name  = "${var.pubsub_topic_name}-sub"
  topic = google_pubsub_topic.telemetry_topic.name

  # Retain unacknowledged messages for 7 days
  message_retention_duration = "604800s"
  retain_acked_messages      = false
  ack_deadline_seconds       = 20

  expiration_policy {
    ttl = "" # Never expire
  }
}