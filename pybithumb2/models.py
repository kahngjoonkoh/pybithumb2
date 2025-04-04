from datetime import datetime, date, time, timezone
from abc import ABC
import types
from typing import Any, List, cast, Type, TypeVar, Iterable, Generic, Dict, Optional, TYPE_CHECKING
from dataclasses import dataclass
from decimal import Decimal
from pydantic import BaseModel, field_validator

from pybithumb2.types import TradeSide, MarketWarning, WarningType
from pybithumb2.utils import parse_datetime, clean_and_format_data
from pybithumb2.constants import DATE_FORMAT, TIME_FORMAT


if TYPE_CHECKING:
    import pandas as pd


class DataFramable:
    def df(self) -> "pd.DataFrame":
        import pandas as pd

        return pd.DataFrame([clean_and_format_data(self.__dict__)])
    

T = TypeVar("T", bound="DataFramable")


class DFList(Generic[T], list[T]):
    def df(self) -> "pd.DataFrame":
        import pandas as pd

        return pd.concat([c.df() for c in self], ignore_index=True)


class FormattableBaseModel(BaseModel, DataFramable):
    def __init__(self, **data):
        super().__init__(**data)
        # Remove keys with None values from __dict__
        for key in list(self.__dict__.keys()):
            if self.__dict__[key] is None:
                del self.__dict__[key]

    @field_validator("*", mode="before")
    @classmethod
    def validate_field(cls, value, info):
        """Dynamically converts fields to their expected type."""
        expected_type = cls.model_fields[
            info.field_name
        ].annotation  # Get expected type

        if isinstance(value, str) and isinstance(expected_type, type):
            try:
                return expected_type(value)  # Convert to expected type
            except ValueError:
                pass  # If conversion fails, return original value

        return value

    def __repr__(self) -> str:
        field_strings = ", ".join(
            f"{name}={getattr(self, name)!r}" for name in self.__dict__
        )
        return f"{self.__class__.__name__}({field_strings})"

    def __str__(self) -> str:
        return self.__repr__()


@dataclass(frozen=True)
class Currency:
    code: str

    def __post_init__(self):
        object.__setattr__(self, "code", self.code.upper())

    def __str__(self) -> str:
        return self.code


class Market(FormattableBaseModel):
    currency_from: Currency
    currency_to: Currency

    @classmethod
    def from_string(cls, market_str: str) -> "Market":
        try:
            currency_from, currency_to = market_str.split("-")
            return cls(
                currency_from=Currency(code=currency_from),
                currency_to=Currency(code=currency_to),
            )
        except ValueError:
            raise ValueError(f"Invalid market format: {market_str}")

    def __str__(self) -> str:
        return f"{self.currency_from}-{self.currency_to}"


class MarketInfo(FormattableBaseModel):
    market: Market
    korean_name: str
    english_name: str
    market_warning: Optional[MarketWarning] = None

    @field_validator("market", mode="before", check_fields=False)
    def validate_market(cls, value):
        if isinstance(value, str):
            return Market.from_string(
                value
            )  # Convert "KRW-BTC" → Market(Currency("KRW"), Currency("BTC"))
        return value


class TimeUnit(FormattableBaseModel):
    minutes: int

    def __init__(self, minutes: int):
        if minutes not in [1, 3, 5, 10, 15, 30, 60, 240]:
            raise ValueError(
                f"Time Unit can only be one of 1, 3, 5, 10, 15, 30, 60, 240 minutes, not {minutes}"
            )
        super().__init__(minutes=minutes)

    def __str__(self) -> str:
        return str(self.minutes)


class Candle(FormattableBaseModel):
    market: Market
    candle_date_time_utc: datetime
    candle_date_time_kst: datetime
    opening_price: Decimal
    high_price: Decimal
    low_price: Decimal
    trade_price: Decimal
    timestamp: int
    candle_acc_trade_price: Decimal
    candle_acc_trade_volume: Decimal

    @field_validator("market", mode="before", check_fields=False)
    def validate_market(cls, value):
        if isinstance(value, str):
            return Market.from_string(value)
        return value

    @field_validator(
        "candle_date_time_utc",
        "candle_date_time_kst",
        mode="before",
        check_fields=False,
    )
    def validate_datetime(cls, value):
        if isinstance(value, str):
            return parse_datetime(value)
        return value


class MinuteCandle(Candle):
    unit: TimeUnit

    @field_validator("unit", mode="before", check_fields=False)
    def validate_timeunit(cls, value):
        if isinstance(value, int):
            return TimeUnit(value)
        return value


class DayCandle(Candle):
    prev_closing_price: Decimal
    change_price: Decimal
    change_rate: Decimal
    converted_trade_price: Optional[Decimal] = None


class WeekCandle(Candle):
    first_day_of_period: date

    @field_validator("first_day_of_period", mode="before", check_fields=False)
    def validate_date(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, DATE_FORMAT).date()
        return value


class MonthCandle(Candle):
    first_day_of_period: date

    @field_validator("first_day_of_period", mode="before", check_fields=False)
    def validate_date(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, DATE_FORMAT).date()
        return value


class TradeInfo(FormattableBaseModel):
    market: Market
    trade_date_utc: date
    trade_time_utc: time
    timestamp: int
    trade_price: Decimal
    trade_volume: Decimal
    prev_closing_price: Decimal
    change_price: Decimal
    ask_bid: TradeSide
    sequential_id: Optional[int] = None

    @field_validator("market", mode="before", check_fields=False)
    def validate_market(cls, value):
        if isinstance(value, str):
            return Market.from_string(value)
        return value
    
    @field_validator("trade_date_utc", mode="before", check_fields=False)
    def validate_date(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, DATE_FORMAT).date()
        return value
    
    @field_validator("trade_time_utc", mode="before", check_fields=False)
    def validate_time(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, TIME_FORMAT).time()
        return value


class WarningMarketInfo(FormattableBaseModel):
    market: Market
    warning_type: WarningType
    end_date: datetime  # KST

    @field_validator("market", mode="before", check_fields=False)
    def validate_market(cls, value):
        if isinstance(value, str):
            return Market.from_string(value)
        return value

    @field_validator("end_date", mode="before", check_fields=False)
    def validate_datetime(cls, value):
        if isinstance(value, str):
            return parse_datetime(value)
        return value


class Account(FormattableBaseModel):
    currency: Currency
    balance: Decimal
    locked: Decimal
    avg_buy_price: Decimal
    avg_buy_price_modified: bool
    unit_currency: Currency
