module "pubsub" {
  source = "../pubsub"

  topic      = var.topic_name
  project_id = var.project_id
}

resource "google_cloud_scheduler_job" "job" {
  name      = var.job_name
  schedule  = var.job_schedule
  time_zone = var.time_zone
  paused    = var.job_paused
  region    = var.region
  project   = var.project_id

  pubsub_target {
    topic_name = "projects/${var.project_id}/topics/${module.pubsub.topic}"
    data       = base64encode(var.message_data)
  }
}

module "function" {
  source = "../event-function"

  name                         = var.function_name
  runtime                      = var.function_runtime
  entry_point                  = var.function_entry_point
  bucket_name                  = var.bucket_name
  timeout_s                    = var.function_timeout_s
  available_memory             = var.function_available_memory
  available_cpu                = var.function_available_cpu
  environment_variables        = var.function_environment_variables
  max_instances                = var.function_max_instances
  secret_environment_variables = var.function_secret_environment_variables
  event_type                   = "google.cloud.pubsub.topic.v1.messagePublished"
  event_filters                = var.function_event_filters
  topic_name                   = module.pubsub.id
  event_trigger_failure_policy = var.function_event_trigger_failure_policy
  source_directory             = var.function_source_directory
  region                       = var.region
  project_id                   = var.project_id
}
