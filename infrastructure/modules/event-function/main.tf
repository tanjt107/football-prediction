data "archive_file" "file" {
  type        = "zip"
  output_path = "${var.source_directory}/${var.function_name}.zip"
  source_dir  = "${var.source_directory}/${var.function_name}"
}

resource "google_storage_bucket_object" "object" {
  bucket = var.bucket_name
  name   = "${var.function_name}.zip"
  source = data.archive_file.file.output_path
}

resource "google_cloudfunctions2_function" "function" {
  name     = var.function_name
  location = var.region
  project  = var.project_id

  build_config {
    runtime     = var.runtime
    entry_point = var.entry_point
    source {
      storage_source {
        bucket = var.bucket_name
        object = google_storage_bucket_object.object.name
      }
    }
  }

  service_config {
    timeout_seconds       = var.timeout_s
    available_memory      = var.available_memory
    available_cpu         = var.available_cpu
    environment_variables = var.environment_variables
    max_instance_count    = var.max_instances
    dynamic "secret_environment_variables" {
      for_each = var.secret_environment_variables
      content {
        key        = secret_environment_variables.value
        project_id = var.project_id
        secret     = secret_environment_variables.value
        version    = "latest"
      }
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = var.event_type
    dynamic "event_filters" {
      for_each = length(var.event_filters) > 0 ? [1] : []
      content {
        attribute = var.event_filters["attribute"]
        value     = var.event_filters["value"]
      }
    }
    pubsub_topic = var.topic_name
    retry_policy = var.event_trigger_failure_policy
  }
}
