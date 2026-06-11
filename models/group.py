from __future__ import annotations

from dataclasses import dataclass, field

from models.team import Team


@dataclass
class Group:
    letter: str
    teams: list[Team] = field(default_factory=list)

    @property
    def sorted_teams(self) -> list[Team]:
        return sorted(self.teams, key=lambda t: t.sort_key(), reverse=True)

    def get_team(self, code: str) -> Team | None:
        for team in self.teams:
            if team.code == code:
                return team
        return None
