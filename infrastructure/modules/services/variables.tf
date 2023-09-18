variable "project_id" {
  description = "The GCP project you want to enable APIs on."
  type        = string
}

variable "enable_apis" {
  description = "Whether to actually enable the APIs."
  type        = bool
  default     = true
}

variable "activate_apis" {
  description = "The list of apis to activate within the project."
  type        = list(string)
  default     = []
}

variable "activate_api_identities" {
  description = "The list of service identities (Google Managed service account for the API) to force-create for the project (e.g. in order to grant additional roles)."
  type        = map(list(string))
  default     = {}
}

variable "activate_api_sleep_duration" {
  description = "The duration to sleep in seconds before activating the apis."
  type        = string
  default     = "5m"
}
