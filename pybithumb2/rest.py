import jwt
import uuid
import time
import hashlib

from abc import ABC
from typing import List, Optional, Union
from requests import Session, HTTPError
from urllib.parse import urlencode

from pybithumb2.types import HTTPResult
from pybithumb2.exceptions import APIError


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
        data: Optional[Union[dict, str]] = None,
        doseq: bool = False,
    ) -> HTTPResult:
        """
        Prepares and submits HTTP requests to given API endpoint and returns response.

        Args:
            method (str): The API endpoint HTTP method
            is_private (bool): Whether the request should use authentication headers.
            path (str): The API endpoint path
            data (Union[dict, str], optional): Either the payload in json format, query params urlencoded, or a dict
             of values to be converted to appropriate format based on `method`. Defaults to None.
            doseq (bool): Whether list should be expanded into multiple parameters. Defaults to False.

        Returns:
            HTTPResult: The response from the API
        """
        if is_private and not self._has_credentials:
            raise APIError("invalid_jwt")

        url: str = self._base_url + path
        query = urlencode(data, doseq) if data is not None else None

        headers = self._generate_headers(is_private, query)

        opts = {
            "headers": headers,
            "allow_redirects": False,
        }

        if method.upper() in ["GET", "DELETE"]:
            opts["params"] = data
        else:
            opts["json"] = data

        # if query:
        #     print(f"{url}?{query}")
        # else:
        #     print(url)

        response = self._session.request(method, url, **opts)

        try:
            response.raise_for_status()
        except HTTPError as http_error:
            error = response.text
            raise APIError(error, http_error)

        if response.text != "":
            obj = response.json()
            if "error" in obj:
                """Sometimes the response is an error but with a success status code."""
                raise APIError(obj["error"])
            return obj
        else:
            raise APIError("Response is empty")

    def _generate_headers(self, is_private: bool, query: Optional[str]) -> dict:
        """
        Generates the appropriate HTTP headers for the API request.

        Args:
            is_private (bool): Whether the request requires authentication.
            query (str, optional): The query string (the part after '?') used in the request. Required to generate
                query hash for authenticated private requests.

        Returns:
            dict: A dictionary containing HTTP headers, including Authorization if private.
        """
        if not is_private:
            return {"accept": "application/json"}
        # Generate access token
        payload = {
            "access_key": self._api_key,
            "nonce": str(uuid.uuid4()),
            "timestamp": round(time.time() * 1000),
        }
        if query:
            hash = hashlib.sha512()
            hash.update(query.encode())
            query_hash = hash.hexdigest()
            payload["query_hash"] = query_hash
            payload["query_hash_alg"] = "SHA512"

        jwt_token = jwt.encode(payload, self._secret_key)
        authorization_token = f"Bearer {jwt_token}"

        return {"Authorization": authorization_token}

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
