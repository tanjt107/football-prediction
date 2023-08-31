resource "google_project" "project" {
  name            = var.name
  project_id      = var.project_id
  billing_account = var.billing_account
}

module "services" {
  source = "../services"

  project_id              = google_project.project.project_id
  activate_apis           = var.activate_apis
  activate_api_identities = var.activate_api_identities
}
