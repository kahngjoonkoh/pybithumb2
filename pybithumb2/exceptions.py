import json
from typing import Optional, Union


class APIError(Exception):
    """
    An error from the Bithumb API, or a request refused before it was sent.

    `name` is Bithumb's error code (e.g. "invalid_jwt", "order_not_found"), `message` its text,
    and `status_code` the HTTP status when there was a response.
    """

    def __init__(self, error: Union[dict, str], http_error=None):
        self._error = error
        self._http_error = http_error
        self.name, self.message = self._parse(error)
        super().__init__(f"{self.name}: {self.message}" if self.message else self.name)

    @staticmethod
    def _parse(error: Union[dict, str]) -> "tuple[str, Optional[str]]":
        if isinstance(error, str):
            try:
                error = json.loads(error)
            except ValueError:
                return error, None
        if isinstance(error, dict):
            error = error.get("error", error)
            if isinstance(error, dict):
                return str(error.get("name") or error.get("code") or ""), error.get(
                    "message"
                )
        return str(error), None

    @property
    def code(self) -> str:
        """Alias of `name`, kept for backwards compatibility."""
        return self.name

    @property
    def status_code(self):
        http_error = self._http_error
        if http_error is not None and hasattr(http_error, "response"):
            return http_error.response.status_code

    @property
    def request(self):
        if self._http_error is not None:
            return self._http_error.request

    @property
    def response(self):
        if self._http_error is not None:
            return self._http_error.response
