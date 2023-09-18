output "emails" {
  description = "Service account emails by name."
  value       = { for name, account in google_service_account.service_accounts : name => account.email }
}
