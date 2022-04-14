import json
import requests
from datetime import datetime
from retry import retry
from typing import List


class FootyStats:
    """
    Parameters:
    ------------
    key: str
        API key.
    """

    def __init__(self, key: str = "example"):
        self.key = key

    @retry(json.decoder.JSONDecodeError, tries=1, delay=1)
    def league_list(self, chosen_leagues_only: bool = False) -> dict:
        """
        Parameters:
        ------------
        chosen_leagues_only: bool
            If True, only return leagues that have been chosen by the user.

        Returns:
        ------------
        league_list: dict
            List of leagues. Each season of a competition gives a unique ID.
        """
        params = {"key": self.key}
        if chosen_leagues_only:
            params["chosen_leagues_only"] = "true"
        response = requests.get(
            "https://api.football-data-api.com/league-list", params=params
        )
        return response.json()["data"]

    def chosen_season_id(self, years: int = 0) -> List[int]:
        """
        Filter recent seasons based on a year offset.

        Parameters:
        ------------
        years: int
            The offset number of years that will be selected. For instance, years=1 will
            return the most recent season and last season.

        Returns:
        ------------
        chosen_season_id: List[int]
            List of chosen season IDs.
        """
        year_today = datetime.now().year
        season_spring_to_fall = year_today - years
        season_fall_to_spring = (year_today - years - 1) * 10000 + year_today - years

        league_ids = []

        for league in self.league_list(chosen_leagues_only=True):
            league_ids.extend(
                season["id"]
                for season in league["season"]
                if (
                    season_spring_to_fall <= season["year"] < 10000
                    or season_fall_to_spring <= season["year"]
                )
            )
        return league_ids

    @retry(json.decoder.JSONDecodeError, tries=1, delay=1)
    def season(self, season_id: int) -> dict:
        """
        Parameters:
        ------------
        season_id: int
            ID of the league season.

        Returns:
        ------------
        season: dict
            League season's stats, and list of teams that have participated in the season.
        """
        params = {"key": self.key, "season_id": season_id}
        response = requests.get(
            "https://api.football-data-api.com/league-season", params=params
        )
        return response.json()["data"]

    @retry(json.decoder.JSONDecodeError, tries=1, delay=1)
    def matches(self, season_id: int) -> dict:
        """
        Returns the full match schedule of the selected league id.

        Parameters:
        ------------
        season_id: int
            ID of the league season.

        Returns:
        ------------
        matches: dict
            Match details.
        """
        params = {"key": self.key, "season_id": season_id}
        response = requests.get(
            "https://api.football-data-api.com/league-matches", params=params
        )
        return response.json()["data"]

    @retry(json.decoder.JSONDecodeError, tries=1, delay=1)
    def teams(self, season_id: int) -> dict:
        """
        Stats for all teams that participated in a season of a league.

        Parameters:
        ------------
        season_id: int
            ID of the league season.

        Returns:
        ------------
        teams: dict
            The data of each team
        """
        params = {"key": self.key, "season_id": season_id}
        response = requests.get(
            "https://api.football-data-api.com/league-teams", params=params
        )
        return response.json()["data"]
