from __future__ import annotations

import logging

from config import FOOTBALL_DATA_API_KEY, USE_MOCK_DATA
from data.api_client import MockSportsDataClient, SportsDataClient
from data.worldcup26_client import WorldCup26Client

logger = logging.getLogger(__name__)


def create_data_client() -> SportsDataClient:
    if USE_MOCK_DATA:
        logger.info("Using mock tournament data")
        return MockSportsDataClient()

    logger.info("Using World Cup 2026 API (worldcup26.ir)")
    if FOOTBALL_DATA_API_KEY:
        logger.info("football-data.org key detected — live stats enrichment enabled")
    return WorldCup26Client()
