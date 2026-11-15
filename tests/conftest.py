"""
Offline test harness: a fake transport mounted on the client's requests Session.

Requests are fully prepared by `requests` (URL, body, headers), so tests see the exact bytes
that would go to Bithumb, and responses come from the API reference examples in
fixtures/examples.json.
"""

import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

import jwt
import pytest
from requests import Response
from requests.adapters import BaseAdapter

from pybithumb2 import BithumbClient

API_KEY = "test-access-key"
SECRET = "test-secret-key-0123456789abcdef!"
EXAMPLES = json.loads(
    (Path(__file__).parent / "fixtures" / "examples.json").read_text()
)


class FakeTransport(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.requests = []
        self.replies = []
        self.next_headers = {}

    def reply(self, body, status=200):
        self.replies.append((body, status))

    def send(self, request, **kwargs):
        self.requests.append(request)
        body, status = self.replies.pop(0) if self.replies else ({}, 200)
        response = Response()
        response.status_code = status
        response._content = (
            body if isinstance(body, str) else json.dumps(body)
        ).encode()
        response.request = request
        response.url = request.url
        response.headers.update(self.next_headers)
        self.next_headers = {}
        return response

    def close(self):
        pass


class Fake:
    def __init__(self, transport, client, raw_client, public_client):
        self.transport = transport
        self.client = client
        self.raw = raw_client
        self.public = public_client

    def reply(self, body, status=200):
        self.transport.reply(body, status)
        return self

    def example(self, key):
        return self.reply(EXAMPLES[key])

    @property
    def last(self):
        return self.transport.requests[-1]

    @property
    def path(self) -> str:
        return urlsplit(self.last.url).path

    @property
    def raw_query(self) -> str:
        """The query string as sent, still percent-encoded."""
        return urlsplit(self.last.url).query

    @property
    def query(self) -> str:
        """The decoded query string: the form whose SHA512 is signed."""
        return unquote(self.raw_query)

    @property
    def body(self):
        return json.loads(self.last.body) if self.last.body else None

    def claims(self) -> dict:
        """The JWT payload, verified against the secret (raises if the signature is wrong)."""
        auth = self.last.headers["Authorization"]
        assert auth.startswith("Bearer ")
        return jwt.decode(auth[len("Bearer ") :], SECRET, algorithms=["HS256"])

    def assert_signed(self, signed_string: str):
        claims = self.claims()
        assert claims["access_key"] == API_KEY
        assert claims["query_hash_alg"] == "SHA512"
        assert (
            claims["query_hash"] == hashlib.sha512(signed_string.encode()).hexdigest()
        )


@pytest.fixture
def fake():
    transport = FakeTransport()
    clients = [
        BithumbClient(API_KEY, SECRET),
        BithumbClient(API_KEY, SECRET, use_raw_data=True),
        BithumbClient(),
    ]
    for c in clients:
        c._session.mount("https://", transport)
    return Fake(transport, *clients)
