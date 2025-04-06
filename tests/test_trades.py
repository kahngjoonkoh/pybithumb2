from datetime import datetime

from pybithumb2.client import BithumbClient
from pybithumb2.models import MarketID, TradeInfo
from pybithumb2.types import RawData


def test_get_trades(api_client: BithumbClient, raw_api_client: BithumbClient):
    now = datetime.now().time()
    market: MarketID = MarketID.from_string("KRW-BTC")
    response = api_client.get_trades(market, to=now, count=10)
    raw_response = raw_api_client.get_trades(market, to=now, count=10)

    assert len(response) > 0

    test_item: TradeInfo = response[0]
    raw_test_item: RawData = raw_response[0]
    print(response.df())

    assert str(test_item.ask_bid) == raw_test_item["ask_bid"]
