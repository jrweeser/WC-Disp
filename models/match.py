from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MatchStatus(Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"


@dataclass
class MatchEvent:
    minute: int
    event_type: str
    team_code: str
    player: str
    detail: str = ""

    def label(self) -> str:
        icons = {
            "goal": "⚽",
            "yellow_card": "🟨",
            "red_card": "🟥",
            "substitution": "🔄",
        }
        icon = icons.get(self.event_type, "•")
        return f"{icon} {self.minute}' {self.player} ({self.team_code}) {self.detail}".strip()


@dataclass
class MatchStats:
    possession_home: float = 50.0
    possession_away: float = 50.0
    shots_home: int = 0
    shots_away: int = 0
    shots_on_target_home: int = 0
    shots_on_target_away: int = 0
    fouls_home: int = 0
    fouls_away: int = 0
    corners_home: int = 0
    corners_away: int = 0


@dataclass
class Match:
    id: str
    home_code: str
    away_code: str
    home_name: str
    away_name: str
    kickoff: datetime
    group_letter: str
    status: MatchStatus = MatchStatus.SCHEDULED
    home_score: int = 0
    away_score: int = 0
    minute: int = 0
    stats: MatchStats = field(default_factory=MatchStats)
    events: list[MatchEvent] = field(default_factory=list)
    home_flag_url: str = ""
    away_flag_url: str = ""
    has_detailed_stats: bool = False

    @property
    def is_live(self) -> bool:
        return self.status == MatchStatus.LIVE

    @property
    def is_finished(self) -> bool:
        return self.status == MatchStatus.FINISHED

    def add_goal(self, team_code: str, player: str, minute: int | None = None) -> None:
        m = minute if minute is not None else self.minute
        if team_code == self.home_code:
            self.home_score += 1
        else:
            self.away_score += 1
        self.events.append(MatchEvent(m, "goal", team_code, player))
