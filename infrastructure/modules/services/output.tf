output "enabled_apis" {
  description = "Enabled APIs in the project"
  value       = [for api in google_project_service.project_services : api.service]

  depends_on = [time_sleep.wait_activate_api]
}
