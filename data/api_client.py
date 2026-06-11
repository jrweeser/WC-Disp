from __future__ import annotations

import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from models.group import Group
from models.match import Match, MatchEvent, MatchStats, MatchStatus
from models.team import Team


GROUP_DATA: dict[str, list[tuple[str, str]]] = {
    "A": [("USA", "United States"), ("MEX", "Mexico"), ("CAN", "Canada"), ("JAM", "Jamaica")],
    "B": [("BRA", "Brazil"), ("ARG", "Argentina"), ("COL", "Colombia"), ("CHI", "Chile")],
    "C": [("FRA", "France"), ("GER", "Germany"), ("ESP", "Spain"), ("POR", "Portugal")],
    "D": [("ENG", "England"), ("NED", "Netherlands"), ("BEL", "Belgium"), ("CRO", "Croatia")],
    "E": [("JPN", "Japan"), ("KOR", "South Korea"), ("AUS", "Australia"), ("SAU", "Saudi Arabia")],
    "F": [("MAR", "Morocco"), ("SEN", "Senegal"), ("NGA", "Nigeria"), ("GHA", "Ghana")],
    "G": [("URU", "Uruguay"), ("ECU", "Ecuador"), ("PER", "Peru"), ("PAR", "Paraguay")],
    "H": [("ITA", "Italy"), ("SUI", "Switzerland"), ("DEN", "Denmark"), ("SRB", "Serbia")],
}

PLAYERS = [
    "Martinez", "Silva", "Johnson", "Kim", "Müller", "Santos",
    "Williams", "Garcia", "Anderson", "Dubois", "Okonkwo", "Rossi",
]


class SportsDataClient(ABC):
    @abstractmethod
    def fetch_tournament(self) -> tuple[dict[str, Group], list[Match]]:
        ...


class MockSportsDataClient(SportsDataClient):
    """Simulates live API data for development and demo purposes."""

    def __init__(self) -> None:
        self._tick = 0
        self._groups = self._build_initial_groups()
        self._matches = self._build_schedule()
        self._simulate_progress()

    def _build_initial_groups(self) -> dict[str, Group]:
        groups: dict[str, Group] = {}
        for letter, teams in GROUP_DATA.items():
            groups[letter] = Group(
                letter=letter,
                teams=[Team(code=c, name=n, group_letter=letter) for c, n in teams],
            )
        return groups

    def _build_schedule(self) -> list[Match]:
        matches: list[Match] = []
        base = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
        match_id = 0
        for letter, teams in GROUP_DATA.items():
            codes = [t[0] for t in teams]
            pairings = [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]
            for day_offset, (i, j) in enumerate(pairings):
                home, away = codes[i], codes[j]
                home_name = dict(teams)[home]
                away_name = dict(teams)[away]
                kickoff = base + timedelta(days=day_offset, hours=(ord(letter) - ord("A")) * 2)
                matches.append(
                    Match(
                        id=f"m{match_id}",
                        home_code=home,
                        away_code=away,
                        home_name=home_name,
                        away_name=away_name,
                        kickoff=kickoff,
                        group_letter=letter,
                    )
                )
                match_id += 1
        matches.sort(key=lambda m: m.kickoff)
        return matches

    def _simulate_progress(self) -> None:
        now = datetime.now()
        finished_count = 0
        live_set = False

        for match in self._matches:
            if finished_count < 4 and match.kickoff <= now - timedelta(hours=2):
                match.status = MatchStatus.FINISHED
                match.home_score = random.randint(0, 3)
                match.away_score = random.randint(0, 3)
                match.minute = 90
                self._apply_finished_stats(match)
                finished_count += 1
            elif not live_set and match.kickoff <= now <= match.kickoff + timedelta(minutes=90):
                match.status = MatchStatus.LIVE
                elapsed = int((now - match.kickoff).total_seconds() / 60)
                match.minute = min(elapsed, 90)
                self._seed_live_match(match)
                live_set = True

    def _apply_finished_stats(self, match: Match) -> None:
        home = self._groups[match.group_letter].get_team(match.home_code)
        away = self._groups[match.group_letter].get_team(match.away_code)
        if home and away:
            home.record_result(match.home_score, match.away_score)
            away.record_result(match.away_score, match.home_score)

    def _seed_live_match(self, match: Match) -> None:
        if match.events:
            return
        match.home_score = random.randint(0, 2)
        match.away_score = random.randint(0, 2)
        match.stats = MatchStats(
            possession_home=random.uniform(40, 60),
            possession_away=100 - random.uniform(40, 60),
            shots_home=random.randint(4, 12),
            shots_away=random.randint(4, 12),
            shots_on_target_home=random.randint(2, 6),
            shots_on_target_away=random.randint(2, 6),
            fouls_home=random.randint(5, 14),
            fouls_away=random.randint(5, 14),
            corners_home=random.randint(2, 8),
            corners_away=random.randint(2, 8),
        )
        match.stats.possession_away = 100 - match.stats.possession_home
        for _ in range(match.home_score):
            match.events.append(
                MatchEvent(
                    random.randint(1, match.minute),
                    "goal",
                    match.home_code,
                    random.choice(PLAYERS),
                )
            )
        for _ in range(match.away_score):
            match.events.append(
                MatchEvent(
                    random.randint(1, match.minute),
                    "goal",
                    match.away_code,
                    random.choice(PLAYERS),
                )
            )
        match.events.sort(key=lambda e: e.minute)

    def _advance_live_matches(self) -> None:
        for match in self._matches:
            if not match.is_live:
                continue
            match.minute = min(match.minute + 1, 90)
            match.stats.shots_home += random.choice([0, 0, 1])
            match.stats.shots_away += random.choice([0, 0, 1])
            if random.random() < 0.15:
                delta = random.uniform(-2, 2)
                match.stats.possession_home = max(35, min(65, match.stats.possession_home + delta))
                match.stats.possession_away = 100 - match.stats.possession_home
            if random.random() < 0.08:
                team = random.choice([match.home_code, match.away_code])
                player = random.choice(PLAYERS)
                match.add_goal(team, player)
            if random.random() < 0.12:
                team = random.choice([match.home_code, match.away_code])
                etype = random.choice(["yellow_card", "substitution"])
                match.events.append(
                    MatchEvent(match.minute, etype, team, random.choice(PLAYERS))
                )
            if match.minute >= 90:
                match.status = MatchStatus.FINISHED
                self._apply_finished_stats(match)

    def _promote_next_live(self) -> None:
        now = datetime.now()
        if any(m.is_live for m in self._matches):
            return
        for match in self._matches:
            if match.status == MatchStatus.SCHEDULED and match.kickoff <= now:
                match.status = MatchStatus.LIVE
                match.minute = 1
                self._seed_live_match(match)
                break

    def fetch_tournament(self) -> tuple[dict[str, Group], list[Match]]:
        self._tick += 1
        self._advance_live_matches()
        self._promote_next_live()
        return self._groups, list(self._matches)
