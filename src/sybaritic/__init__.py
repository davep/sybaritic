"""Sybaritic: Async Spartan Protocol Client Library."""

__version__ = "0.1.0"

from sybaritic.client import Client
from sybaritic.exceptions import (
    ClientError,
    HeaderError,
    InvalidRedirectError,
    InvalidURIError,
    RedirectError,
    RedirectLoopError,
    RequestError,
    ResponseError,
    ServerError,
    StatusError,
    SybariticConnectionError,
    SybariticError,
    TooManyRedirectsError,
    URIError,
)
from sybaritic.response import Response
from sybaritic.status import Status
from sybaritic.uri import DEFAULT_PORT, DEFAULT_SCHEME, SpartanURI

__all__ = [
    "DEFAULT_PORT",
    "DEFAULT_SCHEME",
    "Client",
    "ClientError",
    "HeaderError",
    "InvalidRedirectError",
    "InvalidURIError",
    "RedirectError",
    "RedirectLoopError",
    "RequestError",
    "ResponseError",
    "Response",
    "ServerError",
    "SpartanURI",
    "Status",
    "StatusError",
    "SybariticConnectionError",
    "SybariticError",
    "TooManyRedirectsError",
    "URIError",
    "__version__",
]

