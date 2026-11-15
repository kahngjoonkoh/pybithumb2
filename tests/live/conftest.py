"""
Tests in this folder call the real Bithumb API with your keys (API_KEY_ID and API_SECRET_KEY,
from the environment or a .env file). They are skipped when the keys are missing.

test_orders.py places and cancels a real limit order far below the market; it only runs when
PYBITHUMB2_LIVE_ORDERS=1 is also set.
"""

import os
import pytest
from dotenv import load_dotenv

from pybithumb2.client import BithumbClient

load_dotenv()
API_KEY = os.getenv("API_KEY_ID")
API_SECRET = os.getenv("API_SECRET_KEY")


def pytest_collection_modifyitems(config, items):
    if API_KEY and API_SECRET:
        return
    skip = pytest.mark.skip(
        reason="live test: set API_KEY_ID and API_SECRET_KEY to run"
    )
    for item in items:
        if "tests/live" in str(item.fspath).replace(os.sep, "/"):
            item.add_marker(skip)


@pytest.fixture(scope="session")
def api_client():
    yield BithumbClient(API_KEY, API_SECRET)


@pytest.fixture(scope="session")
def raw_api_client():
    yield BithumbClient(API_KEY, API_SECRET, use_raw_data=True)
