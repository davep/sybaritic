"""Spartan protocol response status codes."""

from enum import IntEnum


class Status(IntEnum):
    """Spartan response status codes."""

    SUCCESS = 2
    """Indicates that the resource was successfully received, understood, and accepted."""

    REDIRECT = 3
    """Indicates that the resource is located at a different location on the same host."""

    CLIENT_ERROR = 4
    """Indicates that the request contains bad syntax or cannot be fulfilled."""

    SERVER_ERROR = 5
    """Indicates that the server is unable to fulfill an otherwise valid request."""

    @property
    def is_success(self) -> bool:
        """Return True if status code indicates success."""
        return self == Status.SUCCESS

    @property
    def is_redirect(self) -> bool:
        """Return True if status code indicates a redirect."""
        return self == Status.REDIRECT

    @property
    def is_client_error(self) -> bool:
        """Return True if status code indicates a client error."""
        return self == Status.CLIENT_ERROR

    @property
    def is_server_error(self) -> bool:
        """Return True if status code indicates a server error."""
        return self == Status.SERVER_ERROR

    @property
    def is_error(self) -> bool:
        """Return True if status code indicates a client or server error."""
        return self in (Status.CLIENT_ERROR, Status.SERVER_ERROR)
