from typing import Any
from datetime import datetime, time
from dateutil import parser
from decimal import Decimal

from pybithumb2.constants import (
    TIME_FORMAT,
    DATETIME_FORMAT,
    DATETIME_FORMAT_T,
    DATETIME_FORMAT_TZ,
    KST,
)


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
            return ",".join(map_values(v) for v in val if v is not None and v != {})

        elif isinstance(val, time):
            return val.strftime(TIME_FORMAT)

        elif isinstance(val, datetime):
            # if the datetime is naive, assume it's KST
            # https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive
            if val.tzinfo is None or val.tzinfo.utcoffset(val) is None:
                val = val.replace(tzinfo=KST)
            return val.strftime(DATETIME_FORMAT)

        elif isinstance(val, (int, float, Decimal)):
            return val

        return str(val)

    return map_values(data)


def parse_datetime(datetime_str: str) -> datetime:
    """Handles datetime fields inconsistencies across endpoints"""
    formats = [DATETIME_FORMAT, DATETIME_FORMAT_T, DATETIME_FORMAT_TZ]

    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue

    # Fallback for timezone-aware formats
    try:
        return parser.parse(datetime_str)  # Handles `+09:00` automatically
    except ValueError:
        pass

    raise ValueError(f"Invalid datetime format: {datetime_str}")
