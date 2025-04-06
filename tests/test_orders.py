from pybithumb2.client import BithumbClient
from pybithumb2.models import MarketID, Order
from pybithumb2.types import OrderID


def test_get_orders(api_client: BithumbClient, raw_api_client: BithumbClient):
    market: MarketID = MarketID.from_string("KRW-SUI")
    uuids = [
        OrderID("C0745000000190648868"),
        OrderID("C0745000000190648815")
    ]
    response = api_client.get_orders(market, uuids)
    raw_response = raw_api_client.get_orders(market, uuids)

    assert len(response) > 0

    test_item: Order = response[0]
    raw_test_item = raw_response[0]

    assert  str(test_item.uuid) == raw_test_item["uuid"]
