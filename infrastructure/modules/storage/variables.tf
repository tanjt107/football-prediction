variable "names" {
  description = "Bucket name suffixes."
  type        = list(string)
}

variable "location" {
  description = "Bucket location."
  type        = string
}

variable "project_id" {
  description = "Bucket project id."
  type        = string
}

variable "force_destroy" {
  description = "Defaults to false."
  type        = bool
  default     = false
}

variable "files" {
  description = "Map of lowercase unprefixed name => list of file objects."
  type        = map(list(string))
  default     = {}
}
