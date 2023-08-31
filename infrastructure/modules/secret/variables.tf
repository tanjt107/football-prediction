variable "secrets" {
  description = "A map of secret objects, each containing a name and the secret data, to be created in Google Secret Manager."
  type        = map(string)
  default     = {}
}

variable "project_id" {
  description = "The unique identifier of the Google Cloud project where the Secret Manager resources will be managed."
  type        = string
}
