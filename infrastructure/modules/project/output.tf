output "project_id" {
  description = "ID of the project."
  value       = google_project.project.project_id

  depends_on = [
    module.services.enabled_apis,
    module.services.enabled_api_identities
  ]
}

output "project_number" {
  description = "Numeric identifier for the project."
  value       = google_project.project.number

  depends_on = [
    module.services.enabled_apis,
    module.services.enabled_api_identities
  ]
}
