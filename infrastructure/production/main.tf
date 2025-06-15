module "project" {
  source = "../modules/project"

  name            = "Football Prediction ${var.environment}"
  project_id      = "football-prediction-${var.environment}"
  billing_account = var.billing_account
  activate_apis = [
    "bigquery.googleapis.com",
    "bigquerydatatransfer.googleapis.com",
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
    "bigquerydatatransfer.googleapis.com" = ["roles/iam.serviceAccountTokenCreator"]
    "compute.googleapis.com"              = ["roles/secretmanager.secretAccessor"]
    "storage.googleapis.com"              = ["roles/pubsub.publisher"]
  }
}

module "buckets" {
  source = "../modules/storage"

  suffix     = "${module.project.project_number}-${var.region}"
  location   = var.region
  project_id = module.project.project_id
  names = [
    "footystats-league-list",
    "footystats-matches",
    "footystats-matches-transformed",
    "footystats-seasons",
    "footystats-tables",
    "footystats-teams",
    "hkjc-odds",
    "hkjc-results",
    "hkjc-team-list",
    "manual",
    "solver",
    "simulation",
    "gcf"
  ]
  files = {
    manual = [
      "../../assets/leagues.csv",
      "../../assets/teams.csv",
      "../../assets/simulation/Asia AFC Champions League.json",
      "../../assets/simulation/Asia AFC Cup.json",
      "../../assets/simulation/China China League One.json",
      "../../assets/simulation/China Chinese Super League.json",
      "../../assets/simulation/England Premier League.json",
      "../../assets/simulation/Europe UEFA Champions League.json",
      "../../assets/simulation/France Ligue 1.json",
      "../../assets/simulation/Germany Bundesliga.json",
      "../../assets/simulation/Hong Kong Hong Kong Premier League.json",
      "../../assets/simulation/International Asian Cup Qualification.json",
      "../../assets/simulation/International FIFA Club World Cup.json",
      "../../assets/simulation/International WC Qualification Asia.json",
      "../../assets/simulation/Italy Serie A.json",
      "../../assets/simulation/Japan J1 League.json",
      "../../assets/simulation/Spain La Liga.json",
    ]
  }
}

module "api-key" {
  source = "../modules/secret"

  secrets    = { "FOOTYSTATS_API_KEY" = file("../../credentials/footystats.txt") }
  project_id = module.project.project_id
}

/*****************************************
  footystats
 *****************************************/
module "footystats-league-list-topic" {
  source = "../modules/pubsub"

  topic      = "footystats-league-list"
  project_id = module.project.project_id
}

resource "google_artifact_registry_repository" "repository" {
  repository_id = "gcf"
  format        = "DOCKER"
  location      = var.region
  project       = module.project.project_id
}

module "footystats-delta-load" {
  source = "../modules/scheduled-function"

  function_name                  = "footystats_publish_season_ids_delta"
  docker_repository              = google_artifact_registry_repository.repository.id
  bucket_name                    = module.buckets.names["gcf"]
  job_name                       = "footystats-delta-load"
  job_schedule                   = "35 */8 * * *"
  topic_name                     = "footystats-delta-load"
  function_source_directory      = "../../src/function"
  function_environment_variables = { "TOPIC_NAME" = module.footystats-league-list-topic.id }
  region                         = var.region
  project_id                     = module.project.project_id
}

module "footystats-get-league-list" {
  source = "../modules/scheduled-function"

  function_name                         = "footystats_get_league_list"
  docker_repository                     = google_artifact_registry_repository.repository.id
  bucket_name                           = module.buckets.names["gcf"]
  job_name                              = "footystats-get-league-list"
  job_schedule                          = "0 23 * * 1"
  topic_name                            = "footystats-get-league-list"
  function_source_directory             = "../../src/function"
  function_secret_environment_variables = [module.api-key.secret_ids["FOOTYSTATS_API_KEY"]]
  function_environment_variables        = { BUCKET_NAME = module.buckets.names["footystats-league-list"] }
  region                                = var.region
  project_id                            = module.project.project_id
}

module "footystats-initial-load-matches" {
  source = "../modules/scheduled-function"

  function_name                  = "footystats_publish_season_ids_initial"
  docker_repository              = google_artifact_registry_repository.repository.id
  bucket_name                    = module.buckets.names["gcf"]
  job_name                       = "footystats-initial-load-matches"
  job_schedule                   = "5 23 * * 1"
  message_data                   = "matches"
  topic_name                     = "footystats-initial-load"
  function_source_directory      = "../../src/function"
  function_environment_variables = { "TOPIC_NAME" = module.footystats-league-list-topic.id }
  region                         = var.region
  project_id                     = module.project.project_id
}

resource "google_cloud_scheduler_job" "footystats-initial-load-season" {
  name     = "footystats-initial-load-season"
  schedule = "15 23 * * 1"
  region   = var.region
  project  = module.project.project_id

  pubsub_target {
    topic_name = "projects/${module.project.project_id}/topics/${module.footystats-initial-load-matches.pubsub_topic_name}"
    data       = base64encode("season")
  }
}

resource "google_cloud_scheduler_job" "footystats-initial-load-tables" {
  name     = "footystats-initial-load-tables"
  schedule = "25 23 * * 1"
  region   = var.region
  project  = module.project.project_id

  pubsub_target {
    topic_name = "projects/${module.project.project_id}/topics/${module.footystats-initial-load-matches.pubsub_topic_name}"
    data       = base64encode("tables")
  }
}

resource "google_cloud_scheduler_job" "footystats-initial-load-teams" {
  name     = "footystats-initial-load-teams"
  schedule = "35 23 * * 1"
  region   = var.region
  project  = module.project.project_id

  pubsub_target {
    topic_name = "projects/${module.project.project_id}/topics/${module.footystats-initial-load-matches.pubsub_topic_name}"
    data       = base64encode("teams")
  }
}

module "footystats-get-footystats" {
  source = "../modules/event-function"

  name                             = "footystats_get_data"
  docker_repository                = google_artifact_registry_repository.repository.id
  bucket_name                      = module.buckets.names["gcf"]
  available_cpu                    = 1
  available_memory                 = "512Mi"
  max_instance_request_concurrency = 80
  secret_environment_variables     = [module.api-key.secret_ids["FOOTYSTATS_API_KEY"]]
  event_type                       = "google.cloud.pubsub.topic.v1.messagePublished"
  topic_name                       = module.footystats-league-list-topic.id
  source_directory                 = "../../src/function"
  event_trigger_failure_policy     = "RETRY_POLICY_RETRY"
  region                           = var.region
  project_id                       = module.project.project_id
  environment_variables = {
    MATCHES_BUCKET_NAME = module.buckets.names["footystats-matches"]
    SEASONS_BUCKET_NAME = module.buckets.names["footystats-seasons"]
    TABLES_BUCKET_NAME  = module.buckets.names["footystats-tables"]
    TEAMS_BUCKET_NAME   = module.buckets.names["footystats-teams"]
  }
}

module "footystats-transform-matches" {
  source = "../modules/event-function"

  name                  = "footystats_transform_matches"
  docker_repository     = google_artifact_registry_repository.repository.id
  bucket_name           = module.buckets.names["gcf"]
  environment_variables = { BUCKET_NAME = module.buckets.names["footystats-matches-transformed"] }
  event_type            = "google.cloud.storage.object.v1.finalized"
  source_directory      = "../../src/function"
  region                = var.region
  project_id            = module.project.project_id
  event_filters = {
    attribute = "bucket"
    value     = module.buckets.names["footystats-matches"]
  }
}

module "bigquery-footystats" {
  source = "../modules/bigquery"

  dataset_id = "footystats"
  location   = var.region
  project_id = module.project.project_id
  external_tables = {
    league_list = {
      schema        = file("../../src/bigquery/schema/footystats/league_list.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["footystats-league-list"]}/league_list.json"]
    }
    matches = {
      schema                    = file("../../src/bigquery/schema/footystats/matches.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["footystats-matches"]}/*/matches.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["footystats-matches"]}/{_COUNTRY:STRING}/{_NAME:STRING}/{_YEAR:STRING}/{_SEASON_ID:INTEGER}" }
    }
    matches_transformed = {
      schema                    = file("../../src/bigquery/schema/footystats/matches_transformed.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["footystats-matches-transformed"]}/*/matches.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["footystats-matches-transformed"]}/{_COUNTRY:STRING}/{_NAME:STRING}/{_YEAR:STRING}/{_SEASON_ID:INTEGER}" }
    }
    seasons = {
      schema                    = file("../../src/bigquery/schema/footystats/seasons.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["footystats-seasons"]}/*/season.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["footystats-seasons"]}/{_COUNTRY:STRING}/{_NAME:STRING}/{_YEAR:STRING}/{_SEASON_ID:INTEGER}" }
    }
    tables = {
      schema                    = file("../../src/bigquery/schema/footystats/tables.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["footystats-tables"]}/*/tables.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["footystats-tables"]}/{_COUNTRY:STRING}/{_NAME:STRING}/{_YEAR:STRING}/{_SEASON_ID:INTEGER}" }
    }
    teams = {
      schema                    = file("../../src/bigquery/schema/footystats/teams.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["footystats-teams"]}/*/teams.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["footystats-teams"]}/{_COUNTRY:STRING}/{_NAME:STRING}/{_YEAR:STRING}/{_SEASON_ID:INTEGER}" }
    }
  }
  routines = {
    get_season_id_delta = {
      definition_body = templatefile("../../src/bigquery/sql/footystats/get_season_id_delta.sql", { project_id = module.project.project_id })
      routine_type    = "TABLE_VALUED_FUNCTION"
      language        = "SQL"
    }
    get_season_id_initial = {
      definition_body = templatefile("../../src/bigquery/sql/footystats/get_season_id_initial.sql", { project_id = module.project.project_id })
      routine_type    = "TABLE_VALUED_FUNCTION"
      language        = "SQL"
    }
  }
}

/*****************************************
  manual
 *****************************************/
module "bigquery-manual" {
  source = "../modules/bigquery"

  dataset_id = "manual"
  location   = var.region
  project_id = module.project.project_id
  external_tables = {
    teams = {
      schema        = file("../../src/bigquery/schema/manual/teams.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/teams.csv"]
    }
    leagues = {
      schema        = file("../../src/bigquery/schema/manual/leagues.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/leagues.csv"]
    }
  }
}


/*****************************************
  hkjc
 *****************************************/
module "hkjc-get-odds" {
  source = "../modules/scheduled-function"

  function_name                         = "hkjc_get_odds"
  docker_repository                     = google_artifact_registry_repository.repository.id
  bucket_name                           = module.buckets.names["gcf"]
  job_name                              = "hkjc-odds"
  job_schedule                          = "55 */8 * * *"
  topic_name                            = "hkjc-odds"
  function_source_directory             = "../../src/function"
  function_event_trigger_failure_policy = "RETRY_POLICY_RETRY"
  function_environment_variables = {
    BUCKET_NAME = module.buckets.names["hkjc-odds"]
    ODDS_TYPES  = jsonencode(["HAD", "HDC"])
  }
  region     = var.region
  project_id = module.project.project_id
}

module "hkjc-get-team-list" {
  source = "../modules/scheduled-function"

  function_name                  = "hkjc_get_team_list"
  docker_repository              = google_artifact_registry_repository.repository.id
  bucket_name                    = module.buckets.names["gcf"]
  job_name                       = "hkjc-get-team-list"
  job_schedule                   = "30 23 * * *"
  topic_name                     = "hkjc-team-list"
  function_source_directory      = "../../src/function"
  function_environment_variables = { BUCKET_NAME = module.buckets.names["hkjc-team-list"] }
  region                         = var.region
  project_id                     = module.project.project_id
}

module "hkjc-get-results" {
  source = "../modules/scheduled-function"

  function_name                  = "hkjc_get_results"
  docker_repository              = google_artifact_registry_repository.repository.id
  bucket_name                    = module.buckets.names["gcf"]
  job_name                       = "hkjc-get-results"
  job_schedule                   = "30 18 * * *"
  topic_name                     = "hkjc-results"
  function_source_directory      = "../../src/function"
  function_environment_variables = { BUCKET_NAME = module.buckets.names["hkjc-results"] }
  region                         = var.region
  project_id                     = module.project.project_id
}

module "bigquery-hkjc" {
  source = "../modules/bigquery"

  dataset_id = "hkjc"
  location   = var.region
  project_id = module.project.project_id
  external_tables = {
    odds = {
      schema                    = file("../../src/bigquery/schema/hkjc/odds.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["hkjc-odds"]}/*/odds.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["hkjc-odds"]}/{_TIMESTAMP:TIMESTAMP}" }
    },
    results = {
      schema                    = file("../../src/bigquery/schema/hkjc/results.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["hkjc-results"]}/*/results.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["hkjc-results"]}/{_DATE:DATE}" }
    },
    teams = {
      schema        = file("../../src/bigquery/schema/hkjc/teams.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["hkjc-team-list"]}/teamList.json"]
    }
  }
  views = {
    odds_clean  = file("../../src/bigquery/sql/hkjc/odds_clean.sql")
    odds_latest = file("../../src/bigquery/sql/hkjc/odds_latest.sql")
    odds_today  = file("../../src/bigquery/sql/hkjc/odds_today.sql")
    scores      = file("../../src/bigquery/sql/hkjc/scores.sql")
  }
}

/*****************************************
  master
 *****************************************/
module "service-accounts" {
  source = "../modules/service-accounts"

  project_id = module.project.project_id
  roles = {
    bigquery-scheduled-queries = [
      "roles/bigquery.admin",
      "roles/storage.objectViewer"
    ]
  }
}

module "bigquery-master" {
  source = "../modules/bigquery"

  dataset_id           = "master"
  service_account_name = module.service-accounts.emails["bigquery-scheduled-queries"]
  location             = var.region
  project_id           = module.project.project_id
  tables = {
    leagues = file("../../src/bigquery/schema/master/leagues.json")
    teams   = file("../../src/bigquery/schema/master/teams.json")
  }
  scheduled_queries = {
    leagues = {
      schedule = "every monday 23:40"
      query    = file("../../src/bigquery/sql/master/leagues.sql")
    }
    teams = {
      schedule = "every monday 23:40"
      query    = file("../../src/bigquery/sql/master/teams.sql")
    }
  }

  depends_on = [
    module.bigquery-footystats.external_tables,
    module.bigquery-hkjc.external_tables,
    module.bigquery-manual.external_tables
  ]
}

/*****************************************
  solver
 *****************************************/
module "pubsub-solver" {
  source = "../modules/pubsub"

  topic      = "simulate-solver"
  project_id = module.project.project_id
}

module "solver-publish-messages" {
  source = "../modules/scheduled-function"

  function_name                  = "solver_publish_messages"
  docker_repository              = google_artifact_registry_repository.repository.id
  bucket_name                    = module.buckets.names["gcf"]
  job_name                       = "solver"
  job_schedule                   = "45 */8 * * *"
  topic_name                     = "solver"
  function_source_directory      = "../../src/function"
  function_environment_variables = { TOPIC_NAME = module.pubsub-solver.id }
  region                         = var.region
  project_id                     = module.project.project_id
}

module "solver" {
  source = "../modules/event-function"

  name                  = "solver"
  docker_repository     = google_artifact_registry_repository.repository.id
  bucket_name           = module.buckets.names["gcf"]
  timeout_s             = 540
  available_memory      = "1Gi"
  available_cpu         = 2
  environment_variables = { BUCKET_NAME = module.buckets.names["solver"] }
  event_type            = "google.cloud.pubsub.topic.v1.messagePublished"
  topic_name            = module.pubsub-solver.id
  source_directory      = "../../src/function"
  region                = var.region
  project_id            = module.project.project_id
}

module "bigquery-solver" {
  source = "../modules/bigquery"

  dataset_id = "solver"
  location   = var.region
  project_id = module.project.project_id
  external_tables = {
    leagues = {
      schema                    = file("../../src/bigquery/schema/solver/leagues.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["solver"]}/*/leagues.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["solver"]}/{_TYPE:STRING}/{_DATE_UNIX:INTEGER}" }
    }
    teams = {
      schema                    = file("../../src/bigquery/schema/solver/teams.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["solver"]}/*/teams.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["solver"]}/{_TYPE:STRING}/{_DATE_UNIX:INTEGER}" }
    }
  }
  routines = {
    get_matches = {
      definition_body = templatefile("../../src/bigquery/sql/solver/get_matches.sql", { project_id = module.project.project_id })
      routine_type    = "TABLE_VALUED_FUNCTION"
      language        = "SQL"
      arguments = [
        {
          name      = "league_type"
          data_type = jsonencode({ "typeKind" : "STRING" })
        },
        {
          name      = "max_time"
          data_type = jsonencode({ "typeKind" : "INT64" })
        }
      ]
    }
    get_messages = {
      definition_body = templatefile("../../src/bigquery/sql/solver/get_messages.sql", { project_id = module.project.project_id })
      routine_type    = "TABLE_VALUED_FUNCTION"
      language        = "SQL"
    }
  }
  views = {
    leagues_latest  = file("../../src/bigquery/sql/solver/leagues_latest.sql")
    teams_7d        = file("../../src/bigquery/sql/solver/teams_7d.sql")
    teams_latest    = file("../../src/bigquery/sql/solver/teams_latest.sql")
    team_ratings_7d = file("../../src/bigquery/sql/solver/team_ratings_7d.sql")
    team_ratings    = file("../../src/bigquery/sql/solver/team_ratings.sql")
  }

  depends_on = [module.bigquery-master.native_tables]
}

/*****************************************
  simulation
 *****************************************/
module "pubsub-simulate-tournament" {
  source = "../modules/pubsub"

  topic      = "simulate-tournament"
  project_id = module.project.project_id
}

module "simulation-publish-message" {
  source = "../modules/event-function"

  name                  = "simulation_publish_messages"
  docker_repository     = google_artifact_registry_repository.repository.id
  bucket_name           = module.buckets.names["gcf"]
  environment_variables = { TOPIC_NAME = module.pubsub-simulate-tournament.id }
  event_type            = "google.cloud.storage.object.v1.finalized"
  source_directory      = "../../src/function"
  region                = var.region
  project_id            = module.project.project_id
  event_filters = {
    attribute = "bucket"
    value     = module.buckets.names["solver"]
  }
}

module "simulate-tournament" {
  source = "../modules/event-function"

  name              = "simulate_tournament"
  docker_repository = google_artifact_registry_repository.repository.id
  bucket_name       = module.buckets.names["gcf"]
  timeout_s         = 300
  environment_variables = {
    INPUT_BUCKET_NAME  = module.buckets.names["manual"],
    RESULT_BUCKET_NAME = module.buckets.names["simulation"]
  }
  event_type       = "google.cloud.pubsub.topic.v1.messagePublished"
  topic_name       = module.pubsub-simulate-tournament.id
  source_directory = "../../src/function"
  region           = var.region
  project_id       = module.project.project_id
}

module "bigquery-simulation" {
  source = "../modules/bigquery"

  dataset_id = "simulation"
  location   = var.region
  project_id = module.project.project_id
  external_tables = {
    leagues = {
      schema                    = file("../../src/bigquery/schema/simulation/leagues.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["simulation"]}/*/league.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["simulation"]}/{_LEAGUE:STRING}/{_DATE_UNIX:INTEGER}" }
    }
  }
  routines = {
    get_avg_goal_home_adv = {
      definition_body = templatefile("../../src/bigquery/sql/simulation/get_avg_goal_home_adv.sql", { project_id = module.project.project_id })
      routine_type    = "TABLE_VALUED_FUNCTION"
      language        = "SQL"
      arguments = [
        {
          name      = "league"
          data_type = jsonencode({ "typeKind" : "STRING" })
        }
      ]
    }
    get_groups = {
      definition_body = templatefile("../../src/bigquery/sql/simulation/get_groups.sql", { project_id = module.project.project_id })
      routine_type    = "TABLE_VALUED_FUNCTION"
      language        = "SQL"
      arguments = [
        {
          name      = "league"
          data_type = jsonencode({ "typeKind" : "STRING" })
        }
      ]
    }
    get_matches = {
      definition_body = templatefile("../../src/bigquery/sql/simulation/get_matches.sql", { project_id = module.project.project_id })
      routine_type    = "TABLE_VALUED_FUNCTION"
      language        = "SQL"
      arguments = [
        {
          name      = "league"
          data_type = jsonencode({ "typeKind" : "STRING" })
        }
      ]
    }
    get_messages = {
      definition_body = templatefile("../../src/bigquery/sql/simulation/get_messages.sql", { project_id = module.project.project_id })
      routine_type    = "TABLE_VALUED_FUNCTION"
      language        = "SQL"
      arguments = [
        {
          name      = "type"
          data_type = jsonencode({ "typeKind" : "STRING" })
        }
      ]
    }
    get_teams = {
      definition_body = templatefile("../../src/bigquery/sql/simulation/get_teams.sql", { project_id = module.project.project_id })
      routine_type    = "TABLE_VALUED_FUNCTION"
      language        = "SQL"
      arguments = [
        {
          name      = "league"
          data_type = jsonencode({ "typeKind" : "STRING" })
        }
      ]
    }
  }
  views = {
    leagues_latest = file("../../src/bigquery/sql/simulation/leagues_latest.sql")
  }
  depends_on = [module.bigquery-master.tables]
}

/*****************************************
  functions
 *****************************************/
module "bigquery-functions" {
  source = "../modules/bigquery"

  dataset_id = "functions"
  location   = var.region
  project_id = module.project.project_id
  routines = {
    accent_to_latin = {
      definition_body = file("../../src/bigquery/sql/functions/accent_to_latin.sql")
      routine_type    = "SCALAR_FUNCTION"
      language        = "SQL"
      arguments = [
        {
          name      = "word"
          data_type = jsonencode({ "typeKind" : "STRING" })
        }
      ]
    }
    matchProbs = {
      definition_body = file("../../src/bigquery/sql/functions/matchProbs.js")
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
          name      = "handicap"
          data_type = jsonencode({ "typeKind" : "STRING" })
        }
      ]
    }
  }
}

/*****************************************
  operations
 *****************************************/

module "bigquery-operations" {
  source = "../modules/bigquery"

  dataset_id = "operations"
  location   = var.region
  project_id = module.project.project_id
  views = {
    get_daily_suggestions = file("../../src/bigquery/sql/operations/get_daily_suggestions.sql")
    get_kelly_ratio       = file("../../src/bigquery/sql/operations/get_kelly_ratio.sql")
    map_hkjc_team_list    = file("../../src/bigquery/sql/operations/map_hkjc_team_list.sql")
    map_hkjc_teams        = file("../../src/bigquery/sql/operations/map_hkjc_teams.sql")
    map_hkjc_tournaments  = file("../../src/bigquery/sql/operations/map_hkjc_tournaments.sql")
  }
  depends_on = [
    module.bigquery-hkjc.views,
    module.bigquery-solver.external_tables,
    module.bigquery-functions.routines,
  ]
}

/*****************************************
  outputs
 *****************************************/
module "bigquery-outputs" {
  source = "../modules/bigquery"

  dataset_id = "outputs"
  location   = var.region
  project_id = module.project.project_id
  views = {
    results                    = file("../../src/bigquery/sql/outputs/results.sql")
    schedule                   = file("../../src/bigquery/sql/outputs/schedule.sql")
    simulation_acl2_gs         = file("../../src/bigquery/sql/outputs/simulation_acl2_gs.sql")
    simulation_acle_gs         = file("../../src/bigquery/sql/outputs/simulation_acle_gs.sql")
    simulation_acq             = file("../../src/bigquery/sql/outputs/simulation_acq.sql")
    simulation_bun             = file("../../src/bigquery/sql/outputs/simulation_bun.sql")
    simulation_cl1             = file("../../src/bigquery/sql/outputs/simulation_cl1.sql")
    simulation_csl             = file("../../src/bigquery/sql/outputs/simulation_csl.sql")
    simulation_cwc_gs          = file("../../src/bigquery/sql/outputs/simulation_cwc_gs.sql")
    simulation_epl             = file("../../src/bigquery/sql/outputs/simulation_epl.sql")
    simulation_hkpl            = file("../../src/bigquery/sql/outputs/simulation_hkpl.sql")
    simulation_j1              = file("../../src/bigquery/sql/outputs/simulation_j1.sql")
    simulation_li1             = file("../../src/bigquery/sql/outputs/simulation_li1.sql")
    simulation_ll              = file("../../src/bigquery/sql/outputs/simulation_ll.sql")
    simulation_sea             = file("../../src/bigquery/sql/outputs/simulation_sea.sql")
    simulation_ucl_gs          = file("../../src/bigquery/sql/outputs/simulation_ucl_gs.sql")
    simulation_ucl_ko          = file("../../src/bigquery/sql/outputs/simulation_ucl_ko.sql")
    simulation_wcq_r3          = file("../../src/bigquery/sql/outputs/simulation_wcq_r3.sql")
    team_ratings_club          = file("../../src/bigquery/sql/outputs/team_ratings_club.sql")
    team_ratings_international = file("../../src/bigquery/sql/outputs/team_ratings_international.sql")
  }

  depends_on = [
    module.bigquery-hkjc.views,
    module.bigquery-solver.external_tables,
    module.bigquery-functions.routines,
    module.bigquery-simulation.external_tables
  ]
}
