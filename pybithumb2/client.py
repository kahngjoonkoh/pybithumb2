from typing import Any, Iterable, List, Optional, Type, Union
from datetime import datetime, time
from decimal import Decimal

from pybithumb2.__env__ import API_BASE_URL, FEED_API_BASE_URL
from pybithumb2.types import (
    RawData,
    Currency,
    NetworkType,
    OrderID,
    OrderState,
    OrderType,
    OrderBy,
    TradeSide,
    TimeInForce,
    TwapFrequency,
    ReceiverType,
    TwoFactorType,
)
from pybithumb2.models import (
    Account,
    DFList,
    FormattableBaseModel,
    MarketID,
    Market,
    MinuteCandle,
    DayCandle,
    WeekCandle,
    MonthCandle,
    TimeUnit,
    TradeInfo,
    Snapshot,
    OrderBook,
    OrderAvailable,
    OrderInfo,
    Order,
    OrderRequest,
    OrderCreated,
    OrderCancelled,
    BatchOrderResult,
    BatchCancelResult,
    OrderV2,
    OrderPage,
    TwapOrderID,
    TwapOrderPage,
    WarningMarketInfo,
    WalletStatus,
    APIKeyInfo,
    Notice,
    CurrencyFee,
    Transfer,
    WithdrawalCancelled,
    CoinAddress,
    WithdrawAddress,
    WithdrawChance,
)
from pybithumb2.rest import RESTClient
from pybithumb2.exceptions import APIError
from pybithumb2.utils import clean_and_format_data


def _params(scope: dict, *drop: str) -> dict:
    """The calling method's arguments, minus `self` and `drop`, formatted for the API."""
    data = {k: v for k, v in scope.items() if k != "self" and k not in drop}
    return clean_and_format_data(data)


def _to_ms(value: Optional[Union[datetime, int]]) -> Optional[int]:
    """datetime -> Unix milliseconds (naive datetimes are taken as KST)."""
    if isinstance(value, datetime):
        from pybithumb2.constants import KST

        if value.tzinfo is None:
            value = value.replace(tzinfo=KST)
        return int(value.timestamp() * 1000)
    return value


def _side(side: Optional[TradeSide]) -> Optional[str]:
    """The v2 endpoints take `bid`/`ask` in lower case."""
    return None if side is None else str(side).lower()


def _check_count(count: int, low: int, high: int, what: str) -> None:
    if count < low or count > high:
        raise APIError(f"You can only request between {low} and {high} {what}")


class BithumbClient(RESTClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        use_raw_data: bool = False,
    ) -> None:
        """
        Instantiates the Bithumb Client.
        If either key is missing, then the client will only have access to the public API.

        Args:
            api_key (str, optional): The API key for the client.
            secret_key (str, optional): The secret key for the client.
            use_raw_data (bool): Whether the API response is returned as raw data or in pydantic models.
        """
        super().__init__(API_BASE_URL, api_key, secret_key, use_raw_data)

    def _parse(
        self, response: Any, model: Type[FormattableBaseModel], many: bool = False
    ):
        if self._use_raw_data:
            return response
        if many:
            return DFList([model.model_validate(item) for item in response])
        return model.model_validate(response)

    # ##### Public API: market data #####

    def get_markets(self, isDetails: bool = False) -> Union[List[Market], RawData]:
        """
        Lists the tradable markets.

        Args:
            isDetails (bool): Include `market_warning` (유의 종목) for each market. Defaults to False.
        """
        response = self.get("/v1/market/all", is_private=False, data=_params(locals()))
        return self._parse(response, Market, many=True)

    def get_minute_candles(
        self,
        market: MarketID,
        to: Optional[datetime] = None,
        count: int = 1,
        unit: TimeUnit = TimeUnit(1),
    ) -> Union[DFList[MinuteCandle], RawData]:
        _check_count(count, 1, 200, "candles")
        response = self.get(
            f"/v1/candles/minutes/{unit}",
            is_private=False,
            data=_params(locals(), "unit"),
        )
        return self._parse(response, MinuteCandle, many=True)

    def get_day_candles(
        self,
        market: MarketID,
        to: Optional[datetime] = None,
        count: int = 1,
        convertingPriceUnit: Optional[Currency] = None,
    ) -> Union[DFList[DayCandle], RawData]:
        _check_count(count, 1, 200, "candles")
        response = self.get(
            "/v1/candles/days", is_private=False, data=_params(locals())
        )
        return self._parse(response, DayCandle, many=True)

    def get_week_candles(
        self, market: MarketID, to: Optional[datetime] = None, count: int = 1
    ) -> Union[DFList[WeekCandle], RawData]:
        _check_count(count, 1, 200, "candles")
        response = self.get(
            "/v1/candles/weeks", is_private=False, data=_params(locals())
        )
        return self._parse(response, WeekCandle, many=True)

    def get_month_candles(
        self, market: MarketID, to: Optional[datetime] = None, count: int = 1
    ) -> Union[DFList[MonthCandle], RawData]:
        _check_count(count, 1, 200, "candles")
        response = self.get(
            "/v1/candles/months", is_private=False, data=_params(locals())
        )
        return self._parse(response, MonthCandle, many=True)

    def get_trades(
        self,
        market: MarketID,
        to: Optional[time] = None,
        count: int = 1,
        cursor: Optional[int] = None,
        daysAgo: Optional[int] = None,
    ) -> Union[DFList[TradeInfo], RawData]:
        """
        Recent trades for a market, newest first.

        Args:
            to (time, optional): Only trades before this time of day (KST).
            cursor (int, optional): The `sequential_id` of the last trade seen, for the next page.
            daysAgo (int, optional): Look 1 to 7 days back.
        """
        if daysAgo is not None and (daysAgo <= 0 or daysAgo > 7):
            raise APIError("You can only request data from 1 to 7 days ago")
        response = self.get(
            "/v1/trades/ticks", is_private=False, data=_params(locals())
        )
        return self._parse(response, TradeInfo, many=True)

    def get_snapshots(
        self, markets: List[MarketID]
    ) -> Union[DFList[Snapshot], RawData]:
        data = {"markets": ",".join(str(m) for m in markets)}
        response = self.get("/v1/ticker", is_private=False, data=data)
        return self._parse(response, Snapshot, many=True)

    def get_orderbooks(
        self, markets: List[MarketID]
    ) -> Union[List[OrderBook], RawData]:
        data = {"markets": ",".join(str(m) for m in markets)}
        response = self.get("/v1/orderbook", is_private=False, data=data)
        return self._parse(response, OrderBook, many=True)

    def get_warning_markets(self) -> Union[List[WarningMarketInfo], RawData]:
        response = self.get("/v1/market/virtual_asset_warning", is_private=False)
        return self._parse(response, WarningMarketInfo, many=True)

    def get_notices(self, count: int = 5) -> Union[DFList[Notice], RawData]:
        """The latest Bithumb notices (1 to 20)."""
        _check_count(count, 1, 20, "notices")
        response = self.get(
            FEED_API_BASE_URL + "/v1/notices", is_private=False, data=_params(locals())
        )
        return self._parse(response, Notice, many=True)

    def get_fees(self, currency: Currency) -> Union[DFList[CurrencyFee], RawData]:
        """Deposit and withdrawal fees and minimums for a currency, per network."""
        response = self.get(f"/v2/fee/inout/{currency}", is_private=False)
        return self._parse(response, CurrencyFee, many=True)

    # ##### Private API: account #####

    def get_accounts(self) -> Union[List[Account], RawData]:
        response = self.get("/v1/accounts", is_private=True)
        return self._parse(response, Account, many=True)

    def get_order_available(self, market: MarketID) -> Union[OrderAvailable, RawData]:
        response = self.get(
            "/v1/orders/chance", is_private=True, data=_params(locals())
        )
        return self._parse(response, OrderAvailable)

    def get_wallet_status(self) -> Union[DFList[WalletStatus], RawData]:
        response = self.get("/v1/status/wallet", is_private=True)
        return self._parse(response, WalletStatus, many=True)

    def get_api_keys(self) -> Union[DFList[APIKeyInfo], RawData]:
        response = self.get("/v1/api_keys", is_private=True)
        return self._parse(response, APIKeyInfo, many=True)

    # ##### Private API: orders #####

    def get_order_info(
        self, uuid: Optional[OrderID] = None, client_order_id: Optional[str] = None
    ) -> Union[OrderInfo, RawData]:
        """One order, with its trades. Pass either `uuid` or `client_order_id`."""
        if (uuid is None) == (client_order_id is None):
            raise APIError("Pass exactly one of uuid or client_order_id")
        response = self.get("/v1/order", is_private=True, data=_params(locals()))
        return self._parse(response, OrderInfo)

    def get_orders(
        self,
        market: Optional[MarketID] = None,
        uuids: Optional[List[OrderID]] = None,
        state: Optional[OrderState] = None,
        states: Optional[Iterable[OrderState]] = None,
        page: int = 1,
        limit: int = 100,
        order_by: OrderBy = OrderBy.DESC,
        client_order_ids: Optional[List[str]] = None,
    ) -> Union[DFList[Order], RawData]:
        """Lists orders (v1, page-numbered). For cursor paging see `get_pending_orders` and `get_closed_orders`."""
        if state and states:
            raise APIError("You can not have both state and states parameter")
        _check_count(limit, 1, 100, "orders")
        response = self.get("/v1/orders", is_private=True, data=_params(locals()))
        return self._parse(response, Order, many=True)

    def submit_order(
        self,
        market: MarketID,
        side: TradeSide,
        volume: Optional[Decimal] = None,
        price: Optional[Decimal] = None,
        ord_type: OrderType = OrderType.LIMIT,
        client_order_id: Optional[str] = None,
        time_in_force: Optional[TimeInForce] = None,
    ) -> Union[OrderCreated, RawData]:
        """
        Places an order.

        Args:
            side (TradeSide): BID to buy, ASK to sell.
            volume (Decimal, optional): Quantity. Required for LIMIT and MARKET (market sell).
            price (Decimal, optional): Unit price for LIMIT; the total to spend for PRICE (market buy).
            ord_type (OrderType): LIMIT, PRICE (market buy), MARKET (market sell) or BEST.
            client_order_id (str, optional): Your own id: 1 to 36 of A-Z, a-z, 0-9, - and _.
            time_in_force (TimeInForce, optional): IOC, FOK or POST_ONLY (LIMIT and BEST only).
        """
        request = OrderRequest(
            market=market,
            side=side,
            order_type=ord_type,
            volume=volume,
            price=price,
            client_order_id=client_order_id,
            time_in_force=time_in_force,
        )
        response = self.post("/v2/orders", is_private=True, data=request.to_body())
        return self._parse(response, OrderCreated)

    def submit_orders(
        self, orders: List[OrderRequest]
    ) -> Union[DFList[BatchOrderResult], RawData]:
        """
        Places several orders in one request. Each result carries either the `order_id` or the
        error `name`/`message` for that order; check `result.ok`.
        """
        data = {"batch_orders": [o.to_body() for o in orders]}
        response = self.post("/v2/orders/batch", is_private=True, data=data)
        if self._use_raw_data:
            return response
        return DFList(
            [
                BatchOrderResult.model_validate(r)
                for r in response["batch_orders_response"]
            ]
        )

    def cancel_order(
        self, uuid: Optional[OrderID] = None, client_order_id: Optional[str] = None
    ) -> Union[OrderCancelled, RawData]:
        """
        Requests cancellation of one order, by order id or `client_order_id`.
        Cancelling is asynchronous: check the order's state afterwards.
        """
        if (uuid is None) == (client_order_id is None):
            raise APIError("Pass exactly one of uuid or client_order_id")
        data = clean_and_format_data(
            {"order_id": uuid, "client_order_id": client_order_id}
        )
        response = self.delete("/v2/order", is_private=True, data=data)
        return self._parse(response, OrderCancelled)

    def cancel_orders(
        self,
        order_ids: Optional[List[OrderID]] = None,
        client_order_ids: Optional[List[str]] = None,
    ) -> Union[BatchCancelResult, RawData]:
        """Requests cancellation of several orders. The result lists what was accepted and what failed."""
        if not order_ids and not client_order_ids:
            raise APIError("Pass order_ids or client_order_ids")
        response = self.post(
            "/v2/orders/cancel", is_private=True, data=_params(locals())
        )
        return self._parse(response, BatchCancelResult)

    def search_orders(
        self,
        market: Optional[MarketID] = None,
        order_ids: Optional[List[OrderID]] = None,
        client_order_ids: Optional[List[str]] = None,
        order_by: OrderBy = OrderBy.DESC,
    ) -> Union[DFList[OrderV2], RawData]:
        """Looks up specific orders by order id or `client_order_id` (v2)."""
        response = self.post(
            "/v2/orders/search", is_private=True, data=_params(locals())
        )
        return self._parse(response, OrderV2, many=True)

    def get_pending_orders(
        self,
        market: Optional[MarketID] = None,
        state: OrderState = OrderState.WAIT,
        limit: int = 100,
        order_by: OrderBy = OrderBy.DESC,
        next_key: Optional[str] = None,
    ) -> Union[OrderPage, RawData]:
        """Open orders: WAIT (resting) or WATCH (reserved). Page with `next_key`."""
        _check_count(limit, 1, 100, "orders")
        response = self.get(
            "/v2/orders/pending", is_private=True, data=_params(locals())
        )
        return self._parse(response, OrderPage)

    def get_closed_orders(
        self,
        market: Optional[MarketID] = None,
        state: Optional[OrderState] = None,
        states: Optional[Iterable[OrderState]] = None,
        start_time: Optional[Union[datetime, int]] = None,
        end_time: Optional[Union[datetime, int]] = None,
        limit: int = 100,
        order_by: OrderBy = OrderBy.DESC,
        next_key: Optional[str] = None,
    ) -> Union[OrderPage, RawData]:
        """
        Finished orders (DONE or CANCEL). The window between `start_time` and `end_time` is at
        most 7 days; times are datetimes (naive = KST) or Unix milliseconds. Page with `next_key`.
        """
        if state and states:
            raise APIError("You can not have both state and states parameter")
        _check_count(limit, 1, 1000, "orders")
        start_time, end_time = _to_ms(start_time), _to_ms(end_time)
        response = self.get(
            "/v2/orders/history", is_private=True, data=_params(locals())
        )
        return self._parse(response, OrderPage)

    # ##### Private API: TWAP #####

    def submit_twap_order(
        self,
        market: MarketID,
        side: TradeSide,
        duration: int,
        frequency: TwapFrequency,
        volume: Optional[Decimal] = None,
        price: Optional[Decimal] = None,
    ) -> Union[TwapOrderID, RawData]:
        """
        Splits an order into child orders over time.

        Args:
            duration (int): Total run time in seconds, 300 to 43200.
            frequency (TwapFrequency): Seconds between child orders.
            volume (Decimal, optional): Quantity to sell (required for ASK).
            price (Decimal, optional): Total to spend (required for BID).
        """
        if duration < 300 or duration > 43200:
            raise APIError("duration must be between 300 and 43200 seconds")
        data = clean_and_format_data(
            {
                "market": market,
                "side": _side(side),
                "volume": volume,
                "price": price,
                "duration": str(duration),
                "frequency": frequency,
            }
        )
        response = self.post("/v1/twap", is_private=True, data=data)
        return self._parse(response, TwapOrderID)

    def get_twap_orders(
        self,
        market: Optional[MarketID] = None,
        uuids: Optional[List[str]] = None,
        state: Optional[str] = None,
        next_key: Optional[str] = None,
        limit: int = 100,
        order_by: OrderBy = OrderBy.DESC,
    ) -> Union[TwapOrderPage, RawData]:
        response = self.get("/v1/twap", is_private=True, data=_params(locals()))
        return self._parse(response, TwapOrderPage)

    def cancel_twap_order(self, algo_order_id: str) -> Union[TwapOrderID, RawData]:
        response = self.delete("/v1/twap", is_private=True, data=_params(locals()))
        return self._parse(response, TwapOrderID)

    # ##### Private API: deposits #####

    def get_deposit(
        self, currency: Currency, uuid: Optional[str] = None, txid: Optional[str] = None
    ) -> Union[Transfer, RawData]:
        response = self.get("/v1/deposit", is_private=True, data=_params(locals()))
        return self._parse(response, Transfer)

    def get_deposits(
        self,
        currency: Optional[Currency] = None,
        state: Optional[str] = None,
        uuids: Optional[List[str]] = None,
        txids: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 100,
        order_by: OrderBy = OrderBy.DESC,
    ) -> Union[DFList[Transfer], RawData]:
        """Coin deposits. A txid containing a space or comma only matches via `get_deposit`."""
        _check_count(limit, 1, 100, "deposits")
        response = self.get("/v1/deposits", is_private=True, data=_params(locals()))
        return self._parse(response, Transfer, many=True)

    def get_krw_deposits(
        self,
        state: Optional[str] = None,
        uuids: Optional[List[str]] = None,
        txids: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 100,
        order_by: OrderBy = OrderBy.DESC,
    ) -> Union[DFList[Transfer], RawData]:
        _check_count(limit, 1, 100, "deposits")
        response = self.get("/v1/deposits/krw", is_private=True, data=_params(locals()))
        return self._parse(response, Transfer, many=True)

    def deposit_krw(
        self, amount: Decimal, two_factor_type: TwoFactorType = TwoFactorType.KAKAO
    ) -> Union[Transfer, RawData]:
        """Requests a KRW deposit from the linked bank account; confirmed with 2FA."""
        response = self.post(
            "/v1/deposits/krw", is_private=True, data=_params(locals())
        )
        return self._parse(response, Transfer)

    def generate_deposit_address(
        self, currency: Currency, net_type: NetworkType
    ) -> Union[CoinAddress, RawData]:
        """Creates a deposit address. Generation is asynchronous; poll `get_deposit_address`."""
        response = self.post(
            "/v1/deposits/generate_coin_address",
            is_private=True,
            data=_params(locals()),
        )
        return self._parse(response, CoinAddress)

    def get_deposit_address(
        self, currency: Currency, net_type: NetworkType
    ) -> Union[CoinAddress, RawData]:
        response = self.get(
            "/v1/deposits/coin_address", is_private=True, data=_params(locals())
        )
        return self._parse(response, CoinAddress)

    def get_deposit_addresses(self) -> Union[DFList[CoinAddress], RawData]:
        response = self.get("/v1/deposits/coin_addresses", is_private=True)
        return self._parse(response, CoinAddress, many=True)

    # ##### Private API: withdrawals #####

    def get_withdraw_chance(
        self, currency: Currency, net_type: NetworkType
    ) -> Union[WithdrawChance, RawData]:
        """Fees, limits and account state for withdrawing `currency` on `net_type`."""
        response = self.get(
            "/v1/withdraws/chance", is_private=True, data=_params(locals())
        )
        return self._parse(response, WithdrawChance)

    def get_withdrawal(
        self, currency: Currency, uuid: Optional[str] = None, txid: Optional[str] = None
    ) -> Union[Transfer, RawData]:
        response = self.get("/v1/withdraw", is_private=True, data=_params(locals()))
        return self._parse(response, Transfer)

    def get_withdrawals(
        self,
        currency: Optional[Currency] = None,
        state: Optional[str] = None,
        uuids: Optional[List[str]] = None,
        txids: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 100,
        order_by: OrderBy = OrderBy.DESC,
    ) -> Union[DFList[Transfer], RawData]:
        """Coin withdrawals. A txid containing a space or comma only matches via `get_withdrawal`."""
        _check_count(limit, 1, 100, "withdrawals")
        response = self.get("/v1/withdraws", is_private=True, data=_params(locals()))
        return self._parse(response, Transfer, many=True)

    def get_krw_withdrawals(
        self,
        state: Optional[str] = None,
        uuids: Optional[List[str]] = None,
        txids: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 100,
        order_by: OrderBy = OrderBy.DESC,
    ) -> Union[DFList[Transfer], RawData]:
        _check_count(limit, 1, 100, "withdrawals")
        response = self.get(
            "/v1/withdraws/krw", is_private=True, data=_params(locals())
        )
        return self._parse(response, Transfer, many=True)

    def withdraw_coin(
        self,
        currency: Currency,
        net_type: NetworkType,
        amount: Decimal,
        address: str,
        secondary_address: Optional[str] = None,
        exchange_name: Optional[str] = None,
        receiver_type: Optional[ReceiverType] = None,
        receiver_ko_name: Optional[str] = None,
        receiver_en_name: Optional[str] = None,
        receiver_corp_ko_name: Optional[str] = None,
        receiver_corp_en_name: Optional[str] = None,
    ) -> Union[Transfer, RawData]:
        """
        Withdraws a coin to an address on the withdrawal allow-list (`get_withdraw_addresses`).
        Travel-rule fields (exchange and receiver) are required when sending to another exchange.
        """
        response = self.post(
            "/v1/withdraws/coin", is_private=True, data=_params(locals())
        )
        return self._parse(response, Transfer)

    def withdraw_krw(
        self, amount: Decimal, two_factor_type: TwoFactorType = TwoFactorType.KAKAO
    ) -> Union[Transfer, RawData]:
        """Withdraws KRW to the linked bank account; confirmed with 2FA."""
        response = self.post(
            "/v1/withdraws/krw", is_private=True, data=_params(locals())
        )
        return self._parse(response, Transfer)

    def cancel_withdrawal(
        self, withdrawal_id: str
    ) -> Union[WithdrawalCancelled, RawData]:
        response = self.delete(
            "/v1/withdraws/coin", is_private=True, data=_params(locals())
        )
        return self._parse(response, WithdrawalCancelled)

    def get_withdraw_addresses(self) -> Union[DFList[WithdrawAddress], RawData]:
        """The withdrawal allow-list registered on the Bithumb website."""
        response = self.get("/v1/withdraws/coin_addresses", is_private=True)
        return self._parse(response, WithdrawAddress, many=True)
