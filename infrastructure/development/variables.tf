variable "environment" {
  default     = "dev"
  type        = string
  description = "The environment to prepare (e.g., 'dev', 'prod')."
}

variable "billing_account" {
  type        = string
  description = "The ID of the billing account to associate this project with"
}

variable "region" {
  default     = "asia-east2"
  type        = string
  description = "Region where resources are created."
}
