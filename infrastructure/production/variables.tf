variable "environment" {
  description = "The environment to prepare (e.g., 'dev', 'prod')."
  type        = string
  default     = "dev"
}

variable "billing_account" {
  description = "The ID of the billing account to associate this project with"
  type        = string
}

variable "region" {
  description = "Region where resources are created."
  type        = string
  default     = "asia-east2"
}
