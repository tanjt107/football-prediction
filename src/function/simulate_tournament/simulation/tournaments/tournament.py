from dataclasses import asdict, dataclass

from simulation.models import Match, Team
from .groups import Groups
from .knockout import Knockout
from .rounds import Round
from .season import Season
from .winner import Winner


@dataclass
class Tournament:
    avg_goal: float
    home_adv: float
    teams: dict[str, Team]
    matches: dict[str, list[Match]] | None = None
    groups: dict[str, list[Team]] | None = None

    def __post_init__(self):
        self.rounds: dict[str, Round] = {}

    def create_round(self, name: str, param: dict) -> Round:
        _format = param["format"]

        if _format == "Groups":
            self.groups = self.groups or {
                group: [self.teams[team] for team in _teams]
                for group, _teams in param["groups"].items()
            }
            return Groups(
                self.groups,
                self.avg_goal,
                self.home_adv,
                self.matches[name],
                param["h2h"],
                param["leg"],
                param.get("advance_to"),
            )

        if _format == "Knockout":
            return Knockout(
                name,
                self.avg_goal,
                self.home_adv,
                self.matches[name],
                param["leg"],
                param.get("advance_to"),
                winning_teams={
                    team
                    for match in self.matches.get(param["advance_to"], [])
                    for team in match.teams
                },
            )

        if _format == "Season":
            return Season(
                self.teams.values(),
                self.avg_goal,
                self.home_adv,
                self.matches[name],
                param["h2h"],
                param["leg"],
                param.get("advance_to"),
            )

        if _format == "Winner":
            return Winner()

        raise ValueError(f"Unknown round format: {_format}")

    def set_rounds(self, rounds: dict[str, dict]):
        for name, param in rounds.items():
            self.rounds[name] = self.create_round(name, param)

    def simulate(self, no_of_simulations: int = 1000) -> list[dict]:
        for _ in range(no_of_simulations):
            for name, round_obj in self.rounds.items():
                round_obj.simulate()

                if advance_to := round_obj.advance_to:
                    if isinstance(advance_to, str):
                        self.rounds[advance_to].add_teams(round_obj.get_advanced())
                    else:
                        for name, positions in advance_to.items():
                            self.rounds[name].add_teams(
                                round_obj.get_advanced(**positions)
                            )
                round_obj.reset()

        for team in self.teams.values():
            team.sim_table /= no_of_simulations
            team.sim_rounds /= no_of_simulations
            team.sim_positions /= no_of_simulations

    @property
    def result(self):
        if self.groups:
            return [
                {
                    "team": team.name,
                    "group": group,
                    "positions": dict(team.sim_positions),
                    "rounds": dict(team.sim_rounds),
                    "table": asdict(team.sim_table),
                }
                for group, teams in self.groups.items()
                for team in teams
            ]

        return [
            {
                "team": team.name,
                "positions": dict(team.sim_positions),
                "rounds": dict(team.sim_rounds),
                "table": asdict(team.sim_table),
            }
            for team in self.teams.values()
        ]
