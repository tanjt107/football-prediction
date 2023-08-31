module "project" {
  source = "../modules/project"

  name            = "Football Prediction ${var.environment}"
  project_id      = "football-prediction-${var.environment}"
  billing_account = var.billing_account
  activate_apis = [
    "bigquery.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudscheduler.googleapis.com",
    "compute.googleapis.com",
    "eventarc.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com"
  ]
  activate_api_identities = {
    "compute.googleapis.com" = ["roles/secretmanager.secretAccessor"]
    "storage.googleapis.com" = ["roles/pubsub.publisher"]
  }
}

module "buckets" {
  source = "../modules/storage"

  location   = var.region
  project_id = module.project.project_id
  names = [
    "footystats-league-list",
    "footystats-matches",
    "footystats-matches-transformed",
    "footystats-season",
    "footystats-teams",
    "solver",
    "gcf"
  ]
}

module "bigquery-footystats" {
  source = "../modules/bigquery"

  dataset_id = "footystats"
  location   = var.region
  project_id = module.project.project_id
  tables = {
    "league_list" = {
      schema        = file("../../bigquery/schema/footystats/league_list.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["footystats-league-list"]}/league_list.json"]
    },
    "matches" = {
      schema        = file("../../bigquery/schema/footystats/matches.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["footystats-matches"]}/*.json"]
    },
    "matches_transformed" = {
      schema        = file("../../bigquery/schema/footystats/matches_transformed.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["footystats-matches-transformed"]}/*.json"]
    },
    "season" = {
      schema        = file("../../bigquery/schema/footystats/season.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["footystats-season"]}/*.json"]
    }
    "teams" = {
      schema        = file("../../bigquery/schema/footystats/teams.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["footystats-teams"]}/*.json"]
    }
  }
  views = {
    "latest_season" = file("../../bigquery/routine/latest_season.sql")
  }
  routines = {
    "get_solver_matches" = {
      definition_body = templatefile("../../bigquery/routine/get_solver_matches.sql", { project_id = module.project.project_id })
      routine_type    = "TABLE_VALUED_FUNCTION"
      language        = "SQL"
      arguments = [
        {
          name      = "cut_off_year"
          data_type = jsonencode({ "typeKind" : "INT64" })
        },
        {
          name      = "inter_league_cut_off_year"
          data_type = jsonencode({ "typeKind" : "INT64" })
        }
      ]
    }
  }
}

module "bigquery-solver" {
  source = "../modules/bigquery"

  dataset_id = "solver"
  location   = var.region
  project_id = module.project.project_id
  tables = {
    "leagues" = {
      schema        = file("../../bigquery/schema/solver/leagues.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["solver"]}/leagues.json"]
    },
    "teams" = {
      schema        = file("../../bigquery/schema/solver/teams.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["solver"]}/teams.json"]
    }
  }
  routines = {
    "matchProbs" = {
      definition_body = file("../../bigquery/routine/matchProbs.js")
      routine_type    = "SCALAR_FUNCTION"
      language        = "JAVASCRIPT"
      return_type = jsonencode({
        "typeKind" : "ARRAY",
        "arrayElementType" : { "typeKind" : "FLOAT64" }
      })
      arguments = [
        {
          name      = "projScore1"
          data_type = jsonencode({ "typeKind" : "FLOAT64" })
        },
        {
          name      = "projScore2"
          data_type = jsonencode({ "typeKind" : "FLOAT64" })
        },
        {
          name      = "goalDiff"
          data_type = jsonencode({ "typeKind" : "INT64" })
        }
      ]
    }
  }
  views = {
    "team_ratings"     = file("../../bigquery/routine/team_ratings.sql")
    "upcoming_matches" = file("../../bigquery/routine/upcoming_matches.sql")
  }
}

module "api-key" {
  source = "../modules/secret"

  secrets    = { "FOOTYSTATS_API_KEY" = var.footystats_api_key }
  project_id = module.project.project_id
}

module "footystats-get-league-list" {
  source = "../modules/scheduled-function"

  function_name                = "footystats_get_league_list"
  bucket_name                  = module.buckets.names["gcf"]
  job_name                     = "footystats"
  job_schedule                 = "0 12,19 * * *"
  topic_name                   = "footystats"
  source_directory             = "../../function_source"
  secret_environment_variables = ["FOOTYSTATS_API_KEY"]
  environment_variables        = { "BUCKET_NAME" = module.buckets.names["footystats-league-list"] }
  region                       = var.region
  project_id                   = module.project.project_id
}

module "footystats-league-list-topic" {
  source = "../modules/pubsub"

  topic      = "footystats-league-list"
  project_id = module.project.project_id
}

module "footystats-publish-season-ids" {
  source = "../modules/event-function"

  function_name                = "footystats_publish_season_ids"
  bucket_name                  = module.buckets.names["gcf"]
  secret_environment_variables = ["FOOTYSTATS_API_KEY"]
  environment_variables        = { "TOPIC_NAME" = module.footystats-league-list-topic.id }
  event_type                   = "google.cloud.storage.object.v1.finalized"
  source_directory             = "../../function_source"
  region                       = var.region
  project_id                   = module.project.project_id
  event_filters = {
    attribute = "bucket"
    value     = module.buckets.names["footystats-league-list"]
  }
}

module "footystats-publish-season-ids-initial-load" {
  source = "../modules/scheduled-function"

  function_name                = "footystats_publish_season_ids_initial_load"
  bucket_name                  = module.buckets.names["gcf"]
  job_name                     = "footystats-initial-load"
  job_schedule                 = "0 8 1 * *"
  topic_name                   = "footystats-initial-load"
  source_directory             = "../../function_source"
  secret_environment_variables = ["FOOTYSTATS_API_KEY"]
  environment_variables        = { "TOPIC_NAME" = module.footystats-league-list-topic.id }
  event_trigger_failure_policy = "RETRY_POLICY_RETRY"
  region                       = var.region
  project_id                   = module.project.project_id
}

module "footystats-get-footystats" {
  source = "../modules/event-function"

  function_name                = "footystats_get_data"
  bucket_name                  = module.buckets.names["gcf"]
  secret_environment_variables = ["FOOTYSTATS_API_KEY"]
  event_type                   = "google.cloud.pubsub.topic.v1.messagePublished"
  topic_name                   = module.footystats-league-list-topic.id
  source_directory             = "../../function_source"
  region                       = var.region
  project_id                   = module.project.project_id
  environment_variables = {
    "MATCHES_BUCKET_NAME" = module.buckets.names["footystats-matches"],
    "SEASON_BUCKET_NAME"  = module.buckets.names["footystats-season"],
    "TEAMS_BUCKET_NAME"   = module.buckets.names["footystats-teams"]
  }
}

module "footystats-transform-matches" {
  source = "../modules/event-function"

  function_name         = "footystats_transform_matches"
  bucket_name           = module.buckets.names["gcf"]
  environment_variables = { "BUCKET_NAME" = module.buckets.names["footystats-matches-transformed"] }
  event_type            = "google.cloud.storage.object.v1.finalized"
  source_directory      = "../../function_source"
  region                = var.region
  project_id            = module.project.project_id
  event_filters = {
    attribute = "bucket"
    value     = module.buckets.names["footystats-matches"]
  }
}

module "solver" {
  source = "../modules/scheduled-function"

  function_name    = "solver"
  bucket_name      = module.buckets.names["gcf"]
  timeout_s        = 540
  available_memory = "1Gi"
  available_cpu    = 2
  job_name         = "solver"
  job_schedule     = "30 12,19 * * *"
  topic_name       = "solver"
  source_directory = "../../function_source"
  environment_variables = {
    "BOUND"       = 10
    "BUCKET_NAME" = module.buckets.names["solver"]
  }
  region     = var.region
  project_id = module.project.project_id
}
