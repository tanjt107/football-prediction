output "native_tables" {
  description = "Map of bigquery native table resources being provisioned."
  value       = google_bigquery_table.native_tables
}

output "external_tables" {
  description = "Map of BigQuery external table resources being provisioned."
  value       = google_bigquery_table.external_tables
}

output "routines" {
  description = "Map of BigQuery routines resources being provisioned."
  value       = google_bigquery_routine.routines
}
