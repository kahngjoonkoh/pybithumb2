from datetime import datetime, timezone
from typing import Any, Dict, Optional
from dataclasses import dataclass
from pydantic import BaseModel, field_validator

from pybithumb2.types import MarketWarning, WarningType
from pybithumb2.constants import DATETIME_FORMAT, KST

class FormattableBaseModel(BaseModel):
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
        expected_type = cls.model_fields[info.field_name].annotation  # Get expected type

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
            return datetime.strptime(value, DATETIME_FORMAT)
        return value


class Account(FormattableBaseModel):
    currency: Currency
    balance: float
    locked: float
    avg_buy_price: float
    avg_buy_price_modified: bool
    unit_currency: Currency


def clean_and_format_data(data: dict) -> dict:
    """removes empty values and converts non json serializable types"""

    def map_values(val: Any) -> Any:
        if isinstance(val, dict):
            return {
                k: map_values(v)
                for k, v in val.items()
                if v is not None and v != {} and len(str(v)) > 0
            }

        elif isinstance(val, list):
            return [map_values(v) for v in val if v is not None and v != {}]

        # elif isinstance(val, bool):
        #     return str(val).lower()

        elif isinstance(val, datetime):
            # if the datetime is naive, assume it's KST
            # https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive
            if val.tzinfo is None or val.tzinfo.utcoffset(val) is None:
                val = val.replace(tzinfo=KST)
            return val.strftime(DATETIME_FORMAT)

        return val

    return map_values(data)


# TOODOOOD!!!!!!!!!!!!!1
def serialize(self) -> dict:
    """
    the equivalent of self::dict but removes empty values and handles converting non json serializable types.

    Ie say we only set trusted_contact.given_name instead of generating a dict like:
        {contact: {city: None, country: None...}, etc}
    we generate just:
        {trusted_contact:{given_name: "new value"}}

    NOTE: This function recurses to handle nested models, so do not use on a self-referential model

    Returns:
        dict: a dict containing any set fields
    """

    def map_values(val: Any) -> Any:
        """
        Some types have issues being json encoded, we convert them here to be encodable

        also handles nested models and lists
        """

        if isinstance(val, UUID):
            return str(val)

        if isinstance(val, NonEmptyRequest):
            return val.to_request_fields()

        if isinstance(val, dict):
            return {k: map_values(v) for k, v in val.items()}

        if isinstance(val, list):
            return [map_values(v) for v in val]

        # RFC 3339
        if isinstance(val, datetime):
            # if the datetime is naive, assume it's UTC
            # https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive
            if val.tzinfo is None or val.tzinfo.utcoffset(val) is None:
                val = val.replace(tzinfo=timezone.utc)
            return val.isoformat()

        if isinstance(val, date):
            return val.isoformat()

        if isinstance(val, IPv4Address):
            return str(val)

        if isinstance(val, IPv6Address):
            return str(val)

        return val

    d = self.model_dump(exclude_none=True)
    if "symbol_or_symbols" in d:
        s = d["symbol_or_symbols"]
        if isinstance(s, list):
            s = ",".join(s)
        d["symbols"] = s
        del d["symbol_or_symbols"]

    # pydantic almost has what we need by passing exclude_none to dict() but it returns:
    #  {trusted_contact: {}, contact: {}, identity: None, etc}
    # so we do a simple list comprehension to filter out None and {}
    return {
        key: map_values(val)
        for key, val in d.items()
        if val is not None and val != {} and len(str(val)) > 0
    }
