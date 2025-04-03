from enum import Enum
from typing import Any, Dict, List, Union

RawData = Dict[str, Any]

HTTPResult = Union[dict, List[dict], Any]

# class Currency(Enum):
#     KRW = "KRW"
#     BTC = "BTC"

class MarketWarning(Enum):
    NONE = "NONE"
    CAUTION = "CAUTION"

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"

    def __str__(self):
        return self.value


class WarningType(Enum):
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
    PRICE_DIFFERENCE_HIGH = "PRICE_DIFFERENCE_HIGH"
    SPECIFIC_ACCOUNT_HIGH_TRANSACTION = "SPECIFIC_ACCOUNT_HIGH_TRANSACTION"
    EXCHANGE_TRADING_CONCENTRATION = "EXCHANGE_TRADING_CONCENTRATION"
