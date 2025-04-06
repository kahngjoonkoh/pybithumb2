import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))
from pybithumb2.client import BithumbClient

load_dotenv()
API_KEY = os.getenv("API_KEY_ID")
API_SECRET = os.getenv("API_SECRET_KEY")

if not API_KEY or not API_SECRET:
    raise ValueError("Missing API credentials. Check your .env file.")


@pytest.fixture(scope="session")
def api_client():
    client = BithumbClient(API_KEY, API_SECRET)
    yield client


@pytest.fixture(scope="session")
def raw_api_client():
    client = BithumbClient(API_KEY, API_SECRET, use_raw_data=True)
    yield client
