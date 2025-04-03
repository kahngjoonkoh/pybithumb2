import sys

API_BASE_URL = "https://api.bithumb.com"

VERSION = "{{VERSION_PLACEHOLDER}}"  # This is automatically set via a tag in GitHub Workflow.
VERSION = "25+dev" if "VERSION_PLACEHOLDER" in VERSION else VERSION

USER_AGENT = f"pybithumb2/{VERSION}"

__package_name__ = "pybithumb2"
__version__ = VERSION
__author__ = "kahngjoonkoh"
__author_email__ = "kahngjoonk@gmail.com"
__url__ = "https://github.com/kahngjoonkoh/pybithumb2"
__license__ = "MIT"

# if sys.version_info < (3, 10):
#     raise RuntimeError(f"Pybithumb2 requires Python 3.10+ (Current: {sys.version})")
