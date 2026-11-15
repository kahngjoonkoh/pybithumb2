"""What goes on the wire: paths, query strings, JSON bodies and JWT signatures."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from pybithumb2 import (
    APIError,
    BithumbClient,
    MarketID,
    OrderID,
    OrderRequest,
    OrderState,
    OrderType,
    TimeInForce,
    TradeSide,
)

BTC = MarketID.from_string("KRW-BTC")


def test_public_request_is_not_signed(fake):
    fake.example("GET /v1/market/all")
    fake.public.get_markets(isDetails=True)
    assert fake.path == "/v1/market/all"
    assert (
        fake.raw_query == "isDetails=true"
    )  # lower-case JSON boolean, not Python's True
    assert "Authorization" not in fake.last.headers


def test_private_request_without_keys_is_refused_before_sending(fake):
    with pytest.raises(APIError, match="invalid_jwt"):
        fake.public.get_accounts()
    assert fake.transport.requests == []


def test_private_get_without_params_has_no_query_hash(fake):
    fake.example("GET /v1/accounts")
    fake.client.get_accounts()
    claims = fake.claims()
    assert claims["access_key"] == "test-access-key"
    assert "query_hash" not in claims
    assert len(str(claims["timestamp"])) == 13  # milliseconds


def test_private_get_signs_the_unencoded_query(fake):
    fake.example("GET /v1/orders")
    fake.client.get_orders(
        market=BTC,
        uuids=[OrderID("a-1"), OrderID("b 2")],
        states=[OrderState.WAIT, OrderState.WATCH],
        limit=10,
    )
    # arrays go out as key[]=value, percent-encoded on the URL...
    assert fake.raw_query == (
        "market=KRW-BTC&uuids%5B%5D=a-1&uuids%5B%5D=b%202&states%5B%5D=wait&states%5B%5D=watch"
        "&page=1&limit=10&order_by=desc"
    )
    # ...while the hash is over the unencoded form
    fake.assert_signed(
        "market=KRW-BTC&uuids[]=a-1&uuids[]=b 2&states[]=wait&states[]=watch"
        "&page=1&limit=10&order_by=desc"
    )


def test_delete_sends_params_in_the_query(fake):
    fake.example("DELETE /v2/order")
    fake.client.cancel_order(OrderID("C0101000000001799653"))
    assert fake.last.method == "DELETE"
    assert fake.path == "/v2/order"
    assert fake.query == "order_id=C0101000000001799653"
    assert fake.last.body is None
    fake.assert_signed("order_id=C0101000000001799653")


def test_post_sends_json_and_signs_the_body(fake):
    fake.example("POST /v2/orders")
    fake.client.submit_order(
        BTC,
        TradeSide.BID,
        volume=Decimal("0.0001"),
        price=Decimal("1E+8"),  # exponent form must not reach the API
        ord_type=OrderType.LIMIT,
        client_order_id="my-order_1",
        time_in_force=TimeInForce.IOC,
    )
    assert fake.last.method == "POST"
    assert fake.path == "/v2/orders"
    assert fake.last.headers["Content-Type"] == "application/json"
    assert fake.body == {
        "market": "KRW-BTC",
        "side": "bid",
        "order_type": "limit",
        "price": "100000000",
        "volume": "0.0001",
        "client_order_id": "my-order_1",
        "time_in_force": "ioc",
    }
    fake.assert_signed(
        "market=KRW-BTC&side=bid&order_type=limit&price=100000000&volume=0.0001"
        "&client_order_id=my-order_1&time_in_force=ioc"
    )


def test_batch_order_body_is_signed_with_indexed_keys(fake):
    fake.example("POST /v2/orders/batch")
    fake.client.submit_orders(
        [
            OrderRequest(
                market=BTC,
                side=TradeSide.BID,
                price=Decimal("50000000"),
                volume=Decimal("0.001"),
            ),
            OrderRequest(
                market=BTC,
                side=TradeSide.ASK,
                order_type=OrderType.MARKET,
                volume=Decimal("0.002"),
            ),
        ]
    )
    assert fake.body == {
        "batch_orders": [
            {
                "market": "KRW-BTC",
                "side": "bid",
                "order_type": "limit",
                "price": "50000000",
                "volume": "0.001",
            },
            {
                "market": "KRW-BTC",
                "side": "ask",
                "order_type": "market",
                "volume": "0.002",
            },
        ]
    }
    fake.assert_signed(
        "batch_orders[0][market]=KRW-BTC&batch_orders[0][side]=bid&batch_orders[0][order_type]=limit"
        "&batch_orders[0][price]=50000000&batch_orders[0][volume]=0.001"
        "&batch_orders[1][market]=KRW-BTC&batch_orders[1][side]=ask&batch_orders[1][order_type]=market"
        "&batch_orders[1][volume]=0.002"
    )


def test_batch_cancel_body_uses_array_keys(fake):
    fake.example("POST /v2/orders/cancel")
    fake.client.cancel_orders(order_ids=[OrderID("A"), OrderID("B")])
    assert fake.body == {"order_ids": ["A", "B"]}
    fake.assert_signed("order_ids[]=A&order_ids[]=B")


def test_datetimes_are_sent_in_kst(fake):
    fake.example("GET /v1/candles/days")
    utc_noon = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    fake.public.get_day_candles(BTC, to=utc_noon, count=2)
    assert fake.query == "market=KRW-BTC&to=2025-01-01 21:00:00&count=2"

    fake.example("GET /v1/candles/days")
    fake.public.get_day_candles(BTC, to=datetime(2025, 1, 1, 9, 30))  # naive = KST
    assert fake.query == "market=KRW-BTC&to=2025-01-01 09:30:00&count=1"


def test_order_history_times_are_unix_milliseconds(fake):
    fake.example("GET /v2/orders/history")
    kst = timezone(timedelta(hours=9))
    fake.client.get_closed_orders(
        start_time=datetime(2026, 4, 6, tzinfo=kst), end_time=1775487600000
    )
    assert (
        fake.query
        == "start_time=1775401200000&end_time=1775487600000&limit=100&order_by=desc"
    )


def test_markets_are_comma_separated(fake):
    fake.example("GET /v1/ticker")
    fake.public.get_snapshots([BTC, MarketID.from_string("KRW-ETH")])
    assert fake.query == "markets=KRW-BTC,KRW-ETH"


def test_notices_come_from_the_feed_host(fake):
    fake.example("GET /v1/notices")
    fake.public.get_notices(count=2)
    assert fake.last.url == "https://feed-api.bithumb.com/v1/notices?count=2"


def test_redirects_are_not_followed(fake):
    fake.reply("<html>302 Found</html>", status=302)
    fake.transport.next_headers = {"location": "https://elsewhere.example/v1/accounts"}
    with pytest.raises(APIError, match="redirect.*elsewhere.example"):
        fake.client.get_accounts()
    assert len(fake.transport.requests) == 1


def test_user_agent_is_sent(fake):
    fake.example("GET /v1/market/all")
    fake.public.get_markets()
    assert fake.last.headers["User-Agent"].startswith("pybithumb2/")
