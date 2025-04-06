from datetime import datetime, date, time
from typing import (
    TypeVar,
    Generic,
    Optional,
    List,
    TYPE_CHECKING,
)
from dataclasses import dataclass
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator

from pybithumb2.types import (
    Currency,
    ChangeType,
    TradeSide,
    MarketWarning,
    WarningType,
    OrderID,
    OrderType,
    OrderState,
    MarketState,
    WalletState,
    BlockState,
    NetworkType
)
from pybithumb2.utils import parse_datetime, clean_and_format_data
from pybithumb2.constants import (
    DATE_FORMAT,
    TIME_FORMAT,
    CONNECTED_DATE_FORMAT,
    CONNECTED_TIME_FORMAT,
)


if TYPE_CHECKING:
    import pandas as pd


class DataFramable:
    def df(self) -> "pd.DataFrame":
        import pandas as pd

        return pd.DataFrame([clean_and_format_data(self.__dict__)])


T = TypeVar("T", bound="DataFramable")


class DFList(Generic[T], List[T]):
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



class MarketID(FormattableBaseModel):
    currency_from: Currency
    currency_to: Currency

    @classmethod
    def from_string(cls, market_str: str) -> "MarketID":
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


class Market(FormattableBaseModel):
    market: MarketID
    korean_name: str
    english_name: str
    market_warning: Optional[MarketWarning] = None

    @field_validator("market", mode="before", check_fields=False)
    def validate_market(cls, value):
        if isinstance(value, str):
            return MarketID.from_string(
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
    market: MarketID
    candle_date_time_utc: datetime
    candle_date_time_kst: datetime
    opening_price: Decimal = Field(default_factory=lambda: Decimal(0))
    high_price: Decimal = Field(default_factory=lambda: Decimal(0))
    low_price: Decimal = Field(default_factory=lambda: Decimal(0))
    trade_price: Decimal = Field(default_factory=lambda: Decimal(0))
    timestamp: int = 0
    candle_acc_trade_price: Decimal = Field(default_factory=lambda: Decimal(0))
    candle_acc_trade_volume: Decimal = Field(default_factory=lambda: Decimal(0))

    @field_validator("market", mode="before", check_fields=False)
    def validate_market(cls, value):
        if isinstance(value, str):
            return MarketID.from_string(value)
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
    prev_closing_price: Decimal = Field(default_factory=lambda: Decimal(0))
    change_price: Decimal = Field(default_factory=lambda: Decimal(0))
    change_rate: Decimal = Field(default_factory=lambda: Decimal(0))
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
    market: MarketID
    trade_date_utc: date
    trade_time_utc: time
    timestamp: int = 0
    trade_price: Decimal = Field(default_factory=lambda: Decimal(0))
    trade_volume: Decimal = Field(default_factory=lambda: Decimal(0))
    prev_closing_price: Decimal = Field(default_factory=lambda: Decimal(0))
    change_price: Decimal = Field(default_factory=lambda: Decimal(0))
    ask_bid: TradeSide
    sequential_id: Optional[int] = None

    @field_validator("market", mode="before", check_fields=False)
    def validate_market(cls, value):
        if isinstance(value, str):
            return MarketID.from_string(value)
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


"""*위 응답의 change, change_price, change_rate, signed_change_price, signed_change_rate 필드는 전일종가의 대비 값입니다."""


class Snapshot(FormattableBaseModel):
    market: MarketID
    trade_date: date
    trade_time: time
    trade_date_kst: date
    trade_time_kst: time
    trade_timestamp: int = 0  # Unix timestamp
    opening_price: Decimal = Field(default_factory=lambda: Decimal(0))
    high_price: Decimal = Field(default_factory=lambda: Decimal(0))
    low_price: Decimal = Field(default_factory=lambda: Decimal(0))
    trade_price: Decimal = Field(default_factory=lambda: Decimal(0))
    prev_closing_price: Decimal = Field(default_factory=lambda: Decimal(0))
    change: ChangeType
    change_rate: Decimal = Field(default_factory=lambda: Decimal(0))
    signed_change_price: Decimal = Field(default_factory=lambda: Decimal(0))
    signed_change_rate: Decimal = Field(default_factory=lambda: Decimal(0))
    trade_volume: Decimal = Field(default_factory=lambda: Decimal(0))
    acc_trade_price: Decimal = Field(default_factory=lambda: Decimal(0))
    acc_trade_price_24h: Decimal = Field(default_factory=lambda: Decimal(0))
    acc_trade_volume: Decimal = Field(default_factory=lambda: Decimal(0))
    acc_trade_volume_24h: Decimal = Field(default_factory=lambda: Decimal(0))
    highest_52_week_price: Decimal = Field(default_factory=lambda: Decimal(0))
    highest_52_week_date: date
    lowest_52_week_price: Decimal = Field(default_factory=lambda: Decimal(0))
    lowest_52_week_date: date
    timestamp: int = 0

    @field_validator("market", mode="before", check_fields=False)
    def validate_market(cls, value):
        if isinstance(value, str):
            return MarketID.from_string(value)
        return value

    @field_validator("trade_date", "trade_date_kst", mode="before", check_fields=False)
    def validate_connected_date(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, CONNECTED_DATE_FORMAT).date()
        return value

    @field_validator("trade_time", "trade_time_kst", mode="before", check_fields=False)
    def validate_connected_time(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, CONNECTED_TIME_FORMAT).time()
        return value

    @field_validator(
        "highest_52_week_date", "lowest_52_week_date", mode="before", check_fields=False
    )
    def validate_date(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, DATE_FORMAT).date()
        return value


class OrderBookUnit(FormattableBaseModel):
    ask_price: Decimal = Field(default_factory=lambda: Decimal(0))
    bid_price: Decimal = Field(default_factory=lambda: Decimal(0))
    ask_size: Decimal = Field(default_factory=lambda: Decimal(0))
    bid_size: Decimal = Field(default_factory=lambda: Decimal(0))


"""orderbook_units 리스트에는 15호가 정보를 차례대로
(1호가, 2호가 ... 15호가) 담고 있습니다. 단, market
에 단일 마켓 코드만 입력 시 orderbook_units 리스트에 
30호가까지의 정보를 제공합니다."""


class OrderBook(FormattableBaseModel):
    market: MarketID
    timestamp: int = 0
    total_ask_size: Decimal = Field(default_factory=lambda: Decimal(0))
    total_bid_size: Decimal = Field(default_factory=lambda: Decimal(0))
    orderbook_units: List[OrderBookUnit]

    def model_post_init(self, __context):
        self.__dict__["orderbook_units"] = DFList(self.orderbook_units)

    @property
    def orderbook_units(self) -> DFList[OrderBookUnit]:
        return self.__dict__["orderbook_units"]

    @field_validator("market", mode="before", check_fields=False)
    def validate_market(cls, value):
        if isinstance(value, str):
            return MarketID.from_string(value)
        return value
    

class WarningMarketInfo(FormattableBaseModel):
    market: MarketID
    warning_type: WarningType
    end_date: datetime  # KST

    @field_validator("market", mode="before", check_fields=False)
    def validate_market(cls, value):
        if isinstance(value, str):
            return MarketID.from_string(value)
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
    avg_buy_price_modified: bool = True
    unit_currency: Currency


class OrderConstraint(FormattableBaseModel):
    currency: Currency
    price_unit: Decimal = Field(default_factory=lambda: Decimal(0.00000001))
    min_total: Decimal


class MarketInfo(FormattableBaseModel):
    id: MarketID
    name: str
    order_types: List[OrderType]
    ask_types: List[OrderType]
    bid_types: List[OrderType]
    bid: OrderConstraint
    ask: OrderConstraint
    max_total: Decimal
    state: MarketState

    @field_validator("id", mode="before", check_fields=False)
    def validate_market(cls, value):
        if isinstance(value, str):
            return MarketID.from_string(value)
        return value


class OrderAvailable(FormattableBaseModel):
    bid_fee: Decimal
    ask_fee: Decimal
    maker_bid_fee: Decimal
    maker_ask_fee: Decimal
    market: MarketInfo
    bid_account: Account
    ask_account: Account


class Order(FormattableBaseModel):
    uuid: OrderID
    side: TradeSide
    ord_type: OrderType
    price: Decimal
    state: OrderState
    market: MarketID
    created_at: datetime
    volume: Decimal
    remaining_volume: Decimal
    reserved_fee: Decimal
    remaining_fee: Decimal
    paid_fee: Decimal
    locked: Decimal
    executed_volume: Decimal
    trades_count: int

    @field_validator("market", mode="before", check_fields=False)
    def validate_market(cls, value):
        if isinstance(value, str):
            return MarketID.from_string(value)
        return value
    
    @field_validator("created_at", mode="before", check_fields=False)
    def validate_datetime(cls, value):
        if isinstance(value, str):
            return parse_datetime(value)
        return value
    
    @field_validator("side", mode="before", check_fields=False)
    def normalize_side(cls, v):
        if isinstance(v, str):
            return TradeSide(v.upper())
        return v



class Trade(FormattableBaseModel):
    market: MarketID
    uuid: OrderID
    price: Decimal
    volume: Decimal
    funds: Decimal
    side: TradeSide
    created_at: datetime

    @field_validator("market", mode="before", check_fields=False)
    def validate_market(cls, value):
        if isinstance(value, str):
            return MarketID.from_string(value)
        return value
    
    @field_validator("created_at", mode="before", check_fields=False)
    def validate_datetime(cls, value):
        if isinstance(value, str):
            return parse_datetime(value)
        return value
    
    @field_validator("side", mode="before", check_fields=False)
    def normalize_side(cls, v):
        if isinstance(v, str):
            return TradeSide(v.upper())
        return v


class OrderInfo(Order):
    trades : Optional[List[Trade]] = None


class WalletStatus(FormattableBaseModel):
    currency: Currency
    wallet_state: WalletState
    block_state: BlockState
    block_height: int = 0
    block_updated_at: datetime
    block_elapsed_minutes: int = 0
    net_type: NetworkType
    network_name: str

    @field_validator("block_updated_at", mode="before", check_fields=False)
    def validate_datetime(cls, value):
        if isinstance(value, str):
            return parse_datetime(value)
        return value


class APIKeyInfo(FormattableBaseModel):
    access_key: str
    expire_at: datetime

    @field_validator("expire_at", mode="before", check_fields=False)
    def validate_datetime(cls, value):
        if isinstance(value, str):
            return parse_datetime(value)
        return value

class OrderID(FormattableBaseModel):
    id: str

    def __str__(self) -> str:
        return f"{self.currency_from}-{self.currency_to}"
