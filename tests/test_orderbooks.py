from decimal import Decimal

from pybithumb2.client import BithumbClient
from pybithumb2.models import Market, OrderBook
from pybithumb2.types import RawData


def test_get_orderbooks(api_client: BithumbClient,):
    markets: Market = [Market.from_string("KRW-BTC"), Market.from_string("KRW-ETH")]
    response = api_client.get_orderbooks(markets)

    assert len(response) > 0

    test_item: OrderBook = response[0]
    print(test_item.orderbook_units.df())

    assert len(test_item.orderbook_units) == 15


def test_get_orderbooks_single(api_client: BithumbClient):
    markets: Market = [Market.from_string("KRW-BTC")]
    response = api_client.get_orderbooks(markets)

    assert len(response) > 0

    test_item: OrderBook = response[0]
    print(test_item.orderbook_units.df())

    assert len(test_item.orderbook_units) == 30
