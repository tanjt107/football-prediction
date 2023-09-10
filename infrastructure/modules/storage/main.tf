locals {
  file_list = flatten([
    for bucket, files in var.files : [
      for file in files : {
        bucket = bucket,
        file   = file
      }
    ]
  ])
}

resource "google_storage_bucket" "buckets" {
  for_each = toset(var.names)

  name          = join("-", compact([each.value, var.suffix]))
  location      = var.location
  force_destroy = var.force_destroy
  project       = var.project_id
}

resource "google_storage_bucket_object" "picture" {
  for_each = { for obj in local.file_list : "${obj.bucket}_${obj.file}" => obj }

  bucket = google_storage_bucket.buckets[each.value.bucket].name
  name   = basename(each.value.file)
  source = each.value.file
}
