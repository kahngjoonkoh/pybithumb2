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


@pytest.fixture(scope="session")
def api_client():
    client = BithumbClient(API_KEY, API_SECRET)
    yield client


@pytest.fixture(scope="session")
def raw_api_client():
    client = BithumbClient(API_KEY, API_SECRET, use_raw_data=True)
    yield client
