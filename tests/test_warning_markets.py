from pybithumb2.client import BithumbClient
from pybithumb2.types import RawData


def test_get_warning_markets(api_client: BithumbClient, raw_api_client: BithumbClient):
    response = api_client.get_warning_markets()
    raw_response = raw_api_client.get_warning_markets()

    assert len(response) == len(raw_response)
    assert len(response) > 0

    test_item = response[0]
    raw_test_item: RawData = raw_response[0]

    for key, value in raw_test_item.items():
        assert str(getattr(test_item, key)) == str(
            value
        ), f"Mismatch for {key}: expected {value}, got {getattr(test_item, key)}"
