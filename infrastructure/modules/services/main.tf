locals {
  service_identities = flatten([
    for api, roles in var.activate_api_identities : [
      for role in roles :
      { api = api, role = role }
    ]
  ])
}

resource "google_project_service" "project_services" {
  for_each = toset(var.activate_apis)

  project = var.project_id
  service = each.value
}

resource "time_sleep" "wait_activate_api" {
  count = var.api_activated ? 0 : 1

  create_duration = var.activate_api_sleep_duration

  depends_on = [google_project_service.project_services]
}

data "google_compute_default_service_account" "service_account" {
  count = length([for api in var.activate_apis : api if api == "compute.googleapis.com"]) > 0 ? 1 : 0

  project = var.project_id

  depends_on = [time_sleep.wait_activate_api]
}

data "google_storage_project_service_account" "service_account" {
  count = length([for api in var.activate_apis : api if api == "storage.googleapis.com"]) > 0 ? 1 : 0

  project = var.project_id

  depends_on = [time_sleep.wait_activate_api]
}

locals {
  add_service_roles = merge(
    {
      for si in local.service_identities :
      "${si.api} ${si.role}" => {
        email = data.google_compute_default_service_account.service_account[0].email
        role  = si.role
      }
      if si.api == "compute.googleapis.com"
    },
    {
      for si in local.service_identities :
      "${si.api} ${si.role}" => {
        email = data.google_storage_project_service_account.service_account[0].email_address
        role  = si.role
      }
      if si.api == "storage.googleapis.com"
    }
  )
}

resource "google_project_iam_member" "project_service_identity_roles" {
  for_each = local.add_service_roles

  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${each.value.email}"

  depends_on = [time_sleep.wait_activate_api]
}
