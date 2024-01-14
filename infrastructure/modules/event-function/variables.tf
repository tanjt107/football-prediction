variable "name" {
  description = "The name to apply to any nameable resources."
  type        = string
}

variable "runtime" {
  description = "The runtime in which the function will be executed."
  type        = string
  default     = "python311"
}

variable "entry_point" {
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
  description = "The name of the Google Cloud Storage bucket used for storing the function's source code."
  type        = string
}

variable "timeout_s" {
  description = "The amount of time in seconds allotted for the execution of the function."
  type        = number
  default     = 60
}

variable "available_memory" {
  description = "The amount of memory allotted for the function to use."
  type        = string
  default     = "256Mi"
}

variable "max_instance_request_concurrency" {
  description = "The maximum number of concurrent requests that each instance can receive."
  type        = number
  default     = 1
}

variable "available_cpu" {
  description = "The number of CPUs used in a single container instance."
  type        = string
  default     = "0.1666"
}

variable "environment_variables" {
  description = "A set of key/value environment variable pairs to assign to the function."
  type        = map(string)
  default     = {}
}

variable "max_instances" {
  description = "The maximum number of parallel executions of the function."
  type        = number
  default     = 100
}

variable "secret_environment_variables" {
  description = "A list of secret names (not the full secret IDs) to be assigned to the function as secret environment variables."
  type        = list(string)
  default     = []
}

variable "event_type" {
  description = "The type of event to observe."
  type        = string
}

variable "event_filters" {
  description = "A map of key-value pairs representing filters used to selectively trigger the function based on specific events."
  type        = map(string)
  default     = {}
}

variable "topic_name" {
  description = "The name of a Pub/Sub topic that will be used as the transport topic for the event delivery."
  type        = string
  default     = null
}

variable "event_trigger_failure_policy" {
  description = "A toggle to determine if the function should be retried on failure."
  type        = string
  default     = "RETRY_POLICY_DO_NOT_RETRY"
}

variable "source_directory" {
  description = "The pathname of the directory which contains the function source code."
  type        = string
}

variable "region" {
  description = "The region in which resources will be applied."
  type        = string
}

variable "project_id" {
  description = "The ID of the project to which resources will be applied."
  type        = string
}

