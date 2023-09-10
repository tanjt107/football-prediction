resource "google_bigquery_dataset" "dataset" {
  dataset_id                 = var.dataset_id
  location                   = var.location
  project                    = var.project_id
  delete_contents_on_destroy = var.deletion_protection
}

resource "google_bigquery_table" "main" {
  for_each            = var.tables
  dataset_id          = google_bigquery_dataset.dataset.dataset_id
  table_id            = each.key
  schema              = each.value["schema"]
  project             = var.project_id
  deletion_protection = var.deletion_protection
}

resource "google_bigquery_table" "external_table" {
  for_each            = var.external_tables
  dataset_id          = google_bigquery_dataset.dataset.dataset_id
  table_id            = each.key
  project             = var.project_id
  deletion_protection = var.deletion_protection

  external_data_configuration {
    autodetect    = false
    schema        = each.value["schema"]
    source_format = each.value["source_format"]
    source_uris   = each.value["source_uris"]
  }
}

resource "google_bigquery_table" "view" {
  for_each            = var.views
  dataset_id          = google_bigquery_dataset.dataset.dataset_id
  table_id            = each.key
  project             = var.project_id
  deletion_protection = var.deletion_protection

  view {
    query          = each.value
    use_legacy_sql = false
  }

  depends_on = [google_bigquery_table.external_table]
}

resource "google_bigquery_routine" "routine" {
  for_each        = var.routines
  dataset_id      = google_bigquery_dataset.dataset.dataset_id
  routine_id      = each.key
  definition_body = each.value["definition_body"]
  routine_type    = each.value["routine_type"]
  language        = each.value["language"]
  return_type     = each.value["return_type"]
  project         = var.project_id

  dynamic "arguments" {
    for_each = each.value["arguments"]
    content {
      name      = arguments.value["name"]
      data_type = arguments.value["data_type"]
    }
  }

  depends_on = [google_bigquery_table.external_table]
}
