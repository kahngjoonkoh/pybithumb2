import json
import jwt
import uuid
import time
import hashlib

from abc import ABC
from typing import List, Optional, Union
from requests import Session, HTTPError
from urllib.parse import quote

from pybithumb2.__env__ import USER_AGENT
from pybithumb2.types import HTTPResult
from pybithumb2.exceptions import APIError


def build_query(data: dict, encode: bool = False) -> str:
    """
    Serialises parameters the way the Bithumb API signs and parses them.

    Lists become `key[]=v` and lists of dicts become `key[i][sub]=v`. With `encode=False` the
    result is the unencoded string whose SHA512 is the JWT `query_hash`; with `encode=True` it
    is the percent-encoded string sent on the URL.
    """

    def text(v) -> str:
        return ("true" if v else "false") if isinstance(v, bool) else str(v)

    q = (lambda v: quote(text(v), safe="")) if encode else text
    parts = []
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    parts += [
                        f"{q(key)}[{i}][{q(k)}]={q(v)}"
                        for k, v in item.items()
                        if v is not None
                    ]
                else:
                    parts.append(f"{q(key)}[]={q(item)}")
        else:
            parts.append(f"{q(key)}={q(value)}")
    return "&".join(parts)


def _http_error(response) -> Optional[HTTPError]:
    try:
        response.raise_for_status()
    except HTTPError as e:
        return e
    return None


class RESTClient(ABC):
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        use_raw_data: bool = False,
    ):
        self._base_url = base_url
        self._api_key = api_key
        self._secret_key = secret_key
        self._has_credentials = bool(self._api_key and self._secret_key)
        self._use_raw_data = use_raw_data
        self._session: Session = Session()

    def _request(
        self,
        method: str,
        path: str,
        is_private: bool,
        data: Optional[dict] = None,
        doseq: bool = False,
    ) -> HTTPResult:
        """
        Prepares and submits HTTP requests to given API endpoint and returns response.

        GET and DELETE send `data` as the query string; other methods send it as a JSON body.
        Private requests are signed with a JWT whose `query_hash` is the SHA512 of the
        unencoded `key=value&...` form of the same data, as the API requires.

        Args:
            method (str): The API endpoint HTTP method
            path (str): The API endpoint path
            is_private (bool): Whether the request should use authentication headers.
            data (dict, optional): Query parameters or JSON body. Lists become `key[]=v`.
            doseq (bool): Kept for backwards compatibility; lists are always expanded.

        Returns:
            HTTPResult: The response from the API
        """
        if is_private and not self._has_credentials:
            raise APIError(
                {
                    "name": "invalid_jwt",
                    "message": "API key and secret key are required",
                }
            )

        data = data or None
        in_query = method.upper() in ("GET", "DELETE")
        url = path if path.startswith("https://") else self._base_url + path
        if in_query and data:
            url += "?" + build_query(data, encode=True)

        headers = self._generate_headers(
            is_private, build_query(data) if data else None
        )
        body = None
        if not in_query and data is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(data, default=str)

        response = self._session.request(
            method, url, headers=headers, data=body, allow_redirects=False
        )

        try:
            obj = response.json() if response.text else None
        except ValueError:
            obj = None

        if isinstance(obj, dict) and "error" in obj:
            # Bithumb returns {"error": {"name", "message"}}, sometimes with a 2xx status.
            raise APIError(obj["error"], _http_error(response))
        if response.is_redirect:
            # never follow: a redirect would resend the Authorization header elsewhere
            raise APIError(
                f"unexpected redirect ({response.status_code}) to {response.headers.get('location')}"
            )
        try:
            response.raise_for_status()
        except HTTPError as http_error:
            raise APIError(response.text, http_error)
        if obj is None:
            raise APIError("Response is empty")
        return obj

    def _generate_headers(self, is_private: bool, query: Optional[str]) -> dict:
        """
        Generates the appropriate HTTP headers for the API request.

        Args:
            is_private (bool): Whether the request requires authentication.
            query (str, optional): The unencoded `key=value&...` string of the request's parameters
                or body. Its SHA512 goes into the JWT payload as `query_hash`.

        Returns:
            dict: A dictionary containing HTTP headers, including Authorization if private.
        """
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        if not is_private:
            return headers
        payload = {
            "access_key": self._api_key,
            "nonce": str(uuid.uuid4()),
            "timestamp": round(time.time() * 1000),
        }
        if query:
            payload["query_hash"] = hashlib.sha512(query.encode()).hexdigest()
            payload["query_hash_alg"] = "SHA512"

        jwt_token = jwt.encode(payload, self._secret_key, algorithm="HS256")
        headers["Authorization"] = f"Bearer {jwt_token}"
        return headers

    def get(
        self,
        path: str,
        is_private: bool,
        data: Optional[Union[dict, str]] = None,
        doseq: bool = False,
    ) -> HTTPResult:
        """
        Performs a single GET request

        Args:
            path (str): The API endpoint path
            is_private (bool): Whether the request should use authentication headers.
            data (Union[dict, str], optional): Query parameters to send. Defaults to None.
            doseq (bool): Whether list should be expanded into multiple parameters. Defaults to False.

        Returns:
            dict: The response
        """
        return self._request("GET", path, is_private, data, doseq)

    def post(
        self,
        path: str,
        is_private: bool,
        data: Optional[Union[dict, List[dict]]] = None,
        doseq: bool = False,
    ) -> HTTPResult:
        """
        Performs a single POST request

        Args:
            path (str): The API endpoint path
            is_private (bool): Whether the request should use authentication headers.
            data (Union[dict, str], optional): The json payload as a dict of values to be converted. Defaults to None.
            doseq (bool): Whether list should be expanded into multiple parameters. Defaults to False.

        Returns:
            dict: The response
        """
        return self._request("POST", path, is_private, data, doseq)

    def put(
        self,
        path: str,
        is_private: bool,
        data: Optional[dict] = None,
        doseq: bool = False,
    ) -> dict:
        """
        Performs a single PUT request

        Args:
            path (str): The API endpoint path
            is_private (bool): Whether the request should use authentication headers.
            data (Union[dict, str], optional): The json payload as a dict of values to be converted. Defaults to None.
            doseq (bool): Whether list should be expanded into multiple parameters. Defaults to False.

        Returns:
            dict: The response
        """
        return self._request("PUT", path, is_private, data, doseq)

    def patch(
        self,
        path: str,
        is_private: bool,
        data: Optional[dict] = None,
        doseq: bool = False,
    ) -> dict:
        """
        Performs a single PATCH request

        Args:
            path (str): The API endpoint path
            is_private (bool): Whether the request should use authentication headers.
            data (Union[dict, str], optional): The json payload as a dict of values to be converted. Defaults to None.
            doseq (bool): Whether list should be expanded into multiple parameters. Defaults to False.

        Returns:
            dict: The response
        """
        return self._request("PATCH", path, is_private, data, doseq)

    def delete(
        self,
        path,
        is_private: bool,
        data: Optional[Union[dict, str]] = None,
        doseq: bool = False,
    ) -> dict:
        """
        Performs a single DELETE request

        Args:
            path (str): The API endpoint path
            is_private (bool): Whether the request should use authentication headers.
            data (Union[dict, str], optional): Query parameters to send. Defaults to None.
            doseq (bool): Whether list should be expanded into multiple parameters. Defaults to False.

        Returns:
            dict: The response
        """
        return self._request("DELETE", path, is_private, data, doseq)
