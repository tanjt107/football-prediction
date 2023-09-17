variable "service_accounts" {
  default = {}
  type    = map(list(string))
}

variable "project_id" {
  type        = string
  description = "Project id where service account will be created."
}
