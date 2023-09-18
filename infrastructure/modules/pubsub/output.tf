output "topic" {
  description = "The name of the Pub/Sub topic."
  value       = google_pubsub_topic.topic.name
}

output "id" {
  description = "The ID of the Pub/Sub topic."
  value       = google_pubsub_topic.topic.id
}
