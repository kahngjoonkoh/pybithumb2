from datetime import datetime

from pybithumb2.client import BithumbClient
from pybithumb2.models import Market, Snapshot
from pybithumb2.types import RawData
from pybithumb2.constants import CONNECTED_DATE_FORMAT


def test_get_snapshot(api_client: BithumbClient, raw_api_client: BithumbClient):
    market: Market = Market.from_string("KRW-BTC")
    response = api_client.get_snapshot(market)
    raw_response = raw_api_client.get_snapshot(market)

    assert len(response) > 0

    test_item: Snapshot = response[0]
    raw_test_item: RawData = raw_response[0]
    print(response.df())

    assert test_item.trade_date == datetime.strptime(raw_test_item["trade_date"], CONNECTED_DATE_FORMAT).date()
