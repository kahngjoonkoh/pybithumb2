from datetime import timezone, timedelta

"""The Bithumb API uses two multiple datetime formats."""
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATETIME_FORMAT_T = "%Y-%m-%dT%H:%M:%S"
DATETIME_FORMAT_TZ = "%Y-%m-%dT%H:%M:%SZ"
KST = timezone(timedelta(hours=9))
