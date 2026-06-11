from __future__ import annotations

import json
import logging
from datetime import datetime

import requests

from config import FOOTBALL_DATA_API_KEY, FOOTBALL_DATA_BASE_URL, WORLDCUP26_BASE_URL
from data.api_client import SportsDataClient
from data.sportsdb_enricher import SportsDbEnricher
from models.group import Group
from models.match import Match, MatchEvent, MatchStats, MatchStatus
from models.team import Team

logger = logging.getLogger(__name__)


class WorldCup26Client(SportsDataClient):
    """Free World Cup 2026 API — no key required (worldcup26.ir)."""

    def __init__(self) -> None:
        self._teams_by_id: dict[str, dict] = {}
        self._sportsdb = SportsDbEnricher()

    def fetch_tournament(self) -> tuple[dict[str, Group], list[Match]]:
        teams = self._fetch_json("/get/teams").get("teams", [])
        groups_data = self._fetch_json("/get/groups").get("groups", [])
        games = self._fetch_json("/get/games").get("games", [])

        self._teams_by_id = {str(team["id"]): team for team in teams}
        groups = self._parse_groups(groups_data)
        matches = self._parse_matches(games)
        self._sportsdb.enrich(matches)

        live = next((m for m in matches if m.is_live), None)
        if live and FOOTBALL_DATA_API_KEY:
            self._enrich_live_stats(live)

        return groups, matches

    def _fetch_json(self, path: str) -> dict:
        response = requests.get(f"{WORLDCUP26_BASE_URL}{path}", timeout=25)
        response.raise_for_status()
        return response.json()

    def _parse_groups(self, groups_data: list[dict]) -> dict[str, Group]:
        groups: dict[str, Group] = {}
        for group_data in groups_data:
            letter = str(group_data.get("name", "")).upper()
            teams: list[Team] = []
            for row in group_data.get("teams", []):
                team_info = self._teams_by_id.get(str(row.get("team_id")))
                if not team_info:
                    continue
                teams.append(
                    Team(
                        code=team_info.get("fifa_code") or team_info.get("iso2", ""),
                        name=team_info.get("name_en", "Unknown"),
                        group_letter=letter,
                        wins=int(row.get("w") or 0),
                        losses=int(row.get("l") or 0),
                        draws=int(row.get("d") or 0),
                        goals_for=int(row.get("gf") or 0),
                        goals_against=int(row.get("ga") or 0),
                        flag_url=team_info.get("flag", ""),
                        flag_iso=str(team_info.get("iso2", "")).lower(),
                    )
                )
            groups[letter] = Group(letter=letter, teams=teams)
        return groups

    def _parse_matches(self, games: list[dict]) -> list[Match]:
        matches: list[Match] = []
        for game in games:
            home_id = str(game.get("home_team_id", ""))
            away_id = str(game.get("away_team_id", ""))
            home = self._teams_by_id.get(home_id, {})
            away = self._teams_by_id.get(away_id, {})

            home_name = game.get("home_team_name_en") or home.get("name_en", "TBD")
            away_name = game.get("away_team_name_en") or away.get("name_en", "TBD")
            home_code = home.get("fifa_code") or home.get("iso2", home_name[:3].upper())
            away_code = away.get("fifa_code") or away.get("iso2", away_name[:3].upper())

            status, minute = self._parse_status(game)
            events = self._parse_scorers(game, home_code, away_code)

            matches.append(
                Match(
                    id=str(game.get("_id") or game.get("id")),
                    home_code=home_code,
                    away_code=away_code,
                    home_name=home_name,
                    away_name=away_name,
                    kickoff=self._parse_kickoff(game.get("local_date", "")),
                    group_letter=str(game.get("group", "")).upper(),
                    status=status,
                    home_score=int(game.get("home_score") or 0),
                    away_score=int(game.get("away_score") or 0),
                    minute=minute,
                    events=events,
                    home_flag_url=home.get("flag", ""),
                    away_flag_url=away.get("flag", ""),
                )
            )
        matches.sort(key=lambda m: m.kickoff)
        return matches

    def _parse_kickoff(self, local_date: str) -> datetime:
        try:
            return datetime.strptime(local_date, "%m/%d/%Y %H:%M")
        except ValueError:
            return datetime.now()

    def _parse_status(self, game: dict) -> tuple[MatchStatus, int]:
        finished = str(game.get("finished", "")).upper() == "TRUE"
        elapsed = str(game.get("time_elapsed", "notstarted")).strip().lower()

        if finished:
            return MatchStatus.FINISHED, 90

        if elapsed not in ("notstarted", "null", ""):
            try:
                return MatchStatus.LIVE, int(elapsed)
            except ValueError:
                return MatchStatus.LIVE, 0

        return MatchStatus.SCHEDULED, 0

    def _parse_scorers(
        self, game: dict, home_code: str, away_code: str
    ) -> list[MatchEvent]:
        events: list[MatchEvent] = []
        for field, team_code in (("home_scorers", home_code), ("away_scorers", away_code)):
            raw = game.get(field)
            if not raw or raw == "null":
                continue
            try:
                scorers = json.loads(raw) if isinstance(raw, str) else raw
            except json.JSONDecodeError:
                continue
            if not isinstance(scorers, list):
                continue
            for scorer in scorers:
                if isinstance(scorer, dict):
                    player = scorer.get("name") or scorer.get("player") or "Unknown"
                    minute = int(scorer.get("minute") or scorer.get("time") or 0)
                else:
                    player = str(scorer)
                    minute = 0
                events.append(MatchEvent(minute, "goal", team_code, player))
        return sorted(events, key=lambda e: e.minute)

    def _enrich_live_stats(self, match: Match) -> None:
        try:
            response = requests.get(
                f"{FOOTBALL_DATA_BASE_URL}/competitions/WC/matches",
                headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
                params={"status": "LIVE"},
                timeout=15,
            )
            if response.status_code != 200:
                return
            for item in response.json().get("matches", []):
                home = item.get("homeTeam", {}).get("name", "")
                away = item.get("awayTeam", {}).get("name", "")
                if home != match.home_name and away != match.away_name:
                    continue
                detail = requests.get(
                    f"{FOOTBALL_DATA_BASE_URL}/matches/{item['id']}",
                    headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
                    timeout=15,
                )
                if detail.status_code != 200:
                    return
                self._apply_football_data_stats(match, detail.json())
                return
        except requests.RequestException as exc:
            logger.debug("football-data.org enrichment skipped: %s", exc)

    def _apply_football_data_stats(self, match: Match, payload: dict) -> None:
        home_stats = payload.get("homeTeam", {}).get("statistics") or {}
        away_stats = payload.get("awayTeam", {}).get("statistics") or {}
        if not home_stats and not away_stats:
            return

        match.stats = MatchStats(
            possession_home=float(home_stats.get("ball_possession") or 50),
            possession_away=float(away_stats.get("ball_possession") or 50),
            shots_home=int(home_stats.get("shots") or 0),
            shots_away=int(away_stats.get("shots") or 0),
            shots_on_target_home=int(home_stats.get("shots_on_goal") or 0),
            shots_on_target_away=int(away_stats.get("shots_on_goal") or 0),
            fouls_home=int(home_stats.get("fouls") or 0),
            fouls_away=int(away_stats.get("fouls") or 0),
            corners_home=int(home_stats.get("corner_kicks") or 0),
            corners_away=int(away_stats.get("corner_kicks") or 0),
        )
        match.has_detailed_stats = True

        if payload.get("minute"):
            match.minute = int(payload["minute"])

        events: list[MatchEvent] = []
        for goal in payload.get("goals") or []:
            team_name = goal.get("team", {}).get("name", "")
            code = match.home_code if team_name == match.home_name else match.away_code
            events.append(
                MatchEvent(
                    int(goal.get("minute") or 0),
                    "goal",
                    code,
                    goal.get("scorer", {}).get("name", "Unknown"),
                    goal.get("type", ""),
                )
            )
        for booking in payload.get("bookings") or []:
            team_name = booking.get("team", {}).get("name", "")
            code = match.home_code if team_name == match.home_name else match.away_code
            card = (booking.get("card") or "").lower()
            event_type = "red_card" if "red" in card else "yellow_card"
            events.append(
                MatchEvent(
                    int(booking.get("minute") or 0),
                    event_type,
                    code,
                    booking.get("player", {}).get("name", "Unknown"),
                )
            )
        if events:
            match.events = sorted(events, key=lambda e: e.minute)
