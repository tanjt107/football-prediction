resource "google_pubsub_topic" "topic" {
  name    = var.topic
  project = var.project_id
}
