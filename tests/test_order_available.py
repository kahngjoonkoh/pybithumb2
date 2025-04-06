from pybithumb2.client import BithumbClient
from pybithumb2.models import MarketID, OrderAvailable


def test_get_order_available(api_client: BithumbClient, raw_api_client: BithumbClient):
    market: MarketID = MarketID.from_string("KRW-BTC")
    response: OrderAvailable = api_client.get_order_available(market)
    raw_response = raw_api_client.get_order_available(market)

    assert str(response.ask_account.currency) == raw_response["ask_account"]["currency"]
    assert str(response.market.order_types[0]) == str(raw_response["market"]["order_types"][0])
