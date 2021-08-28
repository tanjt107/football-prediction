import json
import os
import pandas as pd
import requests
from datetime import datetime
from common import Season, Team, API_KEY, DATA_FOLDER_PATH
from solver import solver

def get_all_leagues(chosen_leagues_only: bool) -> pd.DataFrame:
    response = requests.get(f'https://api.football-data-api.com/league-list?key={API_KEY}&chosen_leagues_only={str(chosen_leagues_only).lower()}').json()
    return pd.DataFrame(response['data'])

def get_inter_league_season_ids(season_ids: list, number_of_years: int) -> list:
    seasons = []
    df = get_all_leagues(True)
    leagues = df.loc[df['name'].isin(season_ids)]['season'].values
    for league in leagues:
        for season in league:
            if season['year'] >= int(CURRENT_YEAR) - number_of_years:
                seasons.append(season['id'])
    return(seasons)


def append_two_seasons_df(current_season: Season, previous_season: Season) -> pd.DataFrame:
    current_season_team_ids = current_season.team_ids()
    previous_season_df = previous_season.matches.df('complete')
    previous_season_df = previous_season_df[
        previous_season_df.homeID.isin(current_season_team_ids)
        & previous_season_df.awayID.isin(current_season_team_ids)
        ]
    return previous_season_df.append(current_season.matches.df('complete'))

def main(inter_league_id: int):
    inter_league = Season(inter_league_id)
    print(inter_league)
    team_ids = inter_league.team_ids('not canceled')
    # updated_season = set()
    for team_id in team_ids:
        team = Team(team_id)
        print(team)
        for current_season_id, previous_season_id in zip(
            team.domestic_league_ids, team.domestic_league_ids[1:]
            ):
            if current_season_id not in updated_season:
                current_season = Season(current_season_id)
                updated_season.add(current_season.id)
                if (current_season.success == True
                    and inter_league.season in current_season.season):
                    if current_season.need_update or CURRENT_YEAR in current_season.season:
                        if (current_season.matchesCompleted) > 0:
                            if (recent:= current_season.status != 'Completed'):
                                previous_season = Season(previous_season_id)
                                assert current_season.name == previous_season.name
                                df = append_two_seasons_df(current_season, previous_season)
                                pass
                            else:
                                df = current_season.matches.df('complete')
                            print(current_season)
                            result = {
                                'id': current_season.id,
                                'name': current_season.name,
                                'country' : current_season.country,
                                'season': current_season.season,
                                'status': current_season.status,
                                **solver(
                                    df,
                                    recent=recent
                                    )}
                            with open(os.path.join(
                                DATA_FOLDER_PATH, current_season.json_name
                                ), 'w') as f:
                                json.dump(result, f, indent=4)

if __name__ == '__main__':
    INTER_LEAGUE_LIST = ['Asia AFC Champions League', 'Asia AFC Cup', 'China Chinese FA Cup', 'India Super Cup']
    CURRENT_YEAR = datetime.today().strftime('%Y')
    updated_season = set()
    inter_league_season_ids = get_inter_league_season_ids(INTER_LEAGUE_LIST, 0)
    for season_id in inter_league_season_ids:
        print('---------------------------------------------------------------')
        main(season_id)