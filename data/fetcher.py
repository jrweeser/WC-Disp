from __future__ import annotations

import threading
from typing import Callable

from data.api_client import SportsDataClient
from data.client_factory import create_data_client
from data.flag_cache import FlagCache
from data.tournament import TournamentState


class DataFetcher:
    def __init__(
        self,
        state: TournamentState,
        on_update: Callable[[], None],
        client: SportsDataClient | None = None,
        interval_seconds: int = 45,
    ) -> None:
        self._state = state
        self._on_update = on_update
        self._client = client or create_data_client()
        self._interval = interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._fetch_once()
        self._thread = threading.Thread(target=self._run, daemon=True, name="DataFetcher")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _fetch_once(self) -> None:
        groups, matches = self._client.fetch_tournament()
        self._state.update(groups, matches)
        self._preload_flags(groups, matches)
        self._on_update()

    def _preload_flags(self, groups: dict, matches: list) -> None:
        urls: list[str] = []
        for group in groups.values():
            for team in group.teams:
                if team.flag_url:
                    urls.append(team.flag_url)
        for match in matches:
            if match.home_flag_url:
                urls.append(match.home_flag_url)
            if match.away_flag_url:
                urls.append(match.away_flag_url)
        FlagCache.get().preload(urls)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            if self._stop_event.wait(self._interval):
                break
            self._fetch_once()
