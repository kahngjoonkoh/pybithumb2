import pytest

from pybithumb2.client import BithumbClient
from pybithumb2.models import WalletStatus
from pybithumb2.types import RawData


@pytest.mark.skip("Invalid access key?")
def test_get_wallet_status(api_client: BithumbClient, raw_api_client: BithumbClient):
    response = api_client.get_wallet_status()
    raw_response = raw_api_client.get_wallet_status()

    assert len(response) > 0

    test_item: WalletStatus = response[0]
    raw_test_item: RawData = raw_response[0]
    print(response.df())

    assert str(test_item.wallet_state) == raw_test_item["wallet_state"]
    assert str(test_item.block_state) == raw_test_item["block_state"]
