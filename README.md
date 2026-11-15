# PyBithumb2
[![PyPI - Version](https://img.shields.io/pypi/v/pybithumb2.svg)](https://pypi.org/project/pybithumb2)
[![Python Versions](https://img.shields.io/pypi/pyversions/pybithumb2.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/kahngjoonkoh/pybithumb2/actions/workflows/tests.yml/badge.svg)](https://github.com/kahngjoonkoh/pybithumb2/actions/workflows/tests.yml)
[![Last Commit](https://img.shields.io/github/last-commit/kahngjoonkoh/pybithumb2)](https://github.com/kahngjoonkoh/pybithumb2/commits/main)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
---
PyBithumb2 is a typed Python client for the [Bithumb API](https://apidocs.bithumb.com/) (the JWT-based API at `api.bithumb.com`). Every response is a Pydantic model with `Decimal` prices, `datetime` timestamps and enums, instead of a raw dict.

## Features
- ✅ Every REST endpoint in the Bithumb API reference: market data, orders (including v2, batch and TWAP), deposits and withdrawals
- 🔍 Pydantic models for every response, with `Decimal` for money
- 🛡️ Orders checked before sending (required price/volume per order type, `time_in_force`, `client_order_id` format)
- 📦 Small: `requests`, `pydantic`, `PyJWT`, `python-dateutil`
- 📊 Optional pandas: `.df()` on any model or list of models
- 🧪 Offline tests for every endpoint against the API reference's own example responses

## Installation
```
pip install pybithumb2            # or pybithumb2[pandas] for .df()
```
PyPI has 1.0.0b0. Until 1.0.0b1 is released there, install it from GitHub:
`pip install "pybithumb2 @ git+https://github.com/kahngjoonkoh/pybithumb2"`.

## Quick Start
```python
from decimal import Decimal
from pybithumb2 import BithumbClient, MarketID, OrderType, TradeSide, TimeInForce

# Keys from https://www.bithumb.com/react/api-support/management-api
client = BithumbClient(api_key="YOUR_API_KEY", secret_key="YOUR_SECRET_KEY")
btc = MarketID.from_string("KRW-BTC")

ticker = client.get_snapshots([btc])[0]
print(ticker.trade_price, ticker.signed_change_rate)

candles = client.get_day_candles(btc, count=30).df()   # needs pandas

order = client.submit_order(
    btc, TradeSide.BID, volume=Decimal("0.001"), price=Decimal("50000000"),
    ord_type=OrderType.LIMIT, client_order_id="my-order-1", time_in_force=TimeInForce.POST_ONLY,
)
client.cancel_order(order.order_id)                    # cancelling is asynchronous
open_orders = client.get_pending_orders(btc).data
```

Pass `use_raw_data=True` to get the API's JSON back unchanged. Errors raise `APIError` with Bithumb's `name` (e.g. `order_not_found`), `message` and the HTTP `status_code`.

## API coverage
| Area | Methods |
|---|---|
| Market data | `get_markets`, `get_minute_candles`, `get_day_candles`, `get_week_candles`, `get_month_candles`, `get_trades`, `get_snapshots`, `get_orderbooks`, `get_warning_markets`, `get_notices`, `get_fees` |
| Account | `get_accounts`, `get_order_available`, `get_wallet_status`, `get_api_keys` |
| Orders | `submit_order`, `submit_orders` (batch), `cancel_order`, `cancel_orders` (batch), `get_order_info`, `get_orders`, `search_orders`, `get_pending_orders`, `get_closed_orders` |
| TWAP | `submit_twap_order`, `get_twap_orders`, `cancel_twap_order` |
| Deposits | `get_deposit`, `get_deposits`, `get_krw_deposits`, `deposit_krw`, `generate_deposit_address`, `get_deposit_address`, `get_deposit_addresses` |
| Withdrawals | `get_withdraw_chance`, `get_withdrawal`, `get_withdrawals`, `get_krw_withdrawals`, `withdraw_coin`, `withdraw_krw`, `cancel_withdrawal`, `get_withdraw_addresses` |

Not yet: the WebSocket API (`ticker`, `trade`, `orderbook`, `myOrder`, `myAsset`), and client-side rate limiting.

## Changes in 1.0.0b1
Bithumb moved placing and cancelling orders to `/v2`. To follow it:
- `submit_order` now returns `OrderCreated` (`order_id`, not `uuid`) and also takes `client_order_id` and `time_in_force`.
- `cancel_order` returns `OrderCancelled` and can cancel by `client_order_id`.
- `get_order_info` returns one `OrderInfo` (it called the list endpoint before).
- `get_notices` calls `feed-api.bithumb.com`, where Bithumb now serves notices. The client never follows redirects, so that its `Authorization` header can't be sent to another host.

Fixed: `get_month_candles` returned weekly candles; orders with `Decimal` volume or price failed to send; list parameters such as `uuids` are now sent as `uuids[]=…` and signed over the unencoded query, as the API reference specifies; reading an empty optional field raised `AttributeError`; `APIError.code` raised on Bithumb's error format; `from pybithumb2 import *` failed. `pytest` and `python-dotenv` are no longer installed as runtime dependencies.

## Development
```
pip install -e ".[dev]"
pytest                                   # offline: a fake transport and the API reference's examples
```
The tests check the exact request sent (path, query string, JSON body) and verify each JWT signature and `query_hash`. The tests in `tests/live` call the real API and skip themselves unless `API_KEY_ID` and `API_SECRET_KEY` are set (from the environment or `.env`); the one that places a real order also needs `PYBITHUMB2_LIVE_ORDERS=1`.

## Contributing
Pull requests and issues are welcome!

Ideas you can help with:
- WebSocket support for live market data and private order/asset streams
- Client-side rate limiting
- Example notebooks or usage guides

To contribute:
1. Fork the repo
2. Create a new branch: `git checkout -b feature/my-feature`
3. Install with `pip install -e ".[dev]"` and run `pytest`
4. Commit and push your changes
5. Open a pull request

Or, feel free to [open an issue](../../issues) for bugs, feature requests, or questions.

Please make sure your code is type-safe and tested. Thanks for helping improve PyBithumb2!

## Acknowledgements
PyBithumb2 was inspired by and built upon the foundations of several excellent Python SDKs:

- [`pybithumb`](https://github.com/sharebook-kr/pybithumb)
- [`Python-KIS`](https://github.com/sharebook-kr/python-kis)
- [`alpaca-trade-api-python`](https://github.com/alpacahq/alpaca-trade-api-python)

🔗 Also check out my related project: [`bithumb-mcp`](https://github.com/kahngjoonkoh/bithumb-mcp), an MCP server built on this library.

## License
This project is licensed under the [MIT License](https://github.com/kahngjoonkoh/pybithumb2/blob/main/LICENSE). See the [LICENSE](https://github.com/kahngjoonkoh/pybithumb2/blob/main/LICENSE) file for more details.
