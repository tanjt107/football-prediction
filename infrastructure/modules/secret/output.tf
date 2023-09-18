output "names" {
  value = concat(
    values({ for k, v in google_secret_manager_secret.secrets : k => v.name }),
  )
  description = "The name list of secrets."
}
