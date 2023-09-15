output "enabled_apis" {
  description = "Enabled APIs in the project"
  value       = [for api in google_project_service.project_services : api.service]

  depends_on = [time_sleep.wait_activate_api]
}

output "enabled_api_identities" {
  description = "Enabled API identities in the project"
  value       = { for i in google_project_service_identity.project_service_identities : i.service => i.email }
}
