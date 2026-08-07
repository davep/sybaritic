"""Exceptions for the Sybaritic Spartan client library."""


class SybariticError(Exception):
    """Base exception for all sybaritic errors."""


class URIError(SybariticError):
    """Raised when a Spartan URI is invalid, unparsable, or has an invalid scheme."""


class ConnectionError(SybariticError):
    """Raised when a network connection to a Spartan server fails."""


class ResponseError(SybariticError):
    """Raised when a response is malformed or invalid."""


class HeaderError(ResponseError):
    """Raised when the response header status line cannot be parsed."""


class RedirectError(SybariticError):
    """Base exception for redirect issues."""


class TooManyRedirectsError(RedirectError):
    """Raised when the maximum redirect threshold is exceeded."""


class RedirectLoopError(RedirectError):
    """Raised when a redirect loop is detected."""


class InvalidRedirectError(RedirectError):
    """Raised when a redirect path is invalid (e.g. not starting with '/')."""


class RequestError(SybariticError):
    """Raised when sending a request fails."""


### exceptions.py ends here
