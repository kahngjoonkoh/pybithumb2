import pytest

from pybithumb2.client import BithumbClient
from pybithumb2.exceptions import APIError


def test_no_auth_creds():
    client = BithumbClient()
    with pytest.raises(APIError, match="invalid_jwt"):
        client.get_accounts()


def test_wrong_access_key(api_client: BithumbClient):
    client = BithumbClient("DUMMY_API_KEY", api_client._secret_key)
    with pytest.raises(APIError, match="invalid_access_key"):
        client.get_accounts()


def test_wrong_secret_key(api_client: BithumbClient):
    client = BithumbClient(api_client._api_key, "DUMMY_SECRET_KEY")
    with pytest.raises(APIError, match="jwt_verification"):
        client.get_accounts()
