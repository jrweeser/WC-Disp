from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Team:
    code: str
    name: str
    group_letter: str
    wins: int = 0
    losses: int = 0
    draws: int = 0
    goals_for: int = 0
    goals_against: int = 0
    flag_url: str = ""
    flag_iso: str = ""

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    @property
    def points(self) -> int:
        return self.wins * 3 + self.draws

    def record_result(self, goals_for: int, goals_against: int) -> None:
        self.goals_for += goals_for
        self.goals_against += goals_against
        if goals_for > goals_against:
            self.wins += 1
        elif goals_for < goals_against:
            self.losses += 1
        else:
            self.draws += 1

    def sort_key(self) -> tuple:
        return (self.points, self.goal_difference, self.goals_for, self.name)
