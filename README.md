# PyBithumb2
[![PyPI - Version](https://img.shields.io/pypi/v/pybithumb2.svg)](https://pypi.org/project/pybithumb2)
[![Python Versions](https://img.shields.io/pypi/pyversions/pybithumb2.svg)](https://www.python.org/downloads/)
[![Last Commit](https://img.shields.io/github/last-commit/kahngjoonkoh/pybithumb2)](https://github.com/CoderGamester/mcp-unity/commits/main)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
---
Bithumb API 2.0 wrapper for Python environments using Pydantic models and the python typing library to enhance developer experience.

## nNotes
I am currently using locals() to supply my parameters. Hence the param names where 1 to 1 matched with the API despite the API having slight unmatches. e.g. convertingPriceUnit
Design philosophy was to respect the developers and provide a 1 to 1 a close as possible?
The API could ahve a single datetime format? in get_trades() there are seperate fields for data and time.
v2.1.0
fUture update for 2.1.5
## Installation
`pip install pybithumb2`

## Credits
Alpaca-trading python SDK
Python-KIS