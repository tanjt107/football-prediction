import json
import numpy as np
import os
import pandas as pd
from common import Season, Team, append_matches_dfs, call_api, get_all_team_ratings, get_current_year, get_season_ids, update_worksheet
from param import PARENT_DIRECTORY, INTER_LEAGUE_LIST, MANUALLY_HANDLED_SEASONS
from scipy import optimize
from solver import solver, clean_data_for_solver
from typing import Dict, List

def update_seasons(season_id: int, years: int=0):
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
                if current_season.success and current_season.ending_year >= CURRENT_YEAR - years:
                    if (current_season.starting_year == inter_league.starting_year 
                        or current_season.ending_year == inter_league.ending_year):
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

def append_all_team_factors() -> List[dict]:
    l = []
    for _, _, files in os.walk(os.path.join(PARENT_DIRECTORY, "data/season")):
        for file in files:
            if file.endswith(".json"):
                with open(os.path.join(PARENT_DIRECTORY, "data/season", file), "r") as f:
                    season = json.load(f)
                    l += [season]
    return l

def get_all_team_factors(seasons: List[Dict]) -> Dict[tuple, dict]:
    d = {}
    for season in seasons:
        for team, factors in season["team"].items():
            d[(team, season["season"])] = {
                "league": f"{season['country']} {season['name']}",
                "offence": factors["offence"],
                "defence": factors["defence"]
            }
    return d

def get_team_countries(season_ids: List[int]) -> Dict[int, str]:
    d = {}
    for season_id in season_ids:
        teams = call_api("league-teams", {"season_id": season_id})["data"]
        for team in teams:
            d[str(team["id"])] = team["country"]
    return d

def get_season2(timestamp: pd.Series) -> pd.Series:
    year = timestamp.year
    return np.where(
        timestamp.month > 7 , f'{year}/{year + 1}',  f'{year - 1}/{year}'
        )

def get_team_factor(date_unix: pd.Series, team: pd.Series) -> pd.DataFrame:
    df = pd.concat([date_unix, team], axis=1)
    team = team.name
    df["date_unix"] = pd.to_datetime(df["date_unix"], unit="s")
    df["season1"] = df["date_unix"].dt.year
    df["season2"] = df["date_unix"].apply(get_season2)
    df[[team, "season1", "season2"]] = df[[team, "season1", "season2"]].astype(str)
    for season in [1, 2]:
        df[f"team_season{season}"] = list(zip(df[team], df[f"season{season}"]))
        df[f"factor_season{season}"] = df[f"team_season{season}"].map(team_factors)
        df[[f"defence{season}", f"league{season}", f"offence{season}"]] = df[f"factor_season{season}"].apply(pd.Series).iloc[:,-3:]
    df["league3"] = df[team].map(team_countries).map(country_leagues)
    for factor in ["offence","defence"]:
        df[factor] = df[f"{factor}1"].fillna(df[f"{factor}2"])
    df["league"] = df["league1"].fillna(df["league2"]).fillna(df["league3"])
    return df[["league", "offence", "defence"]]


def solver_inter_league(df: pd.DataFrame, cut_off_number_of_year: int=4, bounds: float=3):

    def set_calculable_string_in_df(df: pd.DataFrame) -> pd.DataFrame:
        df["average_goal"] = "average_goal"
        df["home_advantage"] = "home_advantage"
        return df

    def get_league_list(df: pd.DataFrame) -> List[int]:
        return np.unique(df[["home_league", "away_league"]].values)

    def get_factors_array(teams: List[str]) -> np.array:
        """second argument is the corresponding strings forarray values."""
        return np.concatenate(
            (["average_goal", "home_advantage"],
            leagues)
            )

    def initialise_factors(factors: np.array) -> np.array:
        """
        first argument required by optimize is a 1d array with some number of values
        and set a reasonable initial value for the solver.
        """
        return np.concatenate(([1.35, 1], np.repeat(0, factors.size - 2)))

    def set_constraints(factors: np.array) -> List[dict]:
        def sum_strength(factors):
            return np.sum(factors[2:])
        def minimum_home_advantage(factors):
            return factors[1] - 1
        con_sum_strength = {"type": "eq", "fun": sum_strength}
        con_home_advantage = {"type": "ineq", "fun": minimum_home_advantage}
        return [con_sum_strength, con_home_advantage]

    def set_boundaries(factors: np.array, max: float) -> List[tuple]:
        return ((-max,max),) * len(factors)

    def objective(values: np.array, factors: np.array, df: pd.DataFrame) -> float:
        """turn df strings into values that can be calculated."""
        assert len(values) == len(factors)
        lookup = {factor: value for factor, value in zip (factors, values)}
        df = df.replace(lookup)
        obj = (
            (
                (
                    df.average_goal * df.home_advantage ** (1 - df.no_home_away)
                    * df.home_offence * df.away_defence
                    + df.home_league - df.away_league
                    - df.home_team_average_goal
                    ) ** 2
                    +
                (
                    df.average_goal / df.home_advantage ** (1 - df.no_home_away)
                    * df.away_offence * df.home_defence
                    + df.away_league - df.home_league
                    - df.away_team_average_goal
                    ) ** 2
            ) * df.recentness
        )
        return np.sum(obj)

    def parse_result_to_dict(solver: str, factors: np.array) -> dict:
        return {factor: value for factor, value in zip(factors, solver.x)}

    df = clean_data_for_solver(df, cut_off_number_of_year=cut_off_number_of_year)
    for team in ["home", "away"]:
        df[[f"{team}_league", f"{team}_offence", f"{team}_defence"]] = get_team_factor(df["date_unix"], df[f"{team}ID"])
    df = df.loc[df.home_league != df.away_league]
    df = df.dropna(subset=["home_league", "away_league"])
    df["date_unix"] = pd.to_datetime(df["date_unix"], unit="s")
    df = df.loc[~((df.competition_id == 5667) & ((df.home_league == "China Chinese Super League") | (df.away_league == "China Chinese Super League")))]
    average_offence = (df.home_offence.mean() + df.away_offence.mean()) / 2
    average_defence = (df.home_defence.mean() + df.away_defence.mean()) / 2
    df = df.fillna({"home_offence": average_offence, "home_defence": average_defence, "away_offence": average_offence, "away_defence": average_defence})
    df = df.apply(set_calculable_string_in_df, axis=1)
    leagues = get_league_list(df)
    factors = get_factors_array(leagues)
    initial = initialise_factors(factors)
    cons = set_constraints(factors)
    bnds = set_boundaries(factors, bounds)
    solver = optimize.minimize(
        objective, args=(factors, df), x0=initial,
        method = "SLSQP", constraints=cons, bounds=bnds, options={"maxiter":10000})
    result = parse_result_to_dict(solver, factors)
    return result

def get_all_team_factors_latest(seasons: List[Dict]) -> dict:
    d = {season["id"]: {
            "name": season["name"],
            "country": season["country"],
            "season": season["season"]
        } for season in seasons}
    df = pd.DataFrame.from_dict(d, orient="index")
    df = df.sort_values(by="season", ascending=False).drop_duplicates(subset="name")
    d = {}
    for season in seasons:
        if season["id"] in df.index.values:
            for team, factors in season["team"].items():
                assert team not in d
                d[team] = {
                "league": f"{season['country']} {season['name']}",
                "offence": factors["offence"],
                "defence": factors["defence"]
            }
    return d

if __name__ == "__main__":
    CURRENT_YEAR = get_current_year()
    updated_seasons = set(MANUALLY_HANDLED_SEASONS)
    inter_league_season_ids_current_season = get_season_ids(INTER_LEAGUE_LIST, 0)
    inter_league_season_ids_4yr = get_season_ids(INTER_LEAGUE_LIST, 4)
    for season_id in inter_league_season_ids_current_season:
        print("---------------------------------------------------------------")
        update_seasons(season_id)
    # ----------------------------------------------------------------------------
    all_factors = append_all_team_factors()
    team_factors = get_all_team_factors(all_factors)
    team_countries = get_team_countries(inter_league_season_ids_4yr)
    df = append_matches_dfs(seasons=[Season(season_id) for season_id in inter_league_season_ids_4yr], main_teams_only=False)
    with open(os.path.join(PARENT_DIRECTORY,"mapping/country-leagues.json"), "r") as f:
        country_leagues = json.load(f)
    league_strength = solver_inter_league(df)
    with open(os.path.join(PARENT_DIRECTORY, "data/clubs", "league-strength.json"), "w") as f:
        json.dump(league_strength, f, indent=4)
    team_factors_latest = get_all_team_factors_latest(all_factors)
    with open(os.path.join(PARENT_DIRECTORY, "data/clubs", "team-factors-latest.json"), "w") as f:
        json.dump(team_factors_latest, f, indent=4)
    team_ratings = get_all_team_ratings(team_factors_latest, True, league_strength)
    update_worksheet("Team Ratings", team_ratings)