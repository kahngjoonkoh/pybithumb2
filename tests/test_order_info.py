from pybithumb2.client import BithumbClient
from pybithumb2.models import MarketID, OrderInfo


def test_get_order_info(api_client: BithumbClient, raw_api_client: BithumbClient):
    response = api_client.get_order_info()
    raw_response = raw_api_client.get_order_info()

    assert len(response) > 0

    test_item = response[0]
    raw_test_item = raw_response[0]

    assert  str(test_item.uuid) == raw_test_item["uuid"]
