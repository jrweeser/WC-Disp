from __future__ import annotations

import customtkinter as ctk

from config import FETCH_INTERVAL_SECONDS
from data.fetcher import DataFetcher
from data.tournament import TournamentState
from ui.match_center_panel import MatchCenterPanel
from ui.standings_panel import StandingsPanel


class WorldCupTrackerApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("World Cup Tracker")
        self.geometry("1280x800")
        self.minsize(960, 600)

        self._state = TournamentState()
        self._fetcher: DataFetcher | None = None

        self._build_layout()
        self._start_data_fetcher()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        divider_color = "#0d0d0d"
        self.configure(fg_color=divider_color)

        self._standings = StandingsPanel(self, self._state)
        self._standings.grid(row=0, column=0, sticky="nsew", padx=(0, 1))

        self._match_center = MatchCenterPanel(self, self._state)
        self._match_center.grid(row=0, column=1, sticky="nsew", padx=(1, 0))

    def _start_data_fetcher(self) -> None:
        self._fetcher = DataFetcher(
            state=self._state,
            on_update=self._schedule_ui_refresh,
            interval_seconds=FETCH_INTERVAL_SECONDS,
        )
        self._fetcher.start()
        self._refresh_ui()

    def _schedule_ui_refresh(self) -> None:
        self.after(0, self._refresh_ui)

    def _refresh_ui(self) -> None:
        self._standings.refresh()
        self._match_center.refresh()

    def _on_close(self) -> None:
        if self._fetcher:
            self._fetcher.stop()
        self.destroy()
