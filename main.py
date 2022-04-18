import footballprediction.etl.jobs.season as season
import footballprediction.etl.jobs.teams as teams
import footballprediction.etl.jobs.matches as matches
import footballprediction.solver.solvers.domestic as domestic
import footballprediction.solver.solvers.inter_league as inter_league


def main():
    season.main()
    teams.main()
    matches.main()
    domestic.main()
    inter_league.main()


if __name__ == "__main__":
    main()
