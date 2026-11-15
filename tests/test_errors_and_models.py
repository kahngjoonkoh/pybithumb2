from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from pybithumb2 import *

BTC = MarketID.from_string("KRW-BTC")


# ##### errors #####


def test_error_body_with_2xx_status_raises(fake):
    fake.reply(
        {"error": {"name": "order_not_found", "message": "주문을 찾지 못했습니다."}}
    )
    with pytest.raises(APIError) as e:
        fake.client.cancel_order(OrderID("X"))
    assert e.value.name == e.value.code == "order_not_found"
    assert e.value.message == "주문을 찾지 못했습니다."


def test_http_error_keeps_status_and_bithumb_error(fake):
    fake.reply(
        {"error": {"name": "invalid_query_payload", "message": "bad"}}, status=401
    )
    with pytest.raises(APIError, match="invalid_query_payload: bad") as e:
        fake.client.get_accounts()
    assert e.value.status_code == 401
    assert e.value.response.status_code == 401


def test_non_json_http_error(fake):
    fake.reply("<html>502 Bad Gateway</html>", status=502)
    with pytest.raises(APIError) as e:
        fake.public.get_markets()
    assert e.value.status_code == 502
    assert "502" in e.value.name


def test_empty_response(fake):
    fake.reply("")
    with pytest.raises(APIError, match="Response is empty"):
        fake.public.get_markets()


def test_api_error_accepts_every_shape():
    assert APIError("invalid_jwt").name == "invalid_jwt"
    assert APIError('{"error": {"name": "n", "message": "m"}}').message == "m"
    assert APIError({"name": "n", "message": "m"}).name == "n"


# ##### arguments checked before sending #####


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.get_minute_candles(BTC, count=0),
        lambda c: c.get_day_candles(BTC, count=201),
        lambda c: c.get_week_candles(BTC, count=201),
        lambda c: c.get_month_candles(BTC, count=201),
        lambda c: c.get_trades(BTC, daysAgo=8),
        lambda c: c.get_notices(count=21),
        lambda c: c.get_order_info(),
        lambda c: c.get_order_info(OrderID("a"), client_order_id="b"),
        lambda c: c.get_orders(state=OrderState.WAIT, states=[OrderState.DONE]),
        lambda c: c.get_closed_orders(
            state=OrderState.DONE, states=[OrderState.CANCEL]
        ),
        lambda c: c.get_closed_orders(limit=1001),
        lambda c: c.get_pending_orders(limit=101),
        lambda c: c.cancel_order(),
        lambda c: c.cancel_orders(),
        lambda c: c.submit_twap_order(
            BTC,
            TradeSide.BID,
            duration=299,
            frequency=TwapFrequency.S15,
            price=Decimal(1),
        ),
        lambda c: c.get_deposits(limit=101),
    ],
)
def test_invalid_arguments_are_refused_before_sending(fake, call):
    with pytest.raises(APIError):
        call(fake.client)
    assert fake.transport.requests == []


@pytest.mark.parametrize(
    "kwargs, error",
    [
        (dict(order_type=OrderType.LIMIT, price=Decimal(1)), "need volume"),
        (dict(order_type=OrderType.LIMIT, volume=Decimal(1)), "need price"),
        (dict(order_type=OrderType.PRICE, volume=Decimal(1)), "need price"),
        (dict(order_type=OrderType.MARKET, price=Decimal(1)), "need volume"),
        (dict(order_type=OrderType.BEST, price=Decimal(1)), "need time_in_force"),
        (
            dict(order_type=OrderType.BEST, time_in_force=TimeInForce.POST_ONLY),
            "POST_ONLY",
        ),
        (
            dict(
                order_type=OrderType.MARKET,
                volume=Decimal(1),
                time_in_force=TimeInForce.IOC,
            ),
            "only applies",
        ),
        (
            dict(price=Decimal(1), volume=Decimal(1), client_order_id="has space"),
            "client_order_id",
        ),
        (
            dict(price=Decimal(1), volume=Decimal(1), client_order_id="x" * 37),
            "client_order_id",
        ),
    ],
)
def test_order_request_validation(kwargs, error):
    with pytest.raises(ValueError, match=error):
        OrderRequest(market=BTC, side=TradeSide.BID, **kwargs)


def test_valid_order_requests():
    OrderRequest(
        market=BTC,
        side=TradeSide.BID,
        order_type=OrderType.BEST,
        time_in_force=TimeInForce.FOK,
    )
    OrderRequest(
        market=BTC,
        side=TradeSide.ASK,
        price=Decimal(1),
        volume=Decimal(1),
        time_in_force=TimeInForce.POST_ONLY,
    )
    OrderRequest(
        market=BTC,
        side=TradeSide.BID,
        price=Decimal(1),
        volume=Decimal(1),
        client_order_id="A-z_09" * 6,
    )


def test_submit_order_validates_before_sending(fake):
    with pytest.raises(ValueError):
        fake.client.submit_order(BTC, TradeSide.BID, price=Decimal(1))
    assert fake.transport.requests == []


# ##### models #####


def test_missing_optional_fields_read_as_none():
    m = Market(market="KRW-BTC", korean_name="비트코인", english_name="Bitcoin")
    assert m.market_warning is None
    assert "market_warning" not in repr(m)


def test_v2_lower_case_side_parses():
    o = OrderCreated.model_validate(
        {
            "order_id": "1",
            "market": "KRW-BTC",
            "side": "ask",
            "order_type": "limit",
            "created_at": "2024-07-14T13:35:41+09:00",
        }
    )
    assert o.side == TradeSide.ASK
    assert o.market == BTC
    assert o.created_at == datetime(
        2024, 7, 14, 13, 35, 41, tzinfo=timezone(timedelta(hours=9))
    )


def test_market_orders_without_price_or_volume_parse():
    o = Order.model_validate(
        {
            "uuid": "1",
            "side": "bid",
            "ord_type": "price",
            "price": "10000",
            "volume": None,
            "state": "done",
            "market": "KRW-BTC",
            "created_at": "2024-07-14T13:35:41+09:00",
            "reserved_fee": "0",
            "remaining_fee": "0",
            "paid_fee": "4",
            "locked": "0",
            "executed_volume": "0.0001",
            "trades_count": 1,
        }
    )
    assert o.volume is None and o.price == Decimal("10000")


def test_parsed_values(fake):
    fake.example("GET /v1/withdraws/chance")
    chance = fake.client.get_withdraw_chance(Currency("BTC"), NetworkType("BTC"))
    assert chance.currency.code == Currency("BTC")
    assert chance.currency.withdraw_fee == Decimal("0.000108")
    assert chance.member_level.security_level is None
    assert chance.account.balance == Decimal("124.45282908")

    fake.example("GET /v2/orders/history")
    page = fake.client.get_closed_orders()
    assert page.has_next and page.next_key
    assert page.data[0].order_id == OrderID("C0101000007410714029")
    assert page.data.df().shape[0] == len(page.data)

    fake.example("POST /v2/orders/cancel")
    result = fake.client.cancel_orders(order_ids=[OrderID("C0101000007410713533")])
    assert result.fail[0].error.name == "order_not_found"


def test_batch_results_flag_failures():
    ok = BatchOrderResult(order_id=OrderID("1"), market=BTC)
    failed = BatchOrderResult(
        client_order_id="c", name="under_min_total_bid", message="too small"
    )
    assert ok.ok and not failed.ok


def test_week_candle_first_day_is_a_date(fake):
    fake.example("GET /v1/candles/weeks")
    candle = fake.public.get_week_candles(BTC)[0]
    assert isinstance(candle.first_day_of_period, date)
