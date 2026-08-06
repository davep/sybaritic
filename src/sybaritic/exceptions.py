from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sybaritic.response import Response


class SybariticError(Exception):
    """Base exception for all sybaritic errors."""


class URIError(SybariticError, ValueError):
    """Raised when a Spartan URI is invalid, unparsable, or has an invalid scheme."""


# Alias for backward compatibility
InvalidURIError = URIError


class SybariticConnectionError(SybariticError):
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


class StatusError(SybariticError):
    """Raised when a response status indicates an error (status 4 or 5)."""

    def __init__(self, message: str, response: Optional["Response"] = None) -> None:
        super().__init__(message)
        self.response = response


class ClientError(StatusError):
    """Raised when server returns a client error status (status 4)."""


class ServerError(StatusError):
    """Raised when server returns a server error status (status 5)."""
