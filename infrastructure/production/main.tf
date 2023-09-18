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
    "footystats-teams",
    "hkjc",
    "manual",
    "solver",
    "gcf"
  ]
  files = {
    manual = [
      "../../manual_files/hkjc_leagues.csv",
      "../../manual_files/hkjc_teams.csv",
      "../../manual_files/intl_club_competitions.csv",
      "../../manual_files/non_hkjc_leagues.csv",
      "../../manual_files/non_hkjc_teams.csv",
      "../../manual_files/transfermarkt_leagues.csv",
      "../../manual_files/transfermarkt_teams.csv",
    ]
  }
}

module "bigquery-footystats" {
  source = "../modules/bigquery"

  dataset_id = "footystats"
  location   = var.region
  project_id = module.project.project_id
  external_tables = {
    league_list = {
      schema        = file("../../bigquery/schema/footystats/league_list.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["footystats-league-list"]}/league_list.json"]
    }
    matches = {
      schema        = file("../../bigquery/schema/footystats/matches.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["footystats-matches"]}/*.json"]
    }
    matches_transformed = {
      schema        = file("../../bigquery/schema/footystats/matches_transformed.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["footystats-matches-transformed"]}/*.json"]
    }
    seasons = {
      schema        = file("../../bigquery/schema/footystats/seasons.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["footystats-seasons"]}/*.json"]
    }
    teams = {
      schema        = file("../../bigquery/schema/footystats/teams.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["footystats-teams"]}/*.json"]
    }
  }
}

module "bigquery-solver" {
  source = "../modules/bigquery"

  dataset_id = "solver"
  location   = var.region
  project_id = module.project.project_id
  tables = {
    run_log = file("../../bigquery/schema/solver/run_log.json")
  }
  external_tables = {
    leagues = {
      schema        = file("../../bigquery/schema/solver/leagues.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["solver"]}/leagues/*.json"]
    }
    teams = {
      schema        = file("../../bigquery/schema/solver/teams.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["solver"]}/teams/*.json"]
    }
  }
}

module "api-key" {
  source = "../modules/secret"

  secrets    = { "FOOTYSTATS_API_KEY" = file("../../credentials/footystats.txt") }
  project_id = module.project.project_id
}

module "footystats-get-league-list" {
  source = "../modules/scheduled-function"

  function_name                         = "footystats_get_league_list"
  bucket_name                           = module.buckets.names["gcf"]
  job_name                              = "footystats"
  job_schedule                          = "0 */3 * * *"
  topic_name                            = "footystats"
  function_source_directory             = "../../function_source"
  function_secret_environment_variables = ["FOOTYSTATS_API_KEY"]
  function_environment_variables        = { BUCKET_NAME = module.buckets.names["footystats-league-list"] }
  region                                = var.region
  project_id                            = module.project.project_id
}

module "footystats-league-list-topic" {
  source = "../modules/pubsub"

  topic      = "footystats-league-list"
  project_id = module.project.project_id
}

module "footystats-publish-season-ids" {
  source = "../modules/event-function"

  name                         = "footystats_publish_season_ids"
  bucket_name                  = module.buckets.names["gcf"]
  secret_environment_variables = ["FOOTYSTATS_API_KEY"]
  environment_variables        = { TOPIC_NAME = module.footystats-league-list-topic.id }
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

  function_name                         = "footystats_publish_season_ids_initial_load"
  bucket_name                           = module.buckets.names["gcf"]
  job_name                              = "footystats-initial-load"
  job_schedule                          = "0 7 1 * *"
  topic_name                            = "footystats-initial-load"
  function_source_directory             = "../../function_source"
  function_secret_environment_variables = ["FOOTYSTATS_API_KEY"]
  function_environment_variables        = { "TOPIC_NAME" = module.footystats-league-list-topic.id }
  function_event_trigger_failure_policy = "RETRY_POLICY_RETRY"
  region                                = var.region
  project_id                            = module.project.project_id
}

module "footystats-get-footystats" {
  source = "../modules/event-function"

  name                         = "footystats_get_data"
  bucket_name                  = module.buckets.names["gcf"]
  max_instances                = 3000
  secret_environment_variables = ["FOOTYSTATS_API_KEY"]
  event_type                   = "google.cloud.pubsub.topic.v1.messagePublished"
  topic_name                   = module.footystats-league-list-topic.id
  source_directory             = "../../function_source"
  region                       = var.region
  project_id                   = module.project.project_id
  environment_variables = {
    MATCHES_BUCKET_NAME = module.buckets.names["footystats-matches"]
    SEASONS_BUCKET_NAME = module.buckets.names["footystats-seasons"]
    TEAMS_BUCKET_NAME   = module.buckets.names["footystats-teams"]
  }
}

module "footystats-transform-matches" {
  source = "../modules/event-function"

  name                  = "footystats_transform_matches"
  bucket_name           = module.buckets.names["gcf"]
  environment_variables = { BUCKET_NAME = module.buckets.names["footystats-matches-transformed"] }
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

  function_name             = "solver"
  bucket_name               = module.buckets.names["gcf"]
  function_timeout_s        = 540
  function_available_memory = "1Gi"
  function_available_cpu    = 2
  job_name                  = "solver"
  job_schedule              = "30 */3 * * *"
  message_data              = "Club"
  topic_name                = "solver"
  function_source_directory = "../../function_source"
  function_environment_variables = {
    BOUND       = 10
    BUCKET_NAME = module.buckets.names["solver"]
  }
  region     = var.region
  project_id = module.project.project_id
}

resource "google_cloud_scheduler_job" "solver-international" {
  name     = "solver-international"
  schedule = "30 */3 * 1-3,6-7,9-11 *"
  region   = var.region
  project  = module.project.project_id

  pubsub_target {
    topic_name = "projects/${module.project.project_id}/topics/${module.solver.pubsub_topic_name}"
    data       = base64encode("International")
  }
}

module "hkjc-get-odds" {
  source = "../modules/scheduled-function"

  function_name             = "hkjc_get_odds"
  bucket_name               = module.buckets.names["gcf"]
  job_name                  = "hkjc-odds"
  job_schedule              = "45 */3 * * *"
  topic_name                = "hkjc-odds"
  function_source_directory = "../../function_source"
  function_environment_variables = {
    BUCKET_NAME = module.buckets.names["hkjc"]
    POOLS       = jsonencode(["HAD", "HDC"])
  }
  region     = var.region
  project_id = module.project.project_id
}

module "hkjc-get-content" {
  source = "../modules/scheduled-function"

  function_name                  = "hkjc_get_content"
  bucket_name                    = module.buckets.names["gcf"]
  job_name                       = "hkjc-get-content"
  job_schedule                   = "45 7 * * *"
  topic_name                     = "hkjc-content"
  function_source_directory      = "../../function_source"
  function_environment_variables = { BUCKET_NAME = module.buckets.names["hkjc"] }
  region                         = var.region
  project_id                     = module.project.project_id
}

module "bigquery-hkjc" {
  source = "../modules/bigquery"

  dataset_id = "hkjc"
  location   = var.region
  project_id = module.project.project_id
  external_tables = {
    leagues = {
      schema        = file("../../bigquery/schema/hkjc/content.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["hkjc"]}/leaguelist.json"]
    },
    odds_had = {
      schema        = file("../../bigquery/schema/hkjc/odds_had.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["hkjc"]}/odds_had.json"]
    },
    odds_hdc = {
      schema        = file("../../bigquery/schema/hkjc/odds_hdc.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["hkjc"]}/odds_hdc.json"]
    },
    teams = {
      schema        = file("../../bigquery/schema/hkjc/content.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["hkjc"]}/teamlist.json"]
    }
  }
}

module "bigquery-manual" {
  source = "../modules/bigquery"

  dataset_id = "manual"
  location   = var.region
  project_id = module.project.project_id
  external_tables = {
    hkjc_leagues = {
      schema        = file("../../bigquery/schema/manual/hkjc_leagues.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/hkjc_leagues.csv"]
    }
    hkjc_teams = {
      schema        = file("../../bigquery/schema/manual/hkjc_teams.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/hkjc_teams.csv"]
    }
    intl_club_competitions = {
      schema        = file("../../bigquery/schema/manual/intl_club_competitions.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/intl_club_competitions.csv"]
    }
    non_hkjc_leagues = {
      schema        = file("../../bigquery/schema/manual/non_hkjc_leagues.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/non_hkjc_leagues.csv"]
    }
    non_hkjc_teams = {
      schema        = file("../../bigquery/schema/manual/non_hkjc_teams.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/non_hkjc_teams.csv"]
    }
    transfermarkt_leagues = {
      schema        = file("../../bigquery/schema/manual/transfermarkt_leagues.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/transfermarkt_leagues.csv"]
    }
    transfermarkt_teams = {
      schema        = file("../../bigquery/schema/manual/transfermarkt_teams.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/transfermarkt_teams.csv"]
    }
  }
}

module "bigquery-functions" {
  source = "../modules/bigquery"

  dataset_id = "functions"
  location   = var.region
  project_id = module.project.project_id
  routines = {
    get_solver_matches = {
      definition_body = templatefile("../../bigquery/routine/functions/get_solver_matches.sql", { project_id = module.project.project_id })
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
        },
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
    matchProbs = {
      definition_body = file("../../bigquery/routine/functions/matchProbs.js")
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

  depends_on = [module.bigquery-footystats.external_tables, module.bigquery-manual.external_tables]
}

module "bigquery-master" {
  source = "../modules/bigquery"

  dataset_id           = "master"
  service_account_name = module.service-accounts.emails["bigquery-scheduled-queries"]
  location             = var.region
  project_id           = module.project.project_id
  scheduled_queries = {
    leagues = {
      schedule = "every 24 hours"
      query    = file("../../bigquery/routine/master/leagues.sql")
    }
    teams = {
      schedule = "every 24 hours"
      query    = file("../../bigquery/routine/master/teams.sql")
    }
  }

  depends_on = [module.bigquery-footystats.external_tables, module.bigquery-hkjc.external_tables, module.bigquery-manual.external_tables]
}

module "bigquery-outputs" {
  source = "../modules/bigquery"

  dataset_id = "outputs"
  location   = var.region
  project_id = module.project.project_id
  views = {
    results                    = file("../../bigquery/routine/outputs/results.sql")
    schedule                   = file("../../bigquery/routine/outputs/schedule.sql")
    team_ratings               = file("../../bigquery/routine/outputs/team_ratings.sql")
    team_ratings_international = file("../../bigquery/routine/outputs/team_ratings_international.sql")
  }

  depends_on = [module.bigquery-master.native_tables]
}
