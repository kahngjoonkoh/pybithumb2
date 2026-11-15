import re
from datetime import datetime, date, time
from types import UnionType
from typing import (
    TypeVar,
    Generic,
    Optional,
    List,
    Union,
    TYPE_CHECKING,
    get_args,
    get_origin,
)
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

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
    NetworkType,
    WarningStep,
    TimeInForce,
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


def _unwrap_optional(annotation):
    """Optional[X] -> X; anything else is returned unchanged."""
    args = [a for a in get_args(annotation) if a is not type(None)]
    if get_origin(annotation) in (Union, UnionType) and len(args) == 1:
        return args[0]
    return annotation


def _parse_date(value: str):
    for fmt in (DATE_FORMAT, CONNECTED_DATE_FORMAT):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return value


class FormattableBaseModel(BaseModel, DataFramable):
    @field_validator("*", mode="before")
    @classmethod
    def validate_field(cls, value, info):
        """Dynamically converts string fields to their expected type."""
        expected_type = _unwrap_optional(cls.model_fields[info.field_name].annotation)

        if not isinstance(value, str) or not isinstance(expected_type, type):
            return value
        try:
            if issubclass(expected_type, MarketID):
                return MarketID.from_string(value)
            if issubclass(expected_type, datetime):
                return parse_datetime(value)
            if issubclass(expected_type, date):
                return _parse_date(value)
            if issubclass(expected_type, TradeSide):
                return TradeSide(value.upper())
            if issubclass(expected_type, BaseModel):
                return value
            return expected_type(value)  # Convert to expected type
        except (ValueError, TypeError, ArithmeticError):
            return value  # If conversion fails, let pydantic report it

    def __repr__(self) -> str:
        field_strings = ", ".join(
            f"{name}={value!r}"
            for name, value in self.__dict__.items()
            if value is not None
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


class MonthCandle(Candle):
    first_day_of_period: date


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


class OrderBookUnit(FormattableBaseModel):
    ask_price: Decimal = Field(default_factory=lambda: Decimal(0))
    bid_price: Decimal = Field(default_factory=lambda: Decimal(0))
    ask_size: Decimal = Field(default_factory=lambda: Decimal(0))
    bid_size: Decimal = Field(default_factory=lambda: Decimal(0))


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


class WarningMarketInfo(FormattableBaseModel):
    market: MarketID
    warning_type: WarningType
    warning_step: Optional[WarningStep] = None
    end_date: datetime  # KST


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
    order_sides: Optional[List[str]] = None
    ask_types: List[OrderType]
    bid_types: List[OrderType]
    bid: OrderConstraint
    ask: OrderConstraint
    max_total: Decimal
    state: MarketState


class OrderAvailable(FormattableBaseModel):
    bid_fee: Decimal
    ask_fee: Decimal
    maker_bid_fee: Decimal
    maker_ask_fee: Decimal
    market: MarketInfo
    bid_account: Account
    ask_account: Account


class Order(FormattableBaseModel):
    """An order as returned by the v1 order endpoints (`uuid`, `ord_type`)."""

    uuid: OrderID
    client_order_id: Optional[str] = None
    side: TradeSide
    ord_type: OrderType
    price: Optional[Decimal] = None  # null for market sell orders
    state: OrderState
    market: MarketID
    created_at: datetime
    volume: Optional[Decimal] = None  # null for market buy orders
    remaining_volume: Optional[Decimal] = None
    reserved_fee: Decimal
    remaining_fee: Decimal
    paid_fee: Decimal
    locked: Decimal
    executed_volume: Decimal
    executed_funds: Optional[Decimal] = None
    trades_count: int = 0
    stp_type: Optional[str] = None
    time_in_force: Optional[TimeInForce] = None


class Trade(FormattableBaseModel):
    market: MarketID
    uuid: OrderID
    price: Decimal
    volume: Decimal
    funds: Decimal
    side: TradeSide
    created_at: datetime


class OrderInfo(Order):
    trades: Optional[List[Trade]] = None
    cancel_type: Optional[str] = None
    canceling_uuid: Optional[str] = None


class WalletStatus(FormattableBaseModel):
    currency: Currency
    wallet_state: WalletState
    block_state: BlockState
    block_height: int = 0
    block_updated_at: datetime
    block_elapsed_minutes: int = 0
    net_type: NetworkType
    network_name: str


class APIKeyInfo(FormattableBaseModel):
    access_key: str
    expire_at: datetime


# ##### v2 orders #####


class OrderRequest(FormattableBaseModel):
    """
    An order to place, for `submit_order` and `submit_orders`.

    LIMIT needs `price` (unit price) and `volume`; PRICE (market buy) needs `price` (total to
    spend); MARKET (market sell) needs `volume`. BEST is priced at the best opposing quote and
    needs `time_in_force` IOC or FOK. POST_ONLY is for LIMIT only.
    """

    market: MarketID
    side: TradeSide
    order_type: OrderType = OrderType.LIMIT
    price: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    client_order_id: Optional[str] = None
    time_in_force: Optional[TimeInForce] = None

    def model_post_init(self, __context):
        needs = {
            OrderType.LIMIT: ("price", "volume"),
            OrderType.PRICE: ("price",),
            OrderType.MARKET: ("volume",),
            OrderType.BEST: ("time_in_force",),
        }[self.order_type]
        missing = [f for f in needs if getattr(self, f) is None]
        if missing:
            raise ValueError(f"{self.order_type!r} orders need {', '.join(missing)}")
        tif = self.time_in_force
        if tif and self.order_type not in (OrderType.LIMIT, OrderType.BEST):
            raise ValueError("time_in_force only applies to LIMIT and BEST orders")
        if tif == TimeInForce.POST_ONLY and self.order_type != OrderType.LIMIT:
            raise ValueError("POST_ONLY only applies to LIMIT orders")
        cid = self.client_order_id
        if cid is not None and not re.fullmatch(r"[A-Za-z0-9_-]{1,36}", cid):
            raise ValueError("client_order_id must be 1-36 of A-Z, a-z, 0-9, - and _")

    def to_body(self) -> dict:
        return clean_and_format_data(
            {
                "market": self.market,
                "side": str(self.side).lower(),
                "order_type": self.order_type,
                "price": self.price,
                "volume": self.volume,
                "client_order_id": self.client_order_id,
                "time_in_force": self.time_in_force,
            }
        )


class OrderCreated(FormattableBaseModel):
    """The acknowledgement of a placed order (v2)."""

    order_id: OrderID
    client_order_id: Optional[str] = None
    market: MarketID
    side: TradeSide
    order_type: OrderType
    created_at: datetime
    stp_type: Optional[str] = None
    time_in_force: Optional[TimeInForce] = None


class BatchOrderResult(FormattableBaseModel):
    """One entry of a batch order response: an accepted order, or `name`/`message` if it failed."""

    client_order_id: Optional[str] = None
    order_id: Optional[OrderID] = None
    market: Optional[MarketID] = None
    side: Optional[TradeSide] = None
    order_type: Optional[OrderType] = None
    created_at: Optional[datetime] = None
    stp_type: Optional[str] = None
    time_in_force: Optional[TimeInForce] = None
    name: Optional[str] = None
    message: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.order_id is not None and self.name is None


class OrderCancelled(FormattableBaseModel):
    """The acknowledgement of a cancel request (v2). Cancelling is asynchronous."""

    order_id: OrderID
    client_order_id: Optional[str] = None
    created_at: datetime


class ErrorInfo(FormattableBaseModel):
    name: str
    message: Optional[str] = None


class CancelFailure(FormattableBaseModel):
    order_id: Optional[OrderID] = None
    client_order_id: Optional[str] = None
    error: ErrorInfo


class BatchCancelResult(FormattableBaseModel):
    success: List[OrderCancelled] = Field(default_factory=list)
    fail: List[CancelFailure] = Field(default_factory=list)


class OrderV2(FormattableBaseModel):
    """An order as returned by the v2 order endpoints (`order_id`, `order_type`)."""

    order_id: OrderID
    client_order_id: Optional[str] = None
    side: TradeSide
    order_type: OrderType
    price: Optional[Decimal] = None
    state: OrderState
    market: MarketID
    created_at: datetime
    volume: Optional[Decimal] = None
    remaining_volume: Optional[Decimal] = None
    reserved_fee: Decimal
    remaining_fee: Decimal
    paid_fee: Decimal
    locked: Decimal
    executed_volume: Decimal
    executed_funds: Optional[Decimal] = None
    trades_count: int = 0
    stp_type: Optional[str] = None
    time_in_force: Optional[TimeInForce] = None
    cancel_type: Optional[str] = None
    canceling_order_id: Optional[str] = None


class OrderPage(FormattableBaseModel):
    """A page of orders. Pass `next_key` to the same call for the next page."""

    data: List[OrderV2]
    has_next: bool = False
    next_key: Optional[str] = None

    def model_post_init(self, __context):
        self.__dict__["data"] = DFList(self.data)


# ##### TWAP #####


class TwapOrder(FormattableBaseModel):
    uuid: str
    side: TradeSide
    price: Optional[Decimal] = None
    state: str  # e.g. "progress", "done", "cancel"; the docs are inconsistent, so not an enum
    market: MarketID
    created_at: datetime
    volume: Optional[Decimal] = None
    finished_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    cancel_type: Optional[str] = None
    total_order_count: int = 0
    total_trades_count: int = 0
    progress_count: int = 0
    total_executed_amount: Decimal = Field(default_factory=lambda: Decimal(0))
    total_executed_volume: Decimal = Field(default_factory=lambda: Decimal(0))
    avg_trade_price: Optional[Decimal] = None
    wallet_id: Optional[str] = None


class TwapOrderPage(FormattableBaseModel):
    orders: List[TwapOrder]
    has_next: bool = False
    next_key: Optional[str] = None

    def model_post_init(self, __context):
        self.__dict__["orders"] = DFList(self.orders)


class TwapOrderID(FormattableBaseModel):
    algo_order_id: str


# ##### Market info #####


class Notice(FormattableBaseModel):
    categories: List[str] = Field(default_factory=list)
    title: str
    pc_url: str
    published_at: datetime
    modified_at: Optional[datetime] = None


class NetworkFee(FormattableBaseModel):
    net_name: str
    deposit_fee_quantity: Optional[Decimal] = None
    deposit_minimum_quantity: Optional[Decimal] = None
    withdraw_fee_quantity: Optional[Decimal] = None
    withdraw_rate: Optional[Decimal] = None
    withdraw_fee_min: Optional[Decimal] = None
    withdraw_fee_max: Optional[Decimal] = None
    withdraw_minimum_quantity: Optional[Decimal] = None


class CurrencyFee(FormattableBaseModel):
    name: str
    currency: Currency
    networks: List[NetworkFee]


# ##### Deposits and withdrawals #####


class Transfer(FormattableBaseModel):
    """A deposit or withdrawal record (`type` is "deposit" or "withdraw")."""

    type: str
    uuid: str
    currency: Currency
    net_type: Optional[NetworkType] = None
    txid: Optional[str] = None
    state: str  # e.g. DEPOSIT_ACCEPTED, PROCESSING, DONE; see the API docs for the full list
    created_at: datetime
    done_at: Optional[datetime] = None
    amount: Decimal
    fee: Decimal = Field(default_factory=lambda: Decimal(0))
    krw_amount: Optional[Decimal] = None
    transaction_type: Optional[str] = None


class WithdrawalCancelled(FormattableBaseModel):
    type: str
    withdrawal_id: str
    currency: Currency
    net_type: Optional[NetworkType] = None
    state: str
    created_at: datetime
    amount: Decimal
    fee: Decimal = Field(default_factory=lambda: Decimal(0))
    krw_amount: Optional[Decimal] = None


class CoinAddress(FormattableBaseModel):
    currency: Currency
    net_type: NetworkType
    deposit_address: Optional[str] = (
        None  # null while the address is still being generated
    )
    secondary_address: Optional[str] = None


class WithdrawAddress(FormattableBaseModel):
    currency: Currency
    net_type: NetworkType
    network_name: Optional[str] = None
    withdraw_address: str
    secondary_address: Optional[str] = None
    exchange_name: Optional[str] = None
    owner_type: Optional[str] = None
    owner_ko_name: Optional[str] = None
    owner_en_name: Optional[str] = None
    owner_corp_ko_name: Optional[str] = None
    owner_corp_en_name: Optional[str] = None


class MemberLevel(FormattableBaseModel):
    security_level: Optional[int] = None
    fee_level: Optional[int] = None
    email_verified: Optional[bool] = None
    identity_auth_verified: Optional[bool] = None
    bank_account_verified: Optional[bool] = None
    two_factor_auth_verified: Optional[bool] = None
    locked: Optional[bool] = None
    wallet_locked: Optional[bool] = None


class WithdrawCurrency(FormattableBaseModel):
    code: Currency
    withdraw_fee: Optional[Decimal] = None
    withdraw_rate: Optional[Decimal] = None
    withdraw_fee_min: Optional[Decimal] = None
    withdraw_fee_max: Optional[Decimal] = None
    is_coin: bool = True
    wallet_state: Optional[str] = None
    wallet_support: List[str] = Field(default_factory=list)


class WithdrawLimit(FormattableBaseModel):
    currency: Currency
    onetime: Optional[Decimal] = None
    daily: Optional[Decimal] = None
    remaining_daily: Optional[Decimal] = None
    remaining_daily_fiat: Optional[Decimal] = None
    remaining_daily_krw: Optional[Decimal] = None
    fiat_currency: Optional[Currency] = None
    minimum: Optional[Decimal] = None
    fixed: Optional[int] = None
    withdraw_delayed_fiat: Optional[Decimal] = None
    can_withdraw: bool = False


class WithdrawChance(FormattableBaseModel):
    member_level: MemberLevel
    currency: WithdrawCurrency
    account: Account
    withdraw_limit: WithdrawLimit
