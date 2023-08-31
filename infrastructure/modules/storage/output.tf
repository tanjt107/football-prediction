output "names" {
  description = "Bucket names."
  value = { for name, bucket in google_storage_bucket.buckets :
    name => bucket.name
  }
}

output "urls" {
  description = "Bucket URLs."
  value = { for name, bucket in google_storage_bucket.buckets :
    name => bucket.url
  }
}
