import pytest
import time

from typing import List
from decimal import Decimal

from pybithumb2.client import BithumbClient
from pybithumb2.models import MarketID, Order, OrderAvailable, Snapshot, OrderInfo
from pybithumb2.types import OrderID, TradeSide, OrderType, OrderState


@pytest.fixture(scope="module")
def market_id():
    yield MarketID.from_string("KRW-SUI")


@pytest.fixture(scope="module")
def order_id(market_id: MarketID, api_client: BithumbClient):
    snapshot: Snapshot = api_client.get_snapshots([market_id])[0]

    test_price = round(
        snapshot.trade_price * Decimal(0.2)
    )  # minimum bid price is 10% of current price.

    order: Order = api_client.submit_order(
        market_id,
        TradeSide.BID,
        price=test_price,
        volume=6000
        / test_price,  # 6000 KRW so that it exceeds the minimum order 5000 KRW even with slight fluctuations.
        ord_type=OrderType.LIMIT,
    )

    time.sleep(0.5)  # time to process and reflect the order in their system

    assert isinstance(order.uuid, OrderID)

    yield order.uuid
    # TODO: the test for cancel_order is slightly buggy. I think it may be a problem with the server data updates?
    api_client.cancel_order(order.uuid)
    response: OrderInfo = api_client.get_orders(
        market_id, [order.uuid], state=OrderState.CANCEL
    )[0]

    assert response.uuid == order.uuid


def test_get_order_available(
    market_id: MarketID, api_client: BithumbClient, raw_api_client: BithumbClient
):
    response: OrderAvailable = api_client.get_order_available(market_id)
    raw_response = raw_api_client.get_order_available(market_id)

    assert str(response.ask_account.currency) == raw_response["ask_account"]["currency"]
    assert str(response.market.order_types[0]) == str(
        raw_response["market"]["order_types"][0]
    )


def test_get_order_info(
    order_id: OrderID, api_client: BithumbClient, raw_api_client: BithumbClient
):
    response = api_client.get_order_info(order_id)
    raw_response = raw_api_client.get_order_info(order_id)

    assert len(response) > 0

    test_item = response[0]
    raw_test_item = raw_response[0]

    assert str(test_item.uuid) == raw_test_item["uuid"]
    assert test_item.state == OrderState.WAIT
    assert test_item.ord_type == OrderType.LIMIT


def test_get_orders(
    market_id: MarketID,
    order_id: OrderID,
    api_client: BithumbClient,
    raw_api_client: BithumbClient,
):
    uuids = [order_id]
    response = api_client.get_orders(market_id, uuids)
    raw_response = raw_api_client.get_orders(market_id, uuids)

    assert len(response) > 0

    test_item: Order = response[0]
    raw_test_item = raw_response[0]

    assert str(test_item.uuid) == raw_test_item["uuid"]
    assert test_item.state == OrderState.WAIT
    assert test_item.ord_type == OrderType.LIMIT
