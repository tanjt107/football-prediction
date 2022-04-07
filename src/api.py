import json
from json.decoder import JSONDecoder, JSONDecodeError
import requests
from retry import retry


class FootyStats:
    def __init__(self, key: str):
        """
        Parameters:
        key: API key.
        """
        self.key = key

    @retry(json.decoder.JSONDecodeError, tries=1, delay=1)
    def leagues(self, chosen_leagues_only: bool = False) -> json.JSONDecoder:
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
        return response.json()

    @retry(json.decoder.JSONDecodeError, tries=1, delay=1)
    def league_stats(self, season_id: int) -> json.JSONDecoder:
        """
        Parameters:
        season_id = ID of the league season that you would like to retrieve

        Returns:
        The League season's stats, and an array of Teams that have participated in the season. The teams contain all stats relevant to them.
        """
        params = {"key": self.key, "season_id": season_id}
        response = requests.get(
            "https://api.football-data-api.com/league-season", params=params
        )
        return response.json()

    @retry(json.decoder.JSONDecodeError, tries=1, delay=1)
    def matches(self, season_id: int) -> json.JSONDecoder:
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
        return response.json()

    @retry(json.decoder.JSONDecodeError, tries=1, delay=1)
    def league_teams(self, season_id: int) -> json.JSONDecoder:
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
        return response.json()

    @retry(json.decoder.JSONDecodeError, tries=1, delay=1)
    def team(self, team_id: int) -> json.JSONDecoder:
        """
        Individual Team Stats

        Parameters:
        team_id: ID of the team you want

        Returns:
        Basic data of the individual team, as well as stats for each recent competition the team participated in.
        """
        params = {"key": self.key, "team_id": team_id}
        response = requests.get("https://api.football-data-api.com/team", params=params)
        return response.json()


# class HKJC:
#     def schedule() -> json.JSONDecoder:
#         params = {"jsontype": "schedule.aspx"}
#         response = requests.get(
#             "https://bet.hkjc.com/football/getJSON.aspx", params=params
#         )
#         return response.json()

#     def allodds(matchID: str) -> json.JSONDecoder:
#         params = {"jsontype": "odds_allodds.aspx", "matchid": matchID}
#         # params = {'jsontype': 'last_odds.aspx', 'matchid': matchID}
#         response = requests.get(
#             "https://bet.hkjc.com/football/getJSON.aspx", params=params
#         )
#         return response.json()

#     def odds_hdc(**kwargs) -> JSONDecoder:
#         """
#         Game Format: Predict the full time result of a match after being adjusted by the applicable handicap goal(s) - Home Win or Away Win.
#         """
#         params = {"jsontype": "odds_hdc.aspx"}
#         response = requests.get(
#             "https://bet.hkjc.com/football/getJSON.aspx", params=params
#         )
#         return response.json()
