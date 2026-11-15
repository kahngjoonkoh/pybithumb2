"""
Every endpoint: the request it makes, and that the API reference's example response parses
into the right model (and comes back untouched with use_raw_data=True).
"""

from datetime import datetime
from decimal import Decimal

import pytest

from pybithumb2 import *
from tests.conftest import EXAMPLES

BTC = MarketID.from_string("KRW-BTC")
BTC_C = Currency("BTC")
BTC_NET = NetworkType("BTC")

# (method, kwargs, endpoint, expected query or JSON body, result type, item type if a list)
CASES = [
    # public
    ("get_markets", {}, "GET /v1/market/all", "isDetails=false", list, Market),
    (
        "get_minute_candles",
        dict(market=BTC, count=2, unit=TimeUnit(5)),
        "GET /v1/candles/minutes/{unit}",
        "market=KRW-BTC&count=2",
        DFList,
        MinuteCandle,
    ),
    (
        "get_day_candles",
        dict(market=BTC, convertingPriceUnit=Currency("KRW")),
        "GET /v1/candles/days",
        "market=KRW-BTC&count=1&convertingPriceUnit=KRW",
        DFList,
        DayCandle,
    ),
    (
        "get_week_candles",
        dict(market=BTC),
        "GET /v1/candles/weeks",
        "market=KRW-BTC&count=1",
        DFList,
        WeekCandle,
    ),
    (
        "get_month_candles",
        dict(market=BTC),
        "GET /v1/candles/months",
        "market=KRW-BTC&count=1",
        DFList,
        MonthCandle,
    ),
    (
        "get_trades",
        dict(market=BTC, count=5, cursor=123, daysAgo=2),
        "GET /v1/trades/ticks",
        "market=KRW-BTC&count=5&cursor=123&daysAgo=2",
        DFList,
        TradeInfo,
    ),
    (
        "get_snapshots",
        dict(markets=[BTC]),
        "GET /v1/ticker",
        "markets=KRW-BTC",
        DFList,
        Snapshot,
    ),
    (
        "get_orderbooks",
        dict(markets=[BTC]),
        "GET /v1/orderbook",
        "markets=KRW-BTC",
        list,
        OrderBook,
    ),
    (
        "get_warning_markets",
        {},
        "GET /v1/market/virtual_asset_warning",
        "",
        list,
        WarningMarketInfo,
    ),
    ("get_notices", dict(count=3), "GET /v1/notices", "count=3", DFList, Notice),
    (
        "get_fees",
        dict(currency=BTC_C),
        "GET /v2/fee/inout/{currency}",
        "",
        DFList,
        CurrencyFee,
    ),
    # account
    ("get_accounts", {}, "GET /v1/accounts", "", list, Account),
    (
        "get_order_available",
        dict(market=BTC),
        "GET /v1/orders/chance",
        "market=KRW-BTC",
        OrderAvailable,
        None,
    ),
    ("get_wallet_status", {}, "GET /v1/status/wallet", "", DFList, WalletStatus),
    ("get_api_keys", {}, "GET /v1/api_keys", "", DFList, APIKeyInfo),
    # orders
    (
        "get_order_info",
        dict(uuid=OrderID("C0101000000001799231")),
        "GET /v1/order",
        "uuid=C0101000000001799231",
        OrderInfo,
        None,
    ),
    (
        "get_orders",
        dict(market=BTC, state=OrderState.DONE),
        "GET /v1/orders",
        "market=KRW-BTC&state=done&page=1&limit=100&order_by=desc",
        DFList,
        Order,
    ),
    (
        "submit_order",
        dict(
            market=BTC,
            side=TradeSide.ASK,
            volume=Decimal("0.5"),
            ord_type=OrderType.MARKET,
        ),
        "POST /v2/orders",
        {"market": "KRW-BTC", "side": "ask", "order_type": "market", "volume": "0.5"},
        OrderCreated,
        None,
    ),
    (
        "submit_orders",
        dict(
            orders=[
                OrderRequest(
                    market=BTC,
                    side=TradeSide.BID,
                    order_type=OrderType.PRICE,
                    price=Decimal("10000"),
                )
            ]
        ),
        "POST /v2/orders/batch",
        {
            "batch_orders": [
                {
                    "market": "KRW-BTC",
                    "side": "bid",
                    "order_type": "price",
                    "price": "10000",
                }
            ]
        },
        DFList,
        BatchOrderResult,
    ),
    (
        "cancel_order",
        dict(client_order_id="my-1"),
        "DELETE /v2/order",
        "client_order_id=my-1",
        OrderCancelled,
        None,
    ),
    (
        "cancel_orders",
        dict(client_order_ids=["a", "b"]),
        "POST /v2/orders/cancel",
        {"client_order_ids": ["a", "b"]},
        BatchCancelResult,
        None,
    ),
    (
        "search_orders",
        dict(market=BTC, order_ids=[OrderID("X")]),
        "POST /v2/orders/search",
        {"market": "KRW-BTC", "order_ids": ["X"], "order_by": "desc"},
        DFList,
        OrderV2,
    ),
    (
        "get_pending_orders",
        dict(market=BTC, next_key="k1"),
        "GET /v2/orders/pending",
        "market=KRW-BTC&state=wait&limit=100&order_by=desc&next_key=k1",
        OrderPage,
        None,
    ),
    (
        "get_closed_orders",
        dict(states=[OrderState.DONE, OrderState.CANCEL], limit=500),
        "GET /v2/orders/history",
        "states[]=done&states[]=cancel&limit=500&order_by=desc",
        OrderPage,
        None,
    ),
    # TWAP
    (
        "submit_twap_order",
        dict(
            market=BTC,
            side=TradeSide.BID,
            duration=600,
            frequency=TwapFrequency.S30,
            price=Decimal("100000"),
        ),
        "POST /v1/twap",
        {
            "market": "KRW-BTC",
            "side": "bid",
            "price": "100000",
            "duration": "600",
            "frequency": "30",
        },
        TwapOrderID,
        None,
    ),
    (
        "get_twap_orders",
        dict(market=BTC, state="progress"),
        "GET /v1/twap",
        "market=KRW-BTC&state=progress&limit=100&order_by=desc",
        TwapOrderPage,
        None,
    ),
    (
        "cancel_twap_order",
        dict(algo_order_id="T-1"),
        "DELETE /v1/twap",
        "algo_order_id=T-1",
        TwapOrderID,
        None,
    ),
    # deposits
    (
        "get_deposit",
        dict(currency=BTC_C, uuid="200012694"),
        "GET /v1/deposit",
        "currency=BTC&uuid=200012694",
        Transfer,
        None,
    ),
    (
        "get_deposits",
        dict(currency=BTC_C, txids=["t1"]),
        "GET /v1/deposits",
        "currency=BTC&txids[]=t1&page=1&limit=100&order_by=desc",
        DFList,
        Transfer,
    ),
    (
        "get_krw_deposits",
        dict(state="ACCEPTED"),
        "GET /v1/deposits/krw",
        "state=ACCEPTED&page=1&limit=100&order_by=desc",
        DFList,
        Transfer,
    ),
    (
        "deposit_krw",
        dict(amount=Decimal("10000")),
        "POST /v1/deposits/krw",
        {"amount": "10000", "two_factor_type": "kakao"},
        Transfer,
        None,
    ),
    (
        "generate_deposit_address",
        dict(currency=BTC_C, net_type=BTC_NET),
        "POST /v1/deposits/generate_coin_address",
        {"currency": "BTC", "net_type": "BTC"},
        CoinAddress,
        None,
    ),
    (
        "get_deposit_address",
        dict(currency=BTC_C, net_type=BTC_NET),
        "GET /v1/deposits/coin_address",
        "currency=BTC&net_type=BTC",
        CoinAddress,
        None,
    ),
    (
        "get_deposit_addresses",
        {},
        "GET /v1/deposits/coin_addresses",
        "",
        DFList,
        CoinAddress,
    ),
    # withdrawals
    (
        "get_withdraw_chance",
        dict(currency=BTC_C, net_type=BTC_NET),
        "GET /v1/withdraws/chance",
        "currency=BTC&net_type=BTC",
        WithdrawChance,
        None,
    ),
    (
        "get_withdrawal",
        dict(currency=BTC_C, txid="tx"),
        "GET /v1/withdraw",
        "currency=BTC&txid=tx",
        Transfer,
        None,
    ),
    (
        "get_withdrawals",
        dict(uuids=["1", "2"], limit=50),
        "GET /v1/withdraws",
        "uuids[]=1&uuids[]=2&page=1&limit=50&order_by=desc",
        DFList,
        Transfer,
    ),
    (
        "get_krw_withdrawals",
        dict(),
        "GET /v1/withdraws/krw",
        "page=1&limit=100&order_by=desc",
        DFList,
        Transfer,
    ),
    (
        "withdraw_coin",
        dict(
            currency=BTC_C,
            net_type=BTC_NET,
            amount=Decimal("0.01"),
            address="bc1q",
            receiver_type=ReceiverType.PERSONAL,
            receiver_ko_name="홍길동",
        ),
        "POST /v1/withdraws/coin",
        {
            "currency": "BTC",
            "net_type": "BTC",
            "amount": "0.01",
            "address": "bc1q",
            "receiver_type": "personal",
            "receiver_ko_name": "홍길동",
        },
        Transfer,
        None,
    ),
    (
        "withdraw_krw",
        dict(amount=Decimal("5000")),
        "POST /v1/withdraws/krw",
        {"amount": "5000", "two_factor_type": "kakao"},
        Transfer,
        None,
    ),
    (
        "cancel_withdrawal",
        dict(withdrawal_id="200377211"),
        "DELETE /v1/withdraws/coin",
        "withdrawal_id=200377211",
        WithdrawalCancelled,
        None,
    ),
    (
        "get_withdraw_addresses",
        {},
        "GET /v1/withdraws/coin_addresses",
        "",
        DFList,
        WithdrawAddress,
    ),
]

PATH_ARGS = {"{unit}": "5", "{currency}": "BTC"}


def _path(endpoint: str) -> str:
    path = endpoint.split(" ", 1)[1]
    for k, v in PATH_ARGS.items():
        path = path.replace(k, v)
    return path


def test_every_documented_endpoint_is_covered():
    documented = {k for k in EXAMPLES if not k.startswith("_")}
    assert {c[2] for c in CASES} == documented


@pytest.mark.parametrize(
    "method,kwargs,endpoint,sent,result_type,item_type",
    CASES,
    ids=[c[0] for c in CASES],
)
def test_endpoint(fake, method, kwargs, endpoint, sent, result_type, item_type):
    fake.example(endpoint)
    result = getattr(fake.client, method)(**kwargs)

    verb = endpoint.split(" ")[0]
    assert fake.last.method == verb
    assert fake.path == _path(endpoint)
    if isinstance(sent, dict):
        assert fake.body == sent
    else:
        assert fake.query == sent

    assert isinstance(result, result_type)
    if item_type is not None:
        assert len(result) > 0 and all(isinstance(r, item_type) for r in result)
        result[0].df()  # every model renders as a DataFrame row
    else:
        result.df()


@pytest.mark.parametrize(
    "method,kwargs,endpoint", [c[:3] for c in CASES], ids=[c[0] for c in CASES]
)
def test_endpoint_raw(fake, method, kwargs, endpoint):
    fake.example(endpoint)
    assert getattr(fake.raw, method)(**kwargs) == EXAMPLES[endpoint]
