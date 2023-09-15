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

locals {
  sa_identities = flatten([
    for sa, roles in var.service_accounts : [
      for role in roles :
      { sa = sa, role = role }
    ]
  ])
}

resource "google_service_account" "service_accounts" {
  for_each   = var.service_accounts
  account_id = each.key
  project    = google_project.project.project_id
}

locals {
  add_roles = {
    for sa in local.sa_identities :
    "${sa.sa} ${sa.role}" => {
      email = google_service_account.service_accounts[sa.sa].email
      role  = sa.role
    }
  }
}

resource "google_project_iam_binding" "service_account_roles" {
  for_each = local.add_roles
  role     = each.value.role
  members  = ["serviceAccount:${each.value.email}"]
  project  = google_project.project.project_id
}
