import json
import os
from common import Season, Team, append_matches_dfs, get_current_year, get_season_ids
from param import PARENT_DIRECTORY, INTER_LEAGUE_LIST
from solver import solver

def update_seasons(season_id: int):
    inter_league = Season(season_id)
    print(inter_league)
    team_ids = inter_league.team_ids("not canceled")
    for team_id in team_ids:
        team = Team(team_id)
        print(team)
        for current_season_id, previous_season_id in zip(
            team.domestic_league_ids, team.domestic_league_ids[1:]
        ):
            if current_season_id not in updated_seasons:
                current_season = Season(current_season_id)
                if current_season.success and current_season.ending_year >= CURRENT_YEAR - 4:
                    if current_season.starting_year == inter_league.season or current_season.ending_year == inter_league.season:
                        updated_seasons.add(current_season.id)
                        if current_season.matchesCompletedBefore != current_season.matchesCompletedLatest:
                            if (recent:= current_season.status != "Completed"):
                                previous_season = Season(previous_season_id)
                                assert current_season.name == previous_season.name
                                df = append_matches_dfs(current_season, [previous_season], current_season.has_market_value)
                                if current_season.has_market_value:
                                    current_season.update_market_value()
                                    market_value = current_season.market_value_factors()
                                else:
                                    market_value = None
                            else:
                                df = current_season.matches.df("complete")
                                market_value = None
                            print(f"{current_season}, Recent: {recent}, Market Value: {market_value is not None}")
                            result = {
                                "id": current_season.id,
                                "name": current_season.name,
                                "country" : current_season.country,
                                "season": current_season.season,
                                "status": current_season.status,
                                "matchesCompleted": current_season.matchesCompletedLatest,
                                **solver(
                                    df,
                                    recent=recent,
                                    market_values = market_value
                                    )}
                            with open(os.path.join(
                                PARENT_DIRECTORY, "data/season", current_season.json_path
                                ), "w") as f:
                                json.dump(result, f, indent=4)
                else:
                    updated_seasons.add(current_season.id)

if __name__ == "__main__":
    CURRENT_YEAR = get_current_year()
    # updated_seasons = set(MANUALLY_HANDLED_SEASONS)
    updated_seasons = set()
    inter_league_season_ids = get_season_ids(INTER_LEAGUE_LIST, 4)
    for season_id in inter_league_season_ids:
        print("---------------------------------------------------------------")
        update_seasons(season_id)        
    # TODO Calculate league strength