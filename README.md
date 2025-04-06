# PyBithumb2
[![PyPI - Version](https://img.shields.io/pypi/v/pybithumb2.svg)](https://pypi.org/project/pybithumb2)
[![Python Versions](https://img.shields.io/pypi/pyversions/pybithumb2.svg)](https://www.python.org/downloads/)
[![Last Commit](https://img.shields.io/github/last-commit/kahngjoonkoh/pybithumb2)](https://github.com/CoderGamester/mcp-unity/commits/main)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
---
PyBithumb2 is a Python wrapper for Bithumb's API v2, designed to provide an intuitive and efficient interface for developers. By leveraging Pydantic models and Python's typing library, PyBithumb2 ensures data validation and enhances the development experience.

## Features
- ✅ Clean and intuitive interface
- 🔍 Pydantic models for response validation
- 📦 Lightweight and dependency-minimal
- 📊 Optional pandas DataFrame support for structured responses

## Installation
`pip install pybithumb2`

## Quick Start
```
from pybithumb2 import BithumbClient

# Get these from https://www.bithumb.com/react/api-support/management-api
client = BithumbClient(api_key="YOUR_API_KEY", secret_key="YOUR_SECRET_KEY")

# Get markets
markets = client.get_markets(isDetails=True)

for market in markets:
    print(f"{market.market}: {market.korean_name} ({market.english_name})")
```

## Contributing
Pull requests and issues are welcome!

There are currently many features and improvements planned. Here are some ideas you can help with:
- Support for Depositing and Withdrawing
- Add more pandas DataFrame outputs for endpoints
- Improve error handling and standardize exception formatting
- Improve docstrings and API documentation
- Add more unit tests for edge cases and error responses
- Support WebSocket endpoints for live trading data
- Create example notebooks or usage guides
- Update the API for v2.1.5 (beta)

To contribute:
1. Fork the repo
2. Create a new branch: `git checkout -b feature/my-feature`
3. Install dependencies and set up environment variables
4. Commit and push your changes
5. Open a pull request

Or, feel free to [open an issue](../../issues) for bugs, feature requests, or questions.

Please make sure your code is type-safe and tested. Thanks for helping improve PyBithumb2!

## Acknowledgements
PyBithumb2 was inspired by and built upon the foundations of several excellent Python SDKs:

- [`pybithumb`](https://github.com/sharebook-kr/pybithumb)
- [`Python-KIS`](https://github.com/sharebook-kr/python-kis)
- [`alpaca-trade-api-python`](https://github.com/alpacahq/alpaca-trade-api-python)

🔗 Also check out my related project: [`bithumb-mcp`](https://github.com/kahngjoonkoh/pybithumb-mcp)

## License
This project is licensed under the [MIT License](https://github.com/kahngjoonkoh/pybithumb2/blob/main/LICENSE). See the [LICENSE](https://github.com/kahngjoonkoh/pybithumb2/blob/main/LICENSE) file for more details.
