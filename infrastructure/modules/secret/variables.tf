variable "secrets" {
  description = "A map of objects, which include the name and the secret."
  type        = map(string)
  default     = {}
}

variable "project_id" {
  description = "Project where the secrets are created."
  type        = string
}
