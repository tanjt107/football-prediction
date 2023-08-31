variable "source_directory" {
  description = "The local directory containing the function's source code. The contents of this directory will be archived and used as the source for the function."
  type        = string
}

variable "function_name" {
  description = "The name assigned to the Google Cloud Function."
  type        = string
}

variable "runtime" {
  description = "The programming language runtime environment in which the function will be executed."
  type        = string
  default     = "python311"
}

variable "entry_point" {
  description = "The name of the method in the function source code that will be invoked when the function is executed."
  type        = string
  default     = "main"
}

variable "bucket_name" {
  type        = string
  description = "The name of the Google Cloud Storage bucket used for storing the function's source code."
}

variable "timeout_s" {
  description = "The maximum duration in seconds allowed for the execution of the function."
  type        = number
  default     = 60
}

variable "available_memory" {
  description = "The amount of memory allocated for the function to use."
  type        = string
  default     = "256Mi"
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
  description = "The maximum number of concurrent instances of the function allowed to execute."
  type        = number
  default     = 100
}

variable "secret_environment_variables" {
  description = "A list of secret names (not the full secret IDs) to be assigned to the function as secret environment variables."
  type        = list(string)
  default     = []
}

variable "event_filters" {
  description = "A map of key-value pairs representing filters used to selectively trigger the function based on specific events."
  type        = map(string)
  default     = {}
}

variable "event_trigger_failure_policy" {
  description = "The retry policy for the function when a triggered event results in a failure."
  type        = string
  default     = "RETRY_POLICY_DO_NOT_RETRY"
}

variable "job_name" {
  type        = string
  description = "The name of the scheduled job to run"
}

variable "job_schedule" {
  type        = string
  description = "The job frequency, in cron syntax"
}

variable "job_paused" {
  type        = bool
  description = "Sets the job to a paused state"
  default     = false
}

variable "message_data" {
  type        = string
  description = "The data to send in the topic message."
  default     = "Tm9uZQ=="
}

variable "time_zone" {
  type        = string
  description = "The timezone to use in scheduler"
  default     = "Asia/Hong_Kong"
}

variable "topic_name" {
  type        = string
  description = "Name of pubsub topic connecting the scheduled job and the function"
}

variable "region" {
  type        = string
  description = "The region in which resources will be applied."
}

variable "project_id" {
  type        = string
  description = "The ID of the project where the resources will be created"
}
