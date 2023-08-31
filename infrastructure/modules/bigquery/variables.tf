variable "dataset_id" {
  description = "Unique ID for the dataset being provisioned."
  type        = string
}

variable "tables" {
  description = "A list of objects which include table_id, expiration_time, external_data_configuration, and labels."
  type = map(object({
    schema        = string,
    source_format = string,
    source_uris   = list(string)
  }))
  default = {}
}

variable "views" {
  description = "A list of objects which include view_id and view query"
  type        = map(string)
  default     = {}
}

variable "routines" {
  description = "A list of objects which include routine_id, routine_type, routine_language, definition_body, return_type, routine_description and arguments."
  default     = {}
  type = map(object({
    definition_body = string,
    routine_type    = string,
    language        = string,
    return_type     = optional(string),
    arguments = list(object({
      name      = string,
      data_type = string
    })),
  }))
}

variable "location" {
  description = "The regional location for the dataset"
  type        = string
}

variable "project_id" {
  description = "Project where the dataset and table are created"
  type        = string
}

variable "deletion_protection" {
  description = "Whether or not to allow Terraform to destroy the instance. Unless this field is set to false in Terraform state, a terraform destroy or terraform apply that would delete the instance will fail"
  type        = bool
  default     = true
}
