output "emails" {
  value       = { for k, v in google_service_account.service_accounts : k => v.email }
  description = "Service account emails by name."
}
