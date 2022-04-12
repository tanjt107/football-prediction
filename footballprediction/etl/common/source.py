import json
import requests
from datetime import datetime
from retry import retry


class FootyStats:
    def __init__(self, filename: str = "credentials/footystats.json"):
        """
        Parameters:
        filename: #TODO API key.
        """
        with open(filename) as f:
            self.key = json.load(f)["key"]

    @retry(json.decoder.JSONDecodeError, tries=1, delay=1)
    def league_list(self, chosen_leagues_only: bool) -> dict:
        """
        Parameters:
        chosen_leagues_only: If set to "true", the list will only return leagues that have been chosen by the user.

        Returns:
        A JSON array of all leagues available in the API Database. Each season of a competition gives a unique ID.
        """
        params = {"key": self.key}
        if chosen_leagues_only:
            params["chosen_leagues_only"] = "true"
        response = requests.get(
            "https://api.football-data-api.com/league-list", params=params
        )
        return response.json()["data"]

    def league_id_list_filtered(self, years: int = 0) -> list:
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
        season_id: ID of the league season that you would like to retrieve

        Returns:
        The League season's stats, and an array of Teams that have participated in the season. The teams contain all stats relevant to them.
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
        season_id: Season ID.

        Returns:
        A JSON Array containing each match details.
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
        season_id: Season ID.

        Returns:
        The data of each team as a JSON array.
        """
        params = {"key": self.key, "season_id": season_id}
        response = requests.get(
            "https://api.football-data-api.com/league-teams", params=params
        )
        return response.json()["data"]
