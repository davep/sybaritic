"""Sybaritic: Async Spartan Protocol Client Library."""

__version__ = "0.1.0"

from sybaritic.client import Client, get, post, request
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
from sybaritic.uri import (
    SPARTAN_DEFAULT_PORT,
    SPARTAN_MAXIMUM_LENGTH,
    SPARTAN_PREFIX,
    SPARTAN_SCHEME,
    SpartanURI,
)

__all__ = [
    "SPARTAN_DEFAULT_PORT",
    "SPARTAN_MAXIMUM_LENGTH",
    "SPARTAN_PREFIX",
    "SPARTAN_SCHEME",
    "Client",
    "ClientError",
    "HeaderError",
    "InvalidRedirectError",
    "InvalidURIError",
    "RedirectError",
    "RedirectLoopError",
    "RequestError",
    "Response",
    "ResponseError",
    "ServerError",
    "SpartanURI",
    "Status",
    "StatusError",
    "SybariticConnectionError",
    "SybariticError",
    "TooManyRedirectsError",
    "URIError",
    "__version__",
    "get",
    "post",
    "request",
]
