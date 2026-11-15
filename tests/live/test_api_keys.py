import pytest

from pybithumb2.client import BithumbClient
from pybithumb2.models import APIKeyInfo
from pybithumb2.types import RawData


def test_get_api_keys(api_client: BithumbClient, raw_api_client: BithumbClient):
    response = api_client.get_api_keys()
    raw_response = raw_api_client.get_api_keys()

    assert len(response) > 0

    test_item: APIKeyInfo = response[0]
    raw_test_item: RawData = raw_response[0]
    print(response.df())

    assert str(test_item.access_key) == raw_test_item["access_key"]
