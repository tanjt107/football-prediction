variable "dataset_id" {
  description = "Unique ID for the dataset being provisioned."
  type        = string
}

variable "tables" {
  description = "A map of objects which include table_id and schema."
  type        = map(string)
  default     = {}
}

variable "external_tables" {
  description = "A map of objects which include table_id and external_data_configuration."
  type = map(object({
    schema        = string,
    source_format = string,
    source_uris   = optional(list(string))
    hive_partitioning_options = optional(object({
      source_uri_prefix = string,
    }))
  }))
  default = {}
}

variable "views" {
  description = "A map of objects which include view_id and view query."
  type        = map(string)
  default     = {}
}

variable "routines" {
  description = "A map of objects which include routine_id, routine_type, routine_language, definition_body, return_type and arguments."
  type = map(object({
    definition_body = string,
    routine_type    = string,
    language        = string,
    return_type     = optional(string),
    arguments = optional(list(object({
      name      = string,
      data_type = string
    }))),
  }))
  default = {}
}

variable "scheduled_queries" {
  description = "Data transfer configuration for creating scheduled queries."
  type        = map(any)
  default     = {}
}

variable "service_account_name" {
  description = "Default service account to apply to the scheduled queries."
  type        = string
  default     = null
}

variable "location" {
  description = "The regional location for the dataset."
  type        = string
}

variable "project_id" {
  description = "Project where the dataset and table are created."
  type        = string
}

variable "deletion_protection" {
  description = "Whether or not to allow Terraform to destroy the instance. Unless this field is set to false in Terraform state, a terraform destroy or terraform apply that would delete the instance will fail."
  type        = bool
  default     = true
}
