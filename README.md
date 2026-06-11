# World Cup Tracker

A desktop dashboard for the FIFA World Cup 2026, built in Python with CustomTkinter. The app provides a real-time tournament overview in a single window split into two panels: **group standings** on the left and **match schedule / live analytics** on the right.

Designed for a **1920×1080** display with large, readable typography and country flags throughout.

---

## Features

### Group Standings (Left Panel)

- Live standings for all **12 groups** (A–L) in a **two-column layout**
- Each group shows a four-team table with **W**, **L**, **D**, **GD**, and **PTS**
- Teams auto-sort by points, then goal difference, then goals scored
- The **top two teams** in each group are highlighted in green (qualification zone)
- **Country flags** beside every team name

### Match Center (Right Panel)

Two modes depending on whether a match is live:

**Schedule mode (no live match)**

- Chronological, scrollable list of all **104 tournament matches**
- Date/time, teams, flags, group label
- Final scores for completed matches
- Live countdown timers for upcoming matches

**Live mode (active match)**

- Scoreboard with flags, team names, live score, and match clock
- Stat comparison bars (when available): possession, shots, shots on target, fouls, corners
- Live event log: goals, cards, substitutions

### Backend

- Background thread fetches fresh data every **60 seconds** (configurable) without freezing the UI
- Thread-safe shared tournament state keeps both panels in sync
- Flag images are downloaded once and cached in memory

---

## Requirements

- **Python 3.10+** (tested on 3.14)
- An internet connection (for live data and flag images)
- A **1920×1080** display (the window is fixed to this resolution)

### Python packages

| Package | Purpose |
|---------|---------|
| `customtkinter` | Modern dark-theme GUI |
| `Pillow` | Flag image loading |
| `requests` | HTTP API calls |
| `python-dotenv` | Optional `.env` configuration |

---

## Installation

1. **Clone or download** this repository.

2. **Create a virtual environment** (recommended):

   ```powershell
   cd "WC Disp"
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   On macOS/Linux:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**:

   ```bash
   python main.py
   ```

---

## Configuration

Copy `.env.example` to `.env` in the project root to customize behavior:

```powershell
copy .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_MOCK_DATA` | `0` | Set to `1` to use simulated data instead of live APIs |
| `FETCH_INTERVAL_SECONDS` | `60` | How often the background thread refreshes data |
| `FOOTBALL_DATA_API_KEY` | *(empty)* | Optional free token for detailed live match stats |
| `WORLDCUP26_BASE_URL` | `https://worldcup26.ir` | Primary tournament data API |
| `SPORTSDB_BASE_URL` | `https://www.thesportsdb.com/api/v1/json/3` | Timeline and timezone enrichment API |

### Optional: football-data.org token

Register for a **free** API token at [football-data.org](https://www.football-data.org/client/register) and add it to `.env`:

```
FOOTBALL_DATA_API_KEY=your_token_here
```

This enables live match statistics (possession, shots, fouls, corners) during active games. Everything else works without it.

### Mock / offline development

Set `USE_MOCK_DATA=1` in `.env` to run with simulated groups, schedules, and a fake live match — useful for UI development without network access.

---

## Timezones

Match times are displayed in **your computer's local timezone**.

The primary API returns stadium-local kickoff times. The app cross-references [TheSportsDB](https://www.thesportsdb.com) for each match's UTC timestamp and converts it using Python's `datetime.astimezone()`. Countdown timers use the same local time.

The Match Center header shows **"Times in your local timezone"** as a reminder.

---

## Data Sources

All core data is **free** and requires no API key.

| Source | Role | Key required? |
|--------|------|---------------|
| [worldcup26.ir](https://worldcup26.ir) | Teams, 12 group standings, 104 matches, live scores | No |
| [TheSportsDB](https://www.thesportsdb.com) | UTC kickoff times, live event timelines | No (public tier) |
| [flagcdn.com](https://flagcdn.com) | Country flag images (via worldcup26 team data) | No |
| [football-data.org](https://www.football-data.org) | Optional live stats enrichment | Free registration |

Data flow on each refresh cycle:

```
worldcup26.ir  ──►  Teams, groups, matches, scores
       │
       ▼
TheSportsDB    ──►  Local kickoff times + live timelines
       │
       ▼
football-data  ──►  Live stats (only if API key set)
       │
       ▼
TournamentState  ──►  UI refresh (both panels)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Thread (GUI)                       │
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │   StandingsPanel     │  │      MatchCenterPanel        │ │
│  │   (12 groups, 2-col) │  │  Schedule / Live dashboard   │ │
│  └──────────┬───────────┘  └──────────────┬───────────────┘ │
│             │         TournamentState       │                 │
│             └──────────────┬────────────────┘                 │
└────────────────────────────┼────────────────────────────────┘
                             │ thread-safe snapshot / update
┌────────────────────────────┼────────────────────────────────┐
│              Background Thread (DataFetcher)                │
│                             │                               │
│                    create_data_client()                     │
│                   ┌─────────┴─────────┐                     │
│                   │  WorldCup26Client │                     │
│                   │  or MockClient    │                     │
│                   └───────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### Core components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| `Team`, `Group`, `Match` | `models/` | Domain objects for standings and fixtures |
| `TournamentState` | `data/tournament.py` | Thread-safe shared state |
| `DataFetcher` | `data/fetcher.py` | Background polling loop |
| `WorldCup26Client` | `data/worldcup26_client.py` | Primary API integration |
| `SportsDbEnricher` | `data/sportsdb_enricher.py` | Timezone + live event enrichment |
| `FlagCache` | `data/flag_cache.py` | Download and cache flag images |
| `StandingsPanel` | `ui/standings_panel.py` | Left panel UI |
| `MatchCenterPanel` | `ui/match_center_panel.py` | Right panel UI |
| `theme` | `ui/theme.py` | Font sizes and layout constants for 1080p |

---

## Project Structure

```
WC Disp/
├── main.py                  # Application entry point
├── config.py                # Environment variable loading
├── requirements.txt         # Python dependencies
├── .env.example             # Configuration template
│
├── models/
│   ├── team.py              # Team standings data
│   ├── group.py             # Group container + sorting
│   └── match.py             # Match, events, stats
│
├── data/
│   ├── api_client.py        # SportsDataClient interface + mock client
│   ├── worldcup26_client.py # Live API client
│   ├── sportsdb_enricher.py # TheSportsDB enrichment
│   ├── client_factory.py    # Client selection (live vs mock)
│   ├── fetcher.py           # Background data polling
│   ├── tournament.py        # Shared tournament state
│   ├── flag_cache.py        # Flag image cache
│   └── time_utils.py        # UTC → local time conversion
│
└── ui/
    ├── main_window.py       # Root window + layout
    ├── standings_panel.py   # Left panel
    ├── match_center_panel.py# Right panel
    ├── widgets.py           # Reusable UI components (StatBar)
    └── theme.py             # Typography and sizing
```

---

## Troubleshooting

**The window is too large for my screen**

The app is fixed to 1920×1080. Use a display at that resolution, or adjust `WINDOW_WIDTH` / `WINDOW_HEIGHT` in `ui/theme.py` and the corresponding `maxsize` call in `ui/main_window.py`.

**No data appears / connection errors**

- Check your internet connection.
- Verify [worldcup26.ir](https://worldcup26.ir/get/teams) is reachable in a browser.
- Try `USE_MOCK_DATA=1` to confirm the UI works independently of the API.

**Times look wrong**

Times should match your system clock's timezone. If they don't, ensure TheSportsDB is reachable — kickoff conversion depends on its UTC timestamps as a fallback when stadium-local parsing is insufficient.

**Flags not loading**

Flags are fetched from the network on first load. A firewall or proxy blocking `flagcdn.com` will prevent them from appearing; the app still works without flags.

**Live stats bars don't appear**

Detailed stats require a `FOOTBALL_DATA_API_KEY` in `.env` and an active live match. Goals, cards, and substitutions still appear in the event log via TheSportsDB without a key.

---

## License

This project is provided as-is for personal and educational use. Tournament data is sourced from third-party APIs; refer to each provider's terms of service for usage restrictions.
