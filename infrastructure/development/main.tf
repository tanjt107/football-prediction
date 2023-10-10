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

  suffix        = "${module.project.project_number}-${var.region}"
  location      = var.region
  project_id    = module.project.project_id
  force_destroy = true
  names = [
    "footystats-league-list",
    "footystats-matches",
    "footystats-matches-transformed",
    "footystats-seasons",
    "footystats-teams",
    "hkjc",
    "manual",
    "solver",
    "simulation",
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
    simulation = ["../../manual_files/simulation_params.csv"]
  }
}

module "api-key" {
  source = "../modules/secret"

  secrets    = { "FOOTYSTATS_API_KEY" = file("../../credentials/footystats.txt") }
  project_id = module.project.project_id
}

module "footystats-league-list-topic" {
  source = "../modules/pubsub"

  topic      = "footystats-league-list"
  project_id = module.project.project_id
}

module "footystats-delta-load" {
  source = "../modules/scheduled-function"

  function_name                         = "footystats_publish_season_ids_delta"
  bucket_name                           = module.buckets.names["gcf"]
  job_name                              = "footystats-delta-load"
  job_schedule                          = "35 4-20/8 * * *"
  job_paused                            = true
  topic_name                            = "footystats-delta-load"
  function_source_directory             = "../../function_source"
  function_secret_environment_variables = [module.api-key.secret_ids["FOOTYSTATS_API_KEY"]]
  function_environment_variables        = { "TOPIC_NAME" = module.footystats-league-list-topic.id }
  region                                = var.region
  project_id                            = module.project.project_id
}

module "footystats-get-league-list" {
  source = "../modules/scheduled-function"

  function_name                         = "footystats_get_league_list"
  bucket_name                           = module.buckets.names["gcf"]
  job_name                              = "footystats-initial-load"
  job_schedule                          = "15 23 1,15 * *"
  job_paused                            = true
  topic_name                            = "footystats-initial-load"
  function_source_directory             = "../../function_source"
  function_secret_environment_variables = [module.api-key.secret_ids["FOOTYSTATS_API_KEY"]]
  function_environment_variables        = { BUCKET_NAME = module.buckets.names["footystats-league-list"] }
  region                                = var.region
  project_id                            = module.project.project_id
}

module "footystats-initial-load" {
  source = "../modules/event-function"

  name                         = "footystats_publish_season_ids_initial"
  bucket_name                  = module.buckets.names["gcf"]
  secret_environment_variables = [module.api-key.secret_ids["FOOTYSTATS_API_KEY"]]
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

module "footystats-get-footystats" {
  source = "../modules/event-function"

  name                             = "footystats_get_data"
  bucket_name                      = module.buckets.names["gcf"]
  available_cpu                    = 1
  available_memory                 = "512Mi"
  max_instance_request_concurrency = 80
  secret_environment_variables     = [module.api-key.secret_ids["FOOTYSTATS_API_KEY"]]
  event_type                       = "google.cloud.pubsub.topic.v1.messagePublished"
  topic_name                       = module.footystats-league-list-topic.id
  source_directory                 = "../../function_source"
  event_trigger_failure_policy     = "RETRY_POLICY_RETRY"
  region                           = var.region
  project_id                       = module.project.project_id
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

module "bigquery-footystats" {
  source = "../modules/bigquery"

  dataset_id          = "footystats"
  location            = var.region
  project_id          = module.project.project_id
  deletion_protection = false
  external_tables = {
    league_list = {
      schema        = file("../../bigquery/schema/footystats/league_list.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["footystats-league-list"]}/league_list.json"]
    }
    matches = {
      schema                    = file("../../bigquery/schema/footystats/matches.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["footystats-matches"]}/*/matches.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["footystats-matches"]}/{_COUNTRY:STRING}/{_NAME:STRING}/{_YEAR:STRING}/{_SEASON_ID:INTEGER}" }
    }
    matches_transformed = {
      schema                    = file("../../bigquery/schema/footystats/matches_transformed.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["footystats-matches-transformed"]}/*/matches.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["footystats-matches-transformed"]}/{_COUNTRY:STRING}/{_NAME:STRING}/{_YEAR:STRING}/{_SEASON_ID:INTEGER}" }
    }
    seasons = {
      schema                    = file("../../bigquery/schema/footystats/seasons.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["footystats-seasons"]}/*/season.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["footystats-seasons"]}/{_COUNTRY:STRING}/{_NAME:STRING}/{_YEAR:STRING}/{_SEASON_ID:INTEGER}" }
    }
    teams = {
      schema                    = file("../../bigquery/schema/footystats/teams.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["footystats-teams"]}/*/teams.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["footystats-teams"]}/{_COUNTRY:STRING}/{_NAME:STRING}/{_YEAR:STRING}/{_SEASON_ID:INTEGER}" }
    }
  }
  routines = {
    get_season_id_delta = {
      definition_body = templatefile("../../bigquery/routine/functions/footystats/get_season_id_delta.sql", { project_id = module.project.project_id })
      routine_type    = "TABLE_VALUED_FUNCTION"
      language        = "SQL"
    }
    get_season_id_initial = {
      definition_body = templatefile("../../bigquery/routine/functions/footystats/get_season_id_initial.sql", { project_id = module.project.project_id })
      routine_type    = "TABLE_VALUED_FUNCTION"
      language        = "SQL"
    }
  }
}

module "solver" {
  source = "../modules/scheduled-function"

  function_name                  = "solver"
  bucket_name                    = module.buckets.names["gcf"]
  function_timeout_s             = 540
  function_available_memory      = "1Gi"
  function_available_cpu         = 2
  job_name                       = "solver"
  job_schedule                   = "45 4-20/8 * * *"
  job_paused                     = true
  message_data                   = "Club"
  topic_name                     = "solver"
  function_source_directory      = "../../function_source"
  function_environment_variables = { BUCKET_NAME = module.buckets.names["solver"] }
  region                         = var.region
  project_id                     = module.project.project_id
}

resource "google_cloud_scheduler_job" "solver-international" {
  name     = "solver-international"
  schedule = "45 20 * 1-3,6-7,9-11 *"
  paused   = true
  region   = var.region
  project  = module.project.project_id

  pubsub_target {
    topic_name = "projects/${module.project.project_id}/topics/${module.solver.pubsub_topic_name}"
    data       = base64encode("International")
  }
}

module "bigquery-solver" {
  source = "../modules/bigquery"

  dataset_id          = "solver"
  location            = var.region
  project_id          = module.project.project_id
  deletion_protection = false
  tables = {
    run_log = file("../../bigquery/schema/solver/run_log.json")
  }
  external_tables = {
    leagues = {
      schema                    = file("../../bigquery/schema/solver/leagues.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["solver"]}/*/leagues.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["solver"]}/{type:STRING}" }
    }
    teams = {
      schema                    = file("../../bigquery/schema/solver/teams.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["solver"]}/*/teams.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["solver"]}/{type:STRING}" }
    }
  }
  routines = {
    get_matches = {
      definition_body = templatefile("../../bigquery/routine/functions/solver/get_matches.sql", { project_id = module.project.project_id })
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
  }
}

module "hkjc-get-odds" {
  source = "../modules/scheduled-function"

  function_name                         = "hkjc_get_odds"
  bucket_name                           = module.buckets.names["gcf"]
  job_name                              = "hkjc-odds"
  job_schedule                          = "55 4,12,20 * * *"
  job_paused                            = true
  topic_name                            = "hkjc-odds"
  function_source_directory             = "../../function_source"
  function_event_trigger_failure_policy = "RETRY_POLICY_RETRY"
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
  job_schedule                   = "30 23 * * *"
  job_paused                     = true
  topic_name                     = "hkjc-content"
  function_source_directory      = "../../function_source"
  function_environment_variables = { BUCKET_NAME = module.buckets.names["hkjc"] }
  region                         = var.region
  project_id                     = module.project.project_id
}

module "bigquery-hkjc" {
  source = "../modules/bigquery"

  dataset_id          = "hkjc"
  location            = var.region
  project_id          = module.project.project_id
  deletion_protection = false
  external_tables = {
    leagues = {
      schema        = file("../../bigquery/schema/hkjc/content.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["hkjc"]}/leaguelist.json"]
    },
    odds_had = {
      schema                    = file("../../bigquery/schema/hkjc/odds_had.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["hkjc"]}/*/odds_had.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["hkjc"]}/{_TIMESTAMP:TIMESTAMP}" }
    },
    odds_hdc = {
      schema                    = file("../../bigquery/schema/hkjc/odds_hdc.json")
      source_format             = "NEWLINE_DELIMITED_JSON"
      source_uris               = ["${module.buckets.urls["hkjc"]}/*/odds_hdc.json"]
      hive_partitioning_options = { source_uri_prefix = "${module.buckets.urls["hkjc"]}/{_TIMESTAMP:TIMESTAMP}" }
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

  dataset_id          = "manual"
  location            = var.region
  project_id          = module.project.project_id
  deletion_protection = false
  external_tables = {
    hkjc_leagues = {
      schema        = file("../../bigquery/schema/manual/hkjc.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/hkjc_leagues.csv"]
    }
    hkjc_teams = {
      schema        = file("../../bigquery/schema/manual/hkjc.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/hkjc_teams.csv"]
    }
    intl_club_competitions = {
      schema        = file("../../bigquery/schema/manual/intl_club_competitions.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/intl_club_competitions.csv"]
    }
    non_hkjc_leagues = {
      schema        = file("../../bigquery/schema/manual/non_hkjc.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/non_hkjc_leagues.csv"]
    }
    non_hkjc_teams = {
      schema        = file("../../bigquery/schema/manual/non_hkjc.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/non_hkjc_teams.csv"]
    }
    transfermarkt_leagues = {
      schema        = file("../../bigquery/schema/manual/transfermarkt.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/transfermarkt_leagues.csv"]
    }
    transfermarkt_teams = {
      schema        = file("../../bigquery/schema/manual/transfermarkt.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["manual"]}/transfermarkt_teams.csv"]
    }
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

module "bigquery-master" {
  source = "../modules/bigquery"

  dataset_id           = "master"
  service_account_name = module.service-accounts.emails["bigquery-scheduled-queries"]
  location             = var.region
  project_id           = module.project.project_id
  deletion_protection  = false
  tables = {
    leagues      = file("../../bigquery/schema/master/leagues.json")
    team_ratings = file("../../bigquery/schema/master/team_ratings.json")
    teams        = file("../../bigquery/schema/master/teams.json")
  }
  scheduled_queries = {
    leagues = {
      schedule = "every day 23:40"
      query    = file("../../bigquery/routine/master/leagues.sql")
    }
    team_ratings = {
      schedule = "every 8 hours from 04:55 to 20:55"
      query    = file("../../bigquery/routine/master/team_ratings.sql")
    }
    teams = {
      schedule = "every day 23:40"
      query    = file("../../bigquery/routine/master/teams.sql")
    }
  }

  depends_on = [
    module.bigquery-footystats.external_tables,
    module.bigquery-hkjc.external_tables,
    module.bigquery-manual.external_tables
  ]
}

module "bigquery-functions" {
  source = "../modules/bigquery"

  dataset_id          = "functions"
  location            = var.region
  project_id          = module.project.project_id
  deletion_protection = false
  routines = {
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
          name      = "handicap"
          data_type = jsonencode({ "typeKind" : "STRING" })
        }
      ]
    }
  }

  depends_on = [module.bigquery-master.native_tables]
}

module "simulation-publish-competitions" {
  source = "../modules/event-function"

  name                  = "simulation_publish_competitions"
  bucket_name           = module.buckets.names["gcf"]
  environment_variables = { GCP_PROJECT = module.project.project_id }
  event_type            = "google.cloud.storage.object.v1.finalized"
  source_directory      = "../../function_source"
  region                = var.region
  project_id            = module.project.project_id
  event_filters = {
    attribute = "bucket"
    value     = module.buckets.names["solver"]
  }
}

module "bigquery-simulation" {
  source = "../modules/bigquery"

  dataset_id          = "simulation"
  location            = var.region
  project_id          = module.project.project_id
  deletion_protection = false
  tables = {
    run_log = file("../../bigquery/schema/simulation/run_log.json")
  }
  external_tables = {
    params = {
      schema        = file("../../bigquery/schema/simulation/params.json")
      source_format = "CSV"
      source_uris   = ["${module.buckets.urls["simulation"]}/simulation_params.csv"]
    }
    ac = {
      schema        = file("../../bigquery/schema/simulation/leagues.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["simulation"]}/AFC Asian Cup.json"]
    }
    acl = {
      schema        = file("../../bigquery/schema/simulation/leagues.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["simulation"]}/AFC Champions League.json"]
    }
    bun = {
      schema        = file("../../bigquery/schema/simulation/leagues.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["simulation"]}/Bundesliga.json"]
    }
    cl1 = {
      schema        = file("../../bigquery/schema/simulation/leagues.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["simulation"]}/China League One.json"]
    }
    csl = {
      schema        = file("../../bigquery/schema/simulation/leagues.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["simulation"]}/Chinese Super League.json"]
    }
    hkpl = {
      schema        = file("../../bigquery/schema/simulation/leagues.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["simulation"]}/Hong Kong Premier League.json"]
    }
    j1 = {
      schema        = file("../../bigquery/schema/simulation/leagues.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["simulation"]}/J1 League.json"]
    }
    ll = {
      schema        = file("../../bigquery/schema/simulation/leagues.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["simulation"]}/La Liga.json"]
    }
    li1 = {
      schema        = file("../../bigquery/schema/simulation/leagues.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["simulation"]}/Ligue 1.json"]
    }
    epl = {
      schema        = file("../../bigquery/schema/simulation/leagues.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["simulation"]}/Premier League.json"]
    }
    sea = {
      schema        = file("../../bigquery/schema/simulation/leagues.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["simulation"]}/Serie A.json"]
    }
    ucl = {
      schema        = file("../../bigquery/schema/simulation/leagues.json")
      source_format = "NEWLINE_DELIMITED_JSON"
      source_uris   = ["${module.buckets.urls["simulation"]}/UEFA Champions League.json"]
    }
  }
}

module "pubsub-simulation-league" {
  source = "../modules/pubsub"

  topic      = "simulation-league"
  project_id = module.project.project_id
}

module "simulation-league" {
  source = "../modules/event-function"

  name                  = "simulation_league"
  bucket_name           = module.buckets.names["gcf"]
  timeout_s             = 300
  environment_variables = { BUCKET_NAME = module.buckets.names["simulation"] }
  event_type            = "google.cloud.pubsub.topic.v1.messagePublished"
  topic_name            = module.pubsub-simulation-league.id
  source_directory      = "../../function_source"
  region                = var.region
  project_id            = module.project.project_id
}

module "pubsub-simulation-cup" {
  source = "../modules/pubsub"

  topic      = "simulation-cup"
  project_id = module.project.project_id
}

module "simulation-cup" {
  source = "../modules/event-function"

  name                  = "simulation_cup"
  bucket_name           = module.buckets.names["gcf"]
  timeout_s             = 300
  environment_variables = { BUCKET_NAME = module.buckets.names["simulation"] }
  event_type            = "google.cloud.pubsub.topic.v1.messagePublished"
  topic_name            = module.pubsub-simulation-cup.id
  source_directory      = "../../function_source"
  region                = var.region
  project_id            = module.project.project_id
}

module "bigquery-outputs" {
  source = "../modules/bigquery"

  dataset_id          = "outputs"
  location            = var.region
  project_id          = module.project.project_id
  deletion_protection = false
  views = {
    results                    = file("../../bigquery/routine/outputs/results.sql")
    schedule                   = file("../../bigquery/routine/outputs/schedule.sql")
    simulation_ac              = file("../../bigquery/routine/outputs/simulation_ac.sql")
    simulation_acl             = file("../../bigquery/routine/outputs/simulation_acl.sql")
    simulation_bun             = file("../../bigquery/routine/outputs/simulation_bun.sql")
    simulation_cl1             = file("../../bigquery/routine/outputs/simulation_cl1.sql")
    simulation_csl             = file("../../bigquery/routine/outputs/simulation_csl.sql")
    simulation_epl             = file("../../bigquery/routine/outputs/simulation_epl.sql")
    simulation_hkpl            = file("../../bigquery/routine/outputs/simulation_hkpl.sql")
    simulation_j1              = file("../../bigquery/routine/outputs/simulation_j1.sql")
    simulation_li1             = file("../../bigquery/routine/outputs/simulation_li1.sql")
    simulation_ll              = file("../../bigquery/routine/outputs/simulation_ll.sql")
    simulation_sea             = file("../../bigquery/routine/outputs/simulation_sea.sql")
    simulation_ucl             = file("../../bigquery/routine/outputs/simulation_ucl.sql")
    team_ratings               = file("../../bigquery/routine/outputs/team_ratings.sql")
    team_ratings_international = file("../../bigquery/routine/outputs/team_ratings_international.sql")
  }

  depends_on = [
    module.bigquery-solver.external_tables,
    module.bigquery-functions.routines,
    module.bigquery-simulation.external_tables
  ]
}
