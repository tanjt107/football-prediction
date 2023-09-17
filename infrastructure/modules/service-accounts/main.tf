resource "google_service_account" "service_accounts" {
  for_each   = var.service_accounts
  account_id = each.key
  project    = var.project_id
}

locals {
  project_roles = { for pair in flatten([
    for sa, roles in var.service_accounts : [
      for role in roles : {
        key = "${sa} ${role}"
        value = {
          sa   = sa
          role = role
        }
      }
    ]
  ]) : pair.key => pair.value }
}

resource "google_project_iam_binding" "service_account_roles" {
  for_each = local.project_roles
  role     = each.value.role
  members  = ["serviceAccount:${google_service_account.service_accounts[each.value.sa].email}"]
  project  = var.project_id
}
