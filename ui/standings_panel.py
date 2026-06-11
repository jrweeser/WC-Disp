from __future__ import annotations

import customtkinter as ctk

from data.flag_cache import FlagCache
from data.tournament import TournamentState
from models.team import Team

QUALIFY_FG = "#2d6a4f"
ROW_ALT = "#2a2a2a"
ROW_DEFAULT = "#242424"
HEADER_COLOR = "#1e1e1e"


class StandingsPanel(ctk.CTkFrame):
    def __init__(self, master, state: TournamentState, **kwargs) -> None:
        super().__init__(master, corner_radius=0, **kwargs)
        self._state = state
        self._flag_cache = FlagCache.get()
        self._image_refs: list[ctk.CTkImage] = []

        header = ctk.CTkLabel(
            self,
            text="Group Standings",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        header.pack(pady=(16, 8), padx=16, anchor="w")

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._group_frames: dict[str, ctk.CTkFrame] = {}
        self._row_widgets: dict[str, list[ctk.CTkFrame]] = {}

    def refresh(self) -> None:
        self._image_refs.clear()
        groups, _ = self._state.snapshot()
        for letter in sorted(groups.keys()):
            group = groups[letter]
            if letter not in self._group_frames:
                self._build_group_card(letter)
            self._update_group_card(letter, group.sorted_teams)

    def _build_group_card(self, letter: str) -> None:
        card = ctk.CTkFrame(self._scroll, corner_radius=10, fg_color="#1a1a1a")
        card.pack(fill="x", pady=6)

        title = ctk.CTkLabel(
            card,
            text=f"Group {letter}",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        )
        title.pack(fill="x", padx=12, pady=(10, 6))

        header_row = ctk.CTkFrame(card, fg_color=HEADER_COLOR, corner_radius=6, height=28)
        header_row.pack(fill="x", padx=8, pady=(0, 4))
        header_row.pack_propagate(False)
        for col, width in [("Team", 150), ("W", 28), ("L", 28), ("D", 28), ("GD", 36), ("PTS", 36)]:
            ctk.CTkLabel(
                header_row,
                text=col,
                width=width,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(side="left", padx=2)

        rows: list[ctk.CTkFrame] = []
        for _ in range(4):
            row = ctk.CTkFrame(card, fg_color=ROW_DEFAULT, corner_radius=4, height=32)
            row.pack(fill="x", padx=8, pady=2)
            row.pack_propagate(False)
            rows.append(row)

        self._group_frames[letter] = card
        self._row_widgets[letter] = rows

    def _update_group_card(self, letter: str, teams: list[Team]) -> None:
        rows = self._row_widgets[letter]
        for idx, team in enumerate(teams):
            row = rows[idx]
            for child in row.winfo_children():
                child.destroy()

            qualified = idx < 2
            bg = QUALIFY_FG if qualified else (ROW_ALT if idx % 2 else ROW_DEFAULT)
            row.configure(fg_color=bg)

            team_cell = ctk.CTkFrame(row, fg_color="transparent", width=150)
            team_cell.pack(side="left", padx=2)
            team_cell.pack_propagate(False)

            flag_image = self._flag_cache.get_ctk_image(self, team.flag_url)
            if flag_image:
                self._image_refs.append(flag_image)
                ctk.CTkLabel(team_cell, text="", image=flag_image, width=26).pack(
                    side="left", padx=(2, 4)
                )

            name_text = f"{'▸ ' if qualified else '  '}{team.name}"
            ctk.CTkLabel(
                team_cell,
                text=name_text,
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold" if qualified else "normal"),
                text_color="#e8f5e9" if qualified else None,
            ).pack(side="left", fill="x", expand=True)

            cols = [
                (str(team.wins), 28),
                (str(team.losses), 28),
                (str(team.draws), 28),
                (f"{team.goal_difference:+d}", 36),
                (str(team.points), 36),
            ]
            for text, width in cols:
                ctk.CTkLabel(
                    row,
                    text=text,
                    width=width,
                    anchor="center",
                    font=ctk.CTkFont(size=12, weight="bold" if qualified else "normal"),
                    text_color="#e8f5e9" if qualified else None,
                ).pack(side="left", padx=2)
