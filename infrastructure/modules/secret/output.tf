output "secret_ids" {
  value       = { for k, v in google_secret_manager_secret.secrets : k => v.secret_id }
  description = "The id of secrets."
}
