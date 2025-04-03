import jwt
import uuid
import time
import hashlib

from abc import ABC
from typing import Any, List, Optional, Union
from requests import Session, HTTPError
from urllib.parse import urlencode

from pybithumb2.types import HTTPResult
from pybithumb2.exceptions import RetryException, APIError


class RESTClient(ABC):
    def __init__(self, base_url: str, api_key: Optional[str] = None, secret_key: Optional[str] = None, use_raw_data: bool = False):
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
    ) -> HTTPResult:
        """Prepares and submits HTTP requests to given API endpoint and returns response.
        Handles retrying if 429 (Rate Limit) error arises.

        Args:
            method (str): The API endpoint HTTP method
            path (str): The API endpoint path
            data (Optional[Union[dict, str]]): Either the payload in json format, query params urlencoded, or a dict
             of values to be converted to appropriate format based on `method`. Defaults to None.

        Returns:
            HTTPResult: The response from the API
        """
        if is_private and not self._has_credentials:
            raise APIError("invalid_jwt")

        url: str = self._base_url + path
        query = urlencode(data) if data is not None else None

        headers = self._generate_headers(is_private, query)

        opts = {
            "headers": headers,
            "allow_redirects": False,
        }

        if method.upper() in ["GET", "DELETE"]:
            opts["params"] = data
        else:
            opts["json"] = data

        if query:
            print(f"{url}?{query}")
        else:
            print(url)

        response = self._session.request(method, url, **opts)
        try:
            response.raise_for_status()
        except HTTPError as http_error:
            error = response.text
            raise APIError(error, http_error)
        
        if response.text != "":
            return response.json()
        else: 
            raise APIError("Response is empty")


    # Query is the str after ?
    def _generate_headers(self, is_private: bool, query: Optional[str]) -> dict:
        if not is_private:
            return {"accept": "application/json"}
        # Generate access token
        payload = {
            'access_key': self._api_key,
            'nonce': str(uuid.uuid4()),
            'timestamp': round(time.time() * 1000)
        }
        if query:
            hash = hashlib.sha512()
            hash.update(query.encode())
            query_hash = hash.hexdigest()
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'

        jwt_token = jwt.encode(payload, self._secret_key)
        authorization_token = f"Bearer {jwt_token}"

        return {'Authorization': authorization_token}

    def get(
        self, path: str, is_private: bool, data: Optional[Union[dict, str]] = None
    ) -> HTTPResult:
        """Performs a single GET request

        Args:
            path (str): The API endpoint path
            data (Union[dict, str], optional): Query parameters to send, either
            as a str urlencoded, or a dict of values to be converted. Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("GET", path, is_private, data)

    def post(
        self, path: str, is_private: bool, data: Optional[Union[dict, List[dict]]] = None
    ) -> HTTPResult:
        """Performs a single POST request

        Args:
            path (str): The API endpoint path
            data (Optional[Union[dict, List[dict]]): The json payload as a dict of values to be converted.
             Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("POST", path, is_private, data)

    def put(self, path: str, is_private: bool, data: Optional[dict] = None) -> dict:
        """Performs a single PUT request

        Args:
            path (str): The API endpoint path
            data (Optional[dict]): The json payload as a dict of values to be converted.
             Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("PUT", path, is_private, data)

    def patch(self, path: str, is_private: bool, data: Optional[dict] = None) -> dict:
        """Performs a single PATCH request

        Args:
            path (str): The API endpoint path
            data (Optional[dict]): The json payload as a dict of values to be converted.
             Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("PATCH", path, is_private, data)

    def delete(self, path, is_private: bool, data: Optional[Union[dict, str]] = None) -> dict:
        """Performs a single DELETE request

        Args:
            path (str): The API endpoint path
            data (Union[dict, str], optional): The payload if any. Defaults to None.

        Returns:
            dict: The response
        """
        return self._request("DELETE", path, is_private, data)

