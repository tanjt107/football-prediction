variable "roles" {
  description = "Roles to apply to service accounts by name."
  type        = map(list(string))
  default     = {}
}

variable "project_id" {
  description = "Project id where service account will be created."
  type        = string
}
