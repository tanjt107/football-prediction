variable "function_name" {
  description = "The name to apply to the function."
  type        = string
}

variable "function_runtime" {
  description = "The runtime in which the function will be executed."
  type        = string
  default     = "python311"
}

variable "function_entry_point" {
  description = "The name of a method in the function source which will be invoked when the function is executed."
  type        = string
  default     = "main"
}

variable "docker_repository" {
  type        = string
  default     = null
  description = "User managed repository created in Artifact Registry optionally with a customer managed encryption key."
}

variable "bucket_name" {
  type        = string
  description = "The name to apply to the bucket."
}

variable "function_timeout_s" {
  description = "The amount of time in seconds allotted for the execution of the function."
  type        = number
  default     = 60
}

variable "function_available_memory" {
  description = "The amount of memory in megabytes allotted for the function to use."
  type        = string
  default     = "256Mi"
}

variable "function_available_cpu" {
  description = "The number of CPUs used in a single container instance."
  type        = string
  default     = "0.1666"
}

variable "function_environment_variables" {
  description = "A set of key/value environment variable pairs to assign to the function."
  type        = map(string)
  default     = {}
}

variable "function_max_instances" {
  description = "The maximum number of parallel executions of the function."
  type        = number
  default     = 100
}

variable "function_secret_environment_variables" {
  description = "A list of secret names (not the full secret IDs) to be assigned to the function as secret environment variables."
  type        = list(string)
  default     = []
}

variable "function_event_filters" {
  description = "A map of key-value pairs representing filters used to selectively trigger the function based on specific events."
  type        = map(string)
  default     = {}
}

variable "function_event_trigger_failure_policy" {
  description = "The retry policy for the function when a triggered event results in a failure."
  type        = string
  default     = "RETRY_POLICY_DO_NOT_RETRY"
}

variable "function_source_directory" {
  description = "The contents of this directory will be archived and used as the function source."
  type        = string
}

variable "job_name" {
  description = "The name of the scheduled job to run."
  type        = string
}

variable "job_schedule" {
  description = "The job frequency, in cron syntax."
  type        = string
}

variable "job_paused" {
  description = "Sets the job to a paused state."
  type        = bool
  default     = false
}

variable "message_data" {
  description = "The data to send in the topic message."
  type        = string
  default     = "Hello World"
}

variable "topic_name" {
  description = "Name of pubsub topic connecting the scheduled job and the function."
  type        = string
}

variable "region" {
  type        = string
  description = "The region in which resources will be applied."
}

variable "project_id" {
  type        = string
  description = "The ID of the project where the resources will be created."
}
