variable "secrets" {
  description = "A map of objects, which include the name and the secret."
  type        = map(string)
  default     = {}
}

variable "project_id" {
  description = "The project ID to manage the Secret Manager resources."
  type        = string
}
