from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

WORLDCUP26_BASE_URL = os.getenv("WORLDCUP26_BASE_URL", "https://worldcup26.ir")
SPORTSDB_BASE_URL = os.getenv("SPORTSDB_BASE_URL", "https://www.thesportsdb.com/api/v1/json/3")
FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "").strip()
FOOTBALL_DATA_BASE_URL = os.getenv(
    "FOOTBALL_DATA_BASE_URL", "https://api.football-data.org/v4"
)

USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "0") == "1"
FETCH_INTERVAL_SECONDS = int(os.getenv("FETCH_INTERVAL_SECONDS", "60"))
