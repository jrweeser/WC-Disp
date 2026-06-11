from __future__ import annotations

import customtkinter as ctk


class StatBar(ctk.CTkFrame):
    """Horizontal comparison bar for a single match statistic."""

    def __init__(self, master, label: str, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._label = ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=12))
        self._label.pack(pady=(0, 4))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")

        self._home_val = ctk.CTkLabel(row, text="0", width=36, font=ctk.CTkFont(size=12, weight="bold"))
        self._home_val.pack(side="left")

        bar_frame = ctk.CTkFrame(row, fg_color="#2b2b2b", corner_radius=6, height=14)
        bar_frame.pack(side="left", fill="x", expand=True, padx=8)
        bar_frame.pack_propagate(False)

        self._home_bar = ctk.CTkFrame(bar_frame, fg_color="#1f6aa5", corner_radius=6, height=14)
        self._home_bar.place(relx=0, rely=0, relwidth=0.5, relheight=1)

        self._away_bar = ctk.CTkFrame(bar_frame, fg_color="#c0392b", corner_radius=6, height=14)
        self._away_bar.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)

        self._away_val = ctk.CTkLabel(row, text="0", width=36, font=ctk.CTkFont(size=12, weight="bold"))
        self._away_val.pack(side="right")

    def set_values(self, home: float, away: float, percent: bool = False) -> None:
        total = home + away if home + away else 1
        home_pct = home / total
        self._home_bar.place(relx=0, rely=0, relwidth=home_pct, relheight=1)
        self._away_bar.place(relx=home_pct, rely=0, relwidth=1 - home_pct, relheight=1)
        if percent:
            self._home_val.configure(text=f"{home:.0f}%")
            self._away_val.configure(text=f"{away:.0f}%")
        else:
            self._home_val.configure(text=str(int(home)))
            self._away_val.configure(text=str(int(away)))
