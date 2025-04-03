import pytest

from pybithumb2.client import BithumbClient
from pybithumb2.exceptions import APIError


def test_no_auth_creds():
    client = BithumbClient()
    with pytest.raises(APIError, match="invalid_jwt"):
        client.get_accounts()


def test_wrong_access_key(api_client: BithumbClient):
    api_client._api_key = "DUMMY_API_KEY"
    with pytest.raises(APIError, match="invalid_access_key"):
        api_client.get_accounts()


def test_wrong_secret_key(api_client: BithumbClient):
    api_client._secret_key = "DUMMY_SECRET_KEY"
    with pytest.raises(APIError, match="invalid_access_key"):
        api_client.get_accounts()
