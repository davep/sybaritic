"""Sybaritic: Async Spartan Protocol Client Library."""

##############################################################################
# Python imports.
from importlib.metadata import version

##############################################################################
# Main library information.
__author__ = "Dave Pearson"
__copyright__ = "Copyright 2026, Dave Pearson"
__credits__ = ["Dave Pearson"]
__maintainer__ = "Dave Pearson"
__email__ = "davep@davep.org"
__version__: str = version("sybaritic")
__licence__ = "MIT"

##############################################################################
# Local imports.
from sybaritic.client import Client, get, post, request
from sybaritic.exceptions import (
    ConnectionError,
    HeaderError,
    InvalidRedirectError,
    RedirectError,
    RedirectLoopError,
    RequestError,
    ResponseError,
    SybariticError,
    TooManyRedirectsError,
    URIError,
)
from sybaritic.response import Response
from sybaritic.status import Status
from sybaritic.uri import (
    SPARTAN_DEFAULT_PORT,
    SPARTAN_PREFIX,
    SPARTAN_SCHEME,
    SpartanURI,
)

##############################################################################
# Exports.
__all__ = [
    "__version__",
    "Client",
    "get",
    "HeaderError",
    "InvalidRedirectError",
    "post",
    "RedirectError",
    "RedirectLoopError",
    "request",
    "RequestError",
    "Response",
    "ResponseError",
    "SPARTAN_DEFAULT_PORT",
    "SPARTAN_PREFIX",
    "SPARTAN_SCHEME",
    "SpartanURI",
    "Status",
    "ConnectionError",
    "SybariticError",
    "TooManyRedirectsError",
    "URIError",
]

### __init__.py ends here
