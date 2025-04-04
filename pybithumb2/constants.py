from datetime import timezone, timedelta

"""The Bithumb API uses two multiple datetime formats."""
DATE_FORMAT = "%Y-%m-%d"
CONNECTED_DATE_FORMAT = "%Y%m%d"
TIME_FORMAT = "%H:%M:%S"
CONNECTED_TIME_FORMAT = "%H%M%S"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATETIME_FORMAT_T = "%Y-%m-%dT%H:%M:%S"
DATETIME_FORMAT_TZ = "%Y-%m-%dT%H:%M:%SZ"
KST = timezone(timedelta(hours=9))
