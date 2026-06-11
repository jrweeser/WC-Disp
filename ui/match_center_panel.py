from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from data.flag_cache import FlagCache
from data.tournament import TournamentState
from models.match import Match
from ui.widgets import StatBar

LIVE_ACCENT = "#c0392b"
SCHEDULED_COLOR = "#3a3a3a"
FINISHED_COLOR = "#2a2a2a"


class MatchCenterPanel(ctk.CTkFrame):
    def __init__(self, master, state: TournamentState, **kwargs) -> None:
        super().__init__(master, corner_radius=0, **kwargs)
        self._state = state
        self._flag_cache = FlagCache.get()
        self._image_refs: list[ctk.CTkImage] = []
        self._countdown_job: str | None = None

        self._header = ctk.CTkLabel(
            self,
            text="Match Center",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self._header.pack(pady=(16, 8), padx=16, anchor="w")

        self._live_container = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=12)
        self._schedule_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")

        self._live_widgets_built = False
        self._schedule_rows: list[ctk.CTkFrame] = []

    def refresh(self) -> None:
        self._image_refs.clear()
        _, matches = self._state.snapshot()
        live = self._state.primary_live_match

        if live:
            self._show_live(live)
        else:
            self._show_schedule(matches)

    def _clear_countdown(self) -> None:
        if self._countdown_job:
            self.after_cancel(self._countdown_job)
            self._countdown_job = None

    def _show_live(self, match: Match) -> None:
        self._clear_countdown()
        self._schedule_scroll.pack_forget()
        self._live_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        if not self._live_widgets_built:
            self._build_live_dashboard()
            self._live_widgets_built = True

        self._update_live_dashboard(match)

    def _build_live_dashboard(self) -> None:
        badge = ctk.CTkLabel(
            self._live_container,
            text="● LIVE",
            text_color=LIVE_ACCENT,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        badge.pack(pady=(14, 4))

        score_row = ctk.CTkFrame(self._live_container, fg_color="transparent")
        score_row.pack(fill="x", padx=20, pady=8)

        self._home_side = ctk.CTkFrame(score_row, fg_color="transparent")
        self._home_side.pack(side="left", expand=True)
        self._home_flag = ctk.CTkLabel(self._home_side, text="")
        self._home_flag.pack(side="left", padx=(0, 8))
        self._home_name = ctk.CTkLabel(
            self._home_side, text="", font=ctk.CTkFont(size=18, weight="bold")
        )
        self._home_name.pack(side="left")

        center = ctk.CTkFrame(score_row, fg_color="transparent")
        center.pack(side="left", padx=16)
        self._score_label = ctk.CTkLabel(
            center, text="0 - 0", font=ctk.CTkFont(size=32, weight="bold")
        )
        self._score_label.pack()
        self._clock_label = ctk.CTkLabel(
            center, text="0'", font=ctk.CTkFont(size=14), text_color="#aaaaaa"
        )
        self._clock_label.pack()

        self._away_side = ctk.CTkFrame(score_row, fg_color="transparent")
        self._away_side.pack(side="right", expand=True)
        self._away_name = ctk.CTkLabel(
            self._away_side, text="", font=ctk.CTkFont(size=18, weight="bold"), anchor="e"
        )
        self._away_name.pack(side="right")
        self._away_flag = ctk.CTkLabel(self._away_side, text="")
        self._away_flag.pack(side="right", padx=(8, 0))

        self._stats_frame = ctk.CTkFrame(self._live_container, fg_color="transparent")
        self._stats_frame.pack(fill="x", padx=20, pady=(8, 4))

        self._stat_bars = {
            "possession": StatBar(self._stats_frame, "Ball Possession"),
            "shots": StatBar(self._stats_frame, "Total Shots"),
            "on_target": StatBar(self._stats_frame, "Shots on Target"),
            "fouls": StatBar(self._stats_frame, "Fouls"),
            "corners": StatBar(self._stats_frame, "Corner Kicks"),
        }
        for bar in self._stat_bars.values():
            bar.pack(fill="x", pady=6)

        self._stats_unavailable = ctk.CTkLabel(
            self._live_container,
            text="Detailed match stats will appear when available.",
            font=ctk.CTkFont(size=12),
            text_color="#888888",
        )

        events_label = ctk.CTkLabel(
            self._live_container,
            text="Live Events",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        events_label.pack(fill="x", padx=20, pady=(12, 4))

        self._events_log = ctk.CTkTextbox(
            self._live_container,
            height=160,
            font=ctk.CTkFont(size=12),
            activate_scrollbars=True,
        )
        self._events_log.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self._events_log.configure(state="disabled")

    def _set_flag(self, label: ctk.CTkLabel, url: str) -> None:
        image = self._flag_cache.get_ctk_image(self, url)
        if image:
            self._image_refs.append(image)
            label.configure(image=image, text="")
        else:
            label.configure(image=None, text="")

    def _update_live_dashboard(self, match: Match) -> None:
        self._set_flag(self._home_flag, match.home_flag_url)
        self._set_flag(self._away_flag, match.away_flag_url)
        self._home_name.configure(text=match.home_name)
        self._away_name.configure(text=match.away_name)
        self._score_label.configure(text=f"{match.home_score}  -  {match.away_score}")
        self._clock_label.configure(text=f"{match.minute}'")

        if match.has_detailed_stats:
            self._stats_unavailable.pack_forget()
            self._stats_frame.pack(fill="x", padx=20, pady=(8, 4))
            s = match.stats
            self._stat_bars["possession"].set_values(
                s.possession_home, s.possession_away, percent=True
            )
            self._stat_bars["shots"].set_values(s.shots_home, s.shots_away)
            self._stat_bars["on_target"].set_values(
                s.shots_on_target_home, s.shots_on_target_away
            )
            self._stat_bars["fouls"].set_values(s.fouls_home, s.fouls_away)
            self._stat_bars["corners"].set_values(s.corners_home, s.corners_away)
        else:
            self._stats_frame.pack_forget()
            self._stats_unavailable.pack(pady=(4, 8))

        self._events_log.configure(state="normal")
        self._events_log.delete("1.0", "end")
        if match.events:
            for event in reversed(match.events):
                self._events_log.insert("end", event.label() + "\n")
        else:
            self._events_log.insert("end", "Waiting for match events...\n")
        self._events_log.configure(state="disabled")

    def _show_schedule(self, matches: list[Match]) -> None:
        self._live_container.pack_forget()
        self._schedule_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        for row in self._schedule_rows:
            row.destroy()
        self._schedule_rows.clear()

        for match in matches:
            row = self._build_schedule_row(match)
            self._schedule_rows.append(row)

        self._tick_countdowns(matches)

    def _build_schedule_row(self, match: Match) -> ctk.CTkFrame:
        if match.is_finished:
            bg = FINISHED_COLOR
        elif match.is_live:
            bg = "#3d2020"
        else:
            bg = SCHEDULED_COLOR

        row = ctk.CTkFrame(self._schedule_scroll, fg_color=bg, corner_radius=8)
        row.pack(fill="x", pady=4)

        date_str = match.kickoff.strftime("%b %d  %H:%M")
        ctk.CTkLabel(
            row, text=date_str, width=110, font=ctk.CTkFont(size=11), text_color="#aaaaaa"
        ).pack(side="left", padx=(12, 8), pady=10)

        teams_frame = ctk.CTkFrame(row, fg_color="transparent")
        teams_frame.pack(side="left", fill="x", expand=True, pady=10)

        home_flag = self._flag_cache.get_ctk_image(self, match.home_flag_url)
        if home_flag:
            self._image_refs.append(home_flag)
            ctk.CTkLabel(teams_frame, text="", image=home_flag, width=22).pack(
                side="left", padx=(0, 4)
            )
        ctk.CTkLabel(
            teams_frame, text=match.home_name, font=ctk.CTkFont(size=13)
        ).pack(side="left")

        ctk.CTkLabel(
            teams_frame, text=" vs ", font=ctk.CTkFont(size=12), text_color="#888888"
        ).pack(side="left", padx=4)

        away_flag = self._flag_cache.get_ctk_image(self, match.away_flag_url)
        if away_flag:
            self._image_refs.append(away_flag)
            ctk.CTkLabel(teams_frame, text="", image=away_flag, width=22).pack(
                side="left", padx=(0, 4)
            )
        ctk.CTkLabel(
            teams_frame, text=match.away_name, font=ctk.CTkFont(size=13)
        ).pack(side="left")

        status_frame = ctk.CTkFrame(row, fg_color="transparent")
        status_frame.pack(side="right", padx=12, pady=10)

        if match.is_finished:
            ctk.CTkLabel(
                status_frame,
                text=f"FT  {match.home_score} - {match.away_score}",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack()
        elif match.is_live:
            ctk.CTkLabel(
                status_frame,
                text=f"LIVE {match.home_score}-{match.away_score} ({match.minute}')",
                text_color=LIVE_ACCENT,
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack()
        else:
            lbl = ctk.CTkLabel(
                status_frame,
                text="",
                font=ctk.CTkFont(size=12),
                text_color="#5dade2",
            )
            lbl.pack()
            row._countdown_label = lbl  # type: ignore[attr-defined]
            row._kickoff = match.kickoff  # type: ignore[attr-defined]

        group_lbl = ctk.CTkLabel(
            row,
            text=f"Grp {match.group_letter}",
            width=48,
            font=ctk.CTkFont(size=10),
            text_color="#777",
        )
        group_lbl.pack(side="right", padx=(0, 4), pady=10)

        return row

    def _tick_countdowns(self, matches: list[Match]) -> None:
        self._clear_countdown()
        now = datetime.now()

        for row in self._schedule_rows:
            if not hasattr(row, "_countdown_label"):
                continue
            delta = row._kickoff - now  # type: ignore[attr-defined]
            if delta.total_seconds() <= 0:
                row._countdown_label.configure(text="Starting soon")  # type: ignore[attr-defined]
            else:
                hrs, rem = divmod(int(delta.total_seconds()), 3600)
                mins, secs = divmod(rem, 60)
                if hrs > 24:
                    days = hrs // 24
                    row._countdown_label.configure(text=f"in {days}d {hrs % 24}h")  # type: ignore[attr-defined]
                elif hrs > 0:
                    row._countdown_label.configure(text=f"in {hrs}h {mins}m")  # type: ignore[attr-defined]
                else:
                    row._countdown_label.configure(text=f"in {mins}m {secs}s")  # type: ignore[attr-defined]

        self._countdown_job = self.after(1000, lambda: self._tick_countdowns(matches))
