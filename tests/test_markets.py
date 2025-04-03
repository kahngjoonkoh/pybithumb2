import pytest

from pybithumb2.client import BithumbClient


def test_get_markets(api_client: BithumbClient, raw_api_client: BithumbClient):
    response = api_client.get_markets()
    raw_response = raw_api_client.get_markets()

    assert len(response) == len(raw_response)
    assert len(response) > 0

    test_item = response[0]
    raw_test_item = raw_response[0]

    assert str(test_item.market) == raw_test_item["market"]
    assert not hasattr(test_item, "market_warning")
    with pytest.raises(AttributeError):
        getattr(test_item, "market_warning")


def test_get_markets_with_details(
    api_client: BithumbClient, raw_api_client: BithumbClient
):
    response = api_client.get_markets(isDetails=True)
    raw_response = raw_api_client.get_markets(isDetails=True)

    assert len(response) == len(raw_response)
    assert len(response) > 0

    test_item = response[0]
    raw_test_item = raw_response[0]

    assert hasattr(test_item, "market_warning")
    assert str(test_item.market_warning) == raw_test_item["market_warning"]
