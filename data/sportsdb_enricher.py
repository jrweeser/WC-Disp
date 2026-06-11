from __future__ import annotations

import logging

import requests

from config import SPORTSDB_BASE_URL
from data.time_utils import utc_iso_to_local_naive
from models.match import Match, MatchEvent, MatchStatus

logger = logging.getLogger(__name__)

LIVE_STATUSES = {"1H", "2H", "HT", "ET", "BT", "P", "LIVE", "IN PLAY"}
FINISHED_STATUSES = {"FT", "AET", "AP", "PEN", "AWD", "WO"}


class SportsDbEnricher:
    """TheSportsDB enrichment: local kickoff times and live timelines."""

    def __init__(self) -> None:
        self._event_index: dict[tuple[str, str, str], dict] | None = None
        self._pair_index: dict[tuple[str, str], dict] | None = None

    def apply_kickoffs(self, matches: list[Match]) -> None:
        """Replace stadium-local API times with the viewer's local timezone."""
        self._ensure_event_index()
        for match in matches:
            event = self._find_event(match)
            if not event:
                continue
            local_kickoff = utc_iso_to_local_naive(event.get("strTimestamp", ""))
            if local_kickoff:
                match.kickoff = local_kickoff

    def enrich(self, matches: list[Match]) -> None:
        self._ensure_event_index()
        for match in matches:
            if match.status != MatchStatus.LIVE:
                continue
            event = self._find_event(match)
            if not event:
                continue
            self._apply_event_status(match, event)
            self._apply_timeline(match, event["idEvent"])

    def _ensure_event_index(self) -> None:
        if self._event_index is not None:
            return
        self._event_index = {}
        self._pair_index = {}
        try:
            response = requests.get(
                f"{SPORTSDB_BASE_URL}/eventsseason.php",
                params={"id": 4429, "s": "2026"},
                timeout=20,
            )
            response.raise_for_status()
            for event in response.json().get("events") or []:
                home = event.get("strHomeTeam", "")
                away = event.get("strAwayTeam", "")
                date = event.get("dateEvent", "")
                key = self._event_key(home, away, date)
                self._event_index[key] = event
                self._pair_index[self._pair_key(home, away)] = event
        except requests.RequestException as exc:
            logger.warning("TheSportsDB season events unavailable: %s", exc)
            self._event_index = {}
            self._pair_index = {}

    def _event_key(self, home: str, away: str, date: str) -> tuple[str, str, str]:
        return (home.strip().lower(), away.strip().lower(), date)

    def _pair_key(self, home: str, away: str) -> tuple[str, str]:
        return (home.strip().lower(), away.strip().lower())

    def _find_event(self, match: Match) -> dict | None:
        if not self._event_index:
            return None
        date = match.kickoff.strftime("%Y-%m-%d")
        event = self._event_index.get(
            self._event_key(match.home_name, match.away_name, date)
        )
        if event:
            return event
        if self._pair_index:
            return self._pair_index.get(
                self._pair_key(match.home_name, match.away_name)
            )
        return None

    def _apply_event_status(self, match: Match, event: dict) -> None:
        status = (event.get("strStatus") or "").upper()
        if status in LIVE_STATUSES:
            match.status = MatchStatus.LIVE
        elif status in FINISHED_STATUSES:
            match.status = MatchStatus.FINISHED

        home_score = event.get("intHomeScore")
        away_score = event.get("intAwayScore")
        if home_score is not None:
            match.home_score = int(home_score)
        if away_score is not None:
            match.away_score = int(away_score)

        progress = event.get("strProgress") or ""
        if progress.endswith("'"):
            try:
                match.minute = int(progress.rstrip("'"))
            except ValueError:
                pass

    def _apply_timeline(self, match: Match, event_id: str) -> None:
        try:
            response = requests.get(
                f"{SPORTSDB_BASE_URL}/lookuptimeline.php",
                params={"id": event_id},
                timeout=15,
            )
            response.raise_for_status()
            timeline = response.json().get("timeline") or []
        except requests.RequestException:
            return

        events: list[MatchEvent] = []
        for item in timeline:
            minute = int(item.get("intTime") or 0)
            player = item.get("strPlayer") or "Unknown"
            team_name = (item.get("strTeam") or "").strip()
            team_code = match.home_code if team_name == match.home_name else match.away_code
            detail = item.get("strTimelineDetail") or ""
            timeline_type = (item.get("strTimeline") or "").lower()

            if "goal" in timeline_type:
                event_type = "goal"
            elif "yellow" in timeline_type:
                event_type = "yellow_card"
            elif "red" in timeline_type:
                event_type = "red_card"
            elif "subst" in timeline_type:
                event_type = "substitution"
            else:
                event_type = "event"

            events.append(MatchEvent(minute, event_type, team_code, player, detail))

        if events:
            match.events = sorted(events, key=lambda e: e.minute)
