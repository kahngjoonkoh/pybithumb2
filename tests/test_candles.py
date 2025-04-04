import pytest
from datetime import datetime
from decimal import Decimal

from pybithumb2.client import BithumbClient
from pybithumb2.utils import parse_datetime
from pybithumb2.models import (
    Currency,
    MinuteCandle,
    DayCandle,
    WeekCandle,
    MonthCandle,
    Market,
)
from pybithumb2.types import RawData
from pybithumb2.exceptions import APIError


def test_get_minute_candles(api_client: BithumbClient, raw_api_client: BithumbClient):
    now = datetime.now()
    market: Market = Market.from_string("KRW-BTC")
    response = api_client.get_minute_candles(market, to=now, count=10)
    raw_response = raw_api_client.get_minute_candles(market, to=now, count=10)

    assert len(response) > 0

    test_item: MinuteCandle = response[0]
    raw_test_item: RawData = raw_response[0]
    print(response.df())

    for key, value in raw_test_item.items():
        if key in ["candle_date_time_utc", "candle_date_time_kst"]:
            assert getattr(test_item, key) == parse_datetime(value)


def test_get_day_candles(api_client: BithumbClient):
    now = datetime.now()
    market: Market = Market.from_string("KRW-BTC")
    response = api_client.get_day_candles(market, to=now)

    assert len(response) > 0

    test_item: DayCandle = response[0]

    assert not hasattr(test_item, "converted_trade_price")
    with pytest.raises(AttributeError):
        getattr(test_item, "converted_trade_price")


def test_get_day_candles_with_converting_price_unit(
    api_client: BithumbClient
):
    now = datetime.now()
    market: Market = Market.from_string("BTC-ETH")
    response = api_client.get_day_candles(
        market, to=now, convertingPriceUnit=Currency("KRW")
    )

    assert len(response) > 0

    test_item: DayCandle = response[0]

    assert hasattr(test_item, "converted_trade_price")


def test_get_week_candles(api_client: BithumbClient, raw_api_client: BithumbClient):
    now = datetime.now()
    market: Market = Market.from_string("KRW-BTC")
    response = api_client.get_week_candles(market, to=now)
    raw_response = raw_api_client.get_week_candles(market, to=now)

    assert len(response) > 0

    test_item: WeekCandle = response[0]
    raw_test_item: RawData = raw_response[0]

    assert str(test_item.first_day_of_period) == raw_test_item["first_day_of_period"]


def test_get_week_candles(api_client: BithumbClient, raw_api_client: BithumbClient):
    now = datetime.now()
    market: Market = Market.from_string("KRW-BTC")
    response = api_client.get_month_candles(market, to=now)
    raw_response = raw_api_client.get_month_candles(market, to=now)

    assert len(response) > 0

    test_item: MonthCandle = response[0]
    raw_test_item: RawData = raw_response[0]

    assert str(test_item.first_day_of_period) == raw_test_item["first_day_of_period"]


def test_fails_get_candles(api_client: BithumbClient):
    market: Market = Market.from_string("KRW-BTC")
    with pytest.raises(APIError):
        api_client.get_minute_candles(market, count=-1)
    with pytest.raises(APIError):
        api_client.get_minute_candles(market, count=201)
