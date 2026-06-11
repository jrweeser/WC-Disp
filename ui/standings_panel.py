from __future__ import annotations

import customtkinter as ctk

from data.flag_cache import FlagCache
from data.tournament import TournamentState
from models.team import Team
from ui import theme

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
            font=theme.font(theme.PANEL_TITLE, "bold"),
        )
        header.pack(pady=(12, 6), padx=16, anchor="w")

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ctk.CTkFrame(self._scroll, fg_color="transparent")
        columns.pack(fill="both", expand=True)
        columns.grid_columnconfigure(0, weight=1)
        columns.grid_columnconfigure(1, weight=1)

        self._col_left = ctk.CTkFrame(columns, fg_color="transparent")
        self._col_right = ctk.CTkFrame(columns, fg_color="transparent")
        self._col_left.grid(row=0, column=0, sticky="new", padx=(0, 5))
        self._col_right.grid(row=0, column=1, sticky="new", padx=(5, 0))

        self._group_frames: dict[str, ctk.CTkFrame] = {}
        self._row_widgets: dict[str, list[ctk.CTkFrame]] = {}

    def refresh(self) -> None:
        self._image_refs.clear()
        groups, _ = self._state.snapshot()
        for index, letter in enumerate(sorted(groups.keys())):
            group = groups[letter]
            if letter not in self._group_frames:
                self._build_group_card(letter, index)
            self._update_group_card(letter, group.sorted_teams)

    def _column_for_index(self, index: int) -> ctk.CTkFrame:
        return self._col_left if index % theme.GROUP_COLS == 0 else self._col_right

    def _build_group_card(self, letter: str, index: int) -> None:
        parent = self._column_for_index(index)
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1a1a1a")
        card.pack(fill="x", pady=4)

        title = ctk.CTkLabel(
            card,
            text=f"Group {letter}",
            font=theme.font(theme.GROUP_TITLE, "bold"),
            anchor="w",
        )
        title.pack(fill="x", padx=10, pady=(8, 4))

        header_row = ctk.CTkFrame(
            card, fg_color=HEADER_COLOR, corner_radius=6, height=theme.GROUP_HEADER_HEIGHT
        )
        header_row.pack(fill="x", padx=6, pady=(0, 3))
        header_row.pack_propagate(False)
        for col, width in [
            ("Team", theme.GROUP_TEAM_WIDTH),
            ("W", theme.GROUP_STAT_WIDTH),
            ("L", theme.GROUP_STAT_WIDTH),
            ("D", theme.GROUP_STAT_WIDTH),
            ("GD", theme.GROUP_STAT_WIDTH + 4),
            ("PTS", theme.GROUP_STAT_WIDTH + 4),
        ]:
            ctk.CTkLabel(
                header_row,
                text=col,
                width=width,
                font=theme.font(theme.GROUP_HEADER, "bold"),
            ).pack(side="left", padx=1)

        rows: list[ctk.CTkFrame] = []
        for _ in range(4):
            row = ctk.CTkFrame(
                card, fg_color=ROW_DEFAULT, corner_radius=4, height=theme.GROUP_ROW_HEIGHT
            )
            row.pack(fill="x", padx=6, pady=1)
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

            team_cell = ctk.CTkFrame(row, fg_color="transparent", width=theme.GROUP_TEAM_WIDTH)
            team_cell.pack(side="left", padx=1)
            team_cell.pack_propagate(False)

            flag_image = self._flag_cache.get_ctk_image(
                self, team.flag_url, theme.FLAG_STANDINGS
            )
            if flag_image:
                self._image_refs.append(flag_image)
                ctk.CTkLabel(team_cell, text="", image=flag_image, width=34).pack(
                    side="left", padx=(2, 4)
                )

            name_text = f"{'▸ ' if qualified else '  '}{team.name}"
            ctk.CTkLabel(
                team_cell,
                text=name_text,
                anchor="w",
                font=theme.font(theme.GROUP_ROW, "bold" if qualified else "normal"),
                text_color="#e8f5e9" if qualified else None,
            ).pack(side="left", fill="x", expand=True)

            cols = [
                (str(team.wins), theme.GROUP_STAT_WIDTH),
                (str(team.losses), theme.GROUP_STAT_WIDTH),
                (str(team.draws), theme.GROUP_STAT_WIDTH),
                (f"{team.goal_difference:+d}", theme.GROUP_STAT_WIDTH + 4),
                (str(team.points), theme.GROUP_STAT_WIDTH + 4),
            ]
            for text, width in cols:
                ctk.CTkLabel(
                    row,
                    text=text,
                    width=width,
                    anchor="center",
                    font=theme.font(theme.GROUP_ROW, "bold" if qualified else "normal"),
                    text_color="#e8f5e9" if qualified else None,
                ).pack(side="left", padx=1)
