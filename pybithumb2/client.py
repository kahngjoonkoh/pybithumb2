from typing import List, Optional, Union

from pybithumb2.__env__ import API_BASE_URL
from pybithumb2.types import RawData
from pybithumb2.models import (
    Account,
    MarketInfo,
    WarningMarketInfo,
    clean_and_format_data,
)
from pybithumb2.rest import RESTClient


class BithumbClient(RESTClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        use_raw_data: bool = False,
    ) -> None:
        """Instantiates the Bithumb Client.
        If either key is missing, then the client will only have access to the public API.

        Args:
            api_key (Optional[str]): The API key for the client.
            secret_key (Optional[str]): The secret key for the client.
            use_raw_data (bool): Whether the API response is returned as raw data or in pydantic models.
        """
        super().__init__(API_BASE_URL, api_key, secret_key, use_raw_data)

    # ##### Public API features #####
    def get_markets(self, isDetails: bool = False) -> Union[List[MarketInfo], RawData]:
        data = locals().copy()
        data.pop("self")
        data = clean_and_format_data(data)

        response = self.get(f"/v1/market/all", is_private=False, data=data)

        if self._use_raw_data:
            return response

        return [MarketInfo.model_validate(item) for item in response]

    def get_warning_markets(self) -> Union[List[WarningMarketInfo], RawData]:
        response = self.get(f"/v1/market/virtual_asset_warning", is_private=False)

        if self._use_raw_data:
            return response

        return [WarningMarketInfo.model_validate(item) for item in response]

    # ##### Private API features #####
    def get_accounts(self) -> Union[List[Account], RawData]:
        response = self.get(f"/v1/accounts", is_private=True)

        if self._use_raw_data:
            return response

        return [Account.model_validate(item) for item in response]
