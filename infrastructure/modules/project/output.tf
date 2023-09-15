output "project_id" {
  description = "ID of the project"
  value       = google_project.project.project_id

  depends_on = [
    module.services.enabled_apis,
    module.services.enabled_api_identities
  ]
}

output "project_number" {
  description = "Numeric identifier for the project"
  value       = google_project.project.number

  depends_on = [
    module.services.enabled_apis,
    module.services.enabled_api_identities
  ]
}

output "service_account_emails" {
  value       = { for k, v in google_service_account.service_accounts : k => v.email }
  description = "The email of the service accounts"
}

output "enabled_api_identities" {
  description = "Enabled API identities in the project"
  value       = module.services.enabled_api_identities
}
