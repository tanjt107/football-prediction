output "topic" {
  value       = google_pubsub_topic.topic.name
  description = "The name of the Pub/Sub topic"
}

output "id" {
  value       = google_pubsub_topic.topic.id
  description = "The ID of the Pub/Sub topic"
}
