variable "name" {
  description = "The name for the project."
  type        = string
}

variable "project_id" {
  description = "The ID to give the project."
  type        = string
}

variable "billing_account" {
  description = "The ID of the billing account to associate this project with."
  type        = string
}

variable "activate_apis" {
  description = "The list of apis to activate within the project"
  type        = list(string)
  default     = []
}

variable "activate_api_identities" {
  description = "The list of service identities (Google Managed service account for the API) to force-create for the project (e.g. in order to grant additional roles)."
  type        = map(list(string))
  default     = {}
}

variable "activate_api_sleep_duration" {
  description = "The duration to sleep after activating the apis."
  type        = string
  default     = "5m"
}
