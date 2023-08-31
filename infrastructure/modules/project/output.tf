output "project_id" {
  description = "ID of the project"
  value       = google_project.project.project_id

  depends_on = [
    module.services.enabled_apis,
    module.services.enabled_api_identities
  ]
}

output "enabled_apis" {
  description = "Enabled APIs in the project"
  value       = module.services.enabled_apis
}
