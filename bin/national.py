import json
import os
import pandas as pd
from common import Season, get_season_ids, get_all_team_ratings, update_worksheet
from param import CURRENT_YEAR, INTERNATIONAL_FOLDER_PATH, NATIONAL_COMP_LIST
from solver import solver

def get_latest_season_id(name: str) -> Season:
    return get_season_ids([name], 1)[0]

def append_multiple_season_matches_df(main_season: Season, other_seasons: list, market_value: bool) -> pd.DataFrame:
    team_ids = main_season.team_ids()
    df = main_season.matches.df('complete')
    df['previous_season'] = 0
    for season in other_seasons:
        df_season = season.matches.df('complete')
        df_season['previous_season'] = int(market_value)
        df = df.append(df_season)
    df = df[
        df.homeID.isin(team_ids)
        & df.awayID.isin(team_ids)
        ]
    return df

if __name__ == '__main__':
    for main_competition, other_competitions, cut_off_number_of_year in NATIONAL_COMP_LIST:
        latest_main_season_id = get_latest_season_id(main_competition)
        latest_main_season = Season(latest_main_season_id)
        competitions = [main_competition] + other_competitions
        season_ids = get_season_ids(competitions, cut_off_number_of_year)
        season_ids.remove(latest_main_season_id)
        seasons = [Season(season_id) for season_id in season_ids]
        df_matches = append_multiple_season_matches_df(latest_main_season, seasons, False)

        print(latest_main_season)
        result = solver(df_matches, cut_off_number_of_year=cut_off_number_of_year, max_boundary=5)

        with open(os.path.join(
            INTERNATIONAL_FOLDER_PATH,
            latest_main_season.json_name
            ), 'w') as f:
            json.dump(result, f, indent=4)

        df_teams = get_all_team_ratings(result)

        update_worksheet(f'{main_competition} Ratings', df_teams)