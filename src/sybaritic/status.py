from enum import IntEnum


class Status(IntEnum):
    """Spartan response status codes."""

    SUCCESS = 2
    REDIRECT = 3
    CLIENT_ERROR = 4
    SERVER_ERROR = 5

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
