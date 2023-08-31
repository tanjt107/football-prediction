resource "google_storage_bucket" "buckets" {
  for_each = toset(var.names)

  name          = join("-", compact([var.project_id, each.value]))
  location      = var.location
  force_destroy = var.force_destroy
  project       = var.project_id
}
