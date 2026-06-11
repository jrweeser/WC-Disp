"""Typography and layout tuned for a 1920x1080 split-pane window."""

import customtkinter as ctk

WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080

# Left panel (~960px) — two group columns
GROUP_COLS = 2
GROUP_TITLE = 20
GROUP_HEADER = 15
GROUP_ROW = 16
GROUP_ROW_HEIGHT = 36
GROUP_HEADER_HEIGHT = 32
GROUP_TEAM_WIDTH = 168
GROUP_STAT_WIDTH = 34

PANEL_TITLE = 28
SECTION_TITLE = 22

# Right panel — schedule & live
SCHEDULE_DATE = 15
SCHEDULE_TEAM = 17
SCHEDULE_STATUS = 16
SCHEDULE_ROW_PADY = 5

LIVE_BADGE = 18
LIVE_TEAM = 24
LIVE_SCORE = 52
LIVE_CLOCK = 18
LIVE_EVENTS_TITLE = 18
LIVE_EVENTS_BODY = 15
LIVE_STATS_LABEL = 14

FLAG_STANDINGS = (32, 22)
FLAG_SCHEDULE = (28, 20)
FLAG_LIVE = (44, 30)


def font(size: int, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(size=size, weight=weight)
