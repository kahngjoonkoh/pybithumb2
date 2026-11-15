from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, List, Union

RawData = Dict[str, Any]

HTTPResult = Union[dict, List[dict], Any]


class FormattableEnum(Enum):
    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class Currency:
    code: str

    def __post_init__(self):
        object.__setattr__(self, "code", self.code.upper())

    def __str__(self) -> str:
        return self.code


class TradeSide(FormattableEnum):
    ASK = "ASK"
    BID = "BID"


class ChangeType(FormattableEnum):
    EVEN = "EVEN"
    RISE = "RISE"
    FALL = "FALL"


class MarketWarning(FormattableEnum):
    NONE = "NONE"
    CAUTION = "CAUTION"


class WarningType(FormattableEnum):
    """
    경보 유형:
        PRICE_SUDDEN_FLUCTUATION: 가격 급등락
        TRADING_VOLUME_SUDDEN_FLUCTUATION: 거래량 급등
        DEPOSIT_AMOUNT_SUDDEN_FLUCTUATION: 입금량 급등
        PRICE_DIFFERENCE_HIGH: 가격 차이
        SPECIFIC_ACCOUNT_HIGH_TRANSACTION: 소수계좌 거래 집중
        EXCHANGE_TRADING_CONCENTRATION: 거래소 거래 집중
    """

    PRICE_SUDDEN_FLUCTUATION = "PRICE_SUDDEN_FLUCTUATION"
    TRADING_VOLUME_SUDDEN_FLUCTUATION = "TRADING_VOLUME_SUDDEN_FLUCTUATION"
    DEPOSIT_AMOUNT_SUDDEN_FLUCTUATION = "DEPOSIT_AMOUNT_SUDDEN_FLUCTUATION"
    PRICE_DIFFERENCE_HIGH = "PRICE_DIFFERENCE_HIGH"
    SPECIFIC_ACCOUNT_HIGH_TRANSACTION = "SPECIFIC_ACCOUNT_HIGH_TRANSACTION"
    EXCHANGE_TRADING_CONCENTRATION = "EXCHANGE_TRADING_CONCENTRATION"


class OrderType(FormattableEnum):
    """
    LIMIT: 지정가, PRICE: 시장가 매수 (price is the total to spend),
    MARKET: 시장가 매도, BEST: 최유리 지정가 (KRW markets only)
    """

    LIMIT = "limit"
    PRICE = "price"
    MARKET = "market"
    BEST = "best"


class TimeInForce(FormattableEnum):
    IOC = "ioc"
    FOK = "fok"
    POST_ONLY = "post_only"


class WarningStep(FormattableEnum):
    CAUTION = "CAUTION"
    WARNING = "WARNING"
    DANGER = "DANGER"


class TwapFrequency(FormattableEnum):
    """Seconds between the child orders of a TWAP order."""

    S15 = "15"
    S20 = "20"
    S30 = "30"
    S60 = "60"
    S120 = "120"


class ReceiverType(FormattableEnum):
    PERSONAL = "personal"
    CORPORATION = "corporation"


class TwoFactorType(FormattableEnum):
    KAKAO = "kakao"


class MarketState(FormattableEnum):
    ACTIVE = "active"


class OrderState(FormattableEnum):
    WAIT = "wait"
    WATCH = "watch"
    PROGRESS = "progress"
    DONE = "done"
    CANCEL = "cancel"


@dataclass(frozen=True)
class NetworkType:
    code: str

    def __post_init__(self):
        object.__setattr__(self, "code", self.code.upper())

    def __str__(self) -> str:
        return self.code


class WalletState(FormattableEnum):
    WORKING = "working"
    WITHDRAW_ONLY = "withdraw_only"
    DEPOSIT_ONLY = "deposit_only"
    PAUSED = "paused"


class BlockState(FormattableEnum):
    NORMAL = "normal"
    DELAYED = "delayed"
    INACTIVE = "inactive"


@dataclass(frozen=True)
class OrderID:
    id: str

    def __str__(self) -> str:
        return self.id


class OrderBy(FormattableEnum):
    ASC = "asc"
    DESC = "desc"
