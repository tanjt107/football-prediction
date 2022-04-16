import footballprediction.etl.jobs.season as season
import footballprediction.etl.jobs.teams as teams
import footballprediction.etl.jobs.matches as matches


def main():
    season.main(0)
    teams.main(0)
    matches.main(0)


if __name__ == "__main__":
    main()
