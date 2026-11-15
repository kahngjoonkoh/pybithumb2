from pybithumb2.client import BithumbClient


def test_get_accounts(api_client: BithumbClient, raw_api_client: BithumbClient):
    response = api_client.get_accounts()
    raw_response = raw_api_client.get_accounts()

    assert len(response) == len(raw_response)
    assert len(response) > 0

    test_item = response[0]
    raw_test_item = raw_response[0]

    assert str(test_item.currency) == raw_test_item["currency"]
    assert str(test_item.unit_currency) == raw_test_item["unit_currency"]
