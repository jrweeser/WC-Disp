from __future__ import annotations

import threading
from dataclasses import dataclass, field

from models.group import Group
from models.match import Match, MatchStatus
from models.team import Team


@dataclass
class TournamentState:
    groups: dict[str, Group] = field(default_factory=dict)
    matches: list[Match] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def get_team(self, code: str) -> Team | None:
        for group in self.groups.values():
            team = group.get_team(code)
            if team:
                return team
        return None

    def get_group_for_team(self, code: str) -> Group | None:
        for group in self.groups.values():
            if group.get_team(code):
                return group
        return None

    @property
    def live_matches(self) -> list[Match]:
        return [m for m in self.matches if m.is_live]

    @property
    def primary_live_match(self) -> Match | None:
        live = self.live_matches
        return live[0] if live else None

    def apply_match_result(self, match: Match) -> None:
        if match.status != MatchStatus.FINISHED:
            return
        home = self.get_team(match.home_code)
        away = self.get_team(match.away_code)
        if home and away:
            home.record_result(match.home_score, match.away_score)
            away.record_result(match.away_score, match.home_score)

    def snapshot(self) -> tuple[dict[str, Group], list[Match]]:
        with self._lock:
            return self.groups, list(self.matches)

    def update(self, groups: dict[str, Group], matches: list[Match]) -> None:
        with self._lock:
            self.groups = groups
            self.matches = matches
