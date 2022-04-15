import footballprediction.etl.jobs.season as season
import footballprediction.etl.jobs.teams as teams
import footballprediction.etl.jobs.matches as matches


def main():
    season.main()
    teams.main()
    matches.main()


if __name__ == "__main__":
    main()
