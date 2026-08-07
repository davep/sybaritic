from __future__ import annotations

from dataclasses import dataclass, field

from sybaritic.exceptions import ClientError, ServerError
from sybaritic.status import Status
from sybaritic.uri import SpartanURI


@dataclass
class Response:
    """Represents a response from a Spartan server.

    Attributes:
        uri: The final SpartanURI of the response.
        status: The response status code enum.
        meta: Metadata string from status line (MIME type, redirect path, or error message).
        content: Raw response body bytes.
        requested_uri: The originally requested SpartanURI (before redirects).
        history: List of intermediate Response objects leading to this response via redirects.
    """

    uri: SpartanURI
    status: Status
    meta: str
    content: bytes = b""
    requested_uri: SpartanURI | None = None
    history: list[Response] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.requested_uri is None:
            self.requested_uri = self.uri

    @property
    def is_success(self) -> bool:
        """Return True if response is status 2 (Success)."""
        return self.status.is_success

    @property
    def is_redirect(self) -> bool:
        """Return True if response is status 3 (Redirect)."""
        return self.status.is_redirect

    @property
    def is_client_error(self) -> bool:
        """Return True if response is status 4 (Client Error)."""
        return self.status.is_client_error

    @property
    def is_server_error(self) -> bool:
        """Return True if response is status 5 (Server Error)."""
        return self.status.is_server_error

    @property
    def is_error(self) -> bool:
        """Return True if response is status 4 or 5."""
        return self.status.is_error

    @property
    def is_redirected(self) -> bool:
        """Return True if this response is the result of following redirects."""
        return len(self.history) > 0

    @property
    def mime_type(self) -> str:
        """Return the MIME type for a successful response (without parameters)."""
        if not self.is_success or not self.meta:
            return ""
        return self.meta.split(";")[0].strip().lower()

    @property
    def encoding(self) -> str:
        """Return the character encoding extracted from MIME type parameters, defaulting to 'utf-8'."""
        if self.is_success and ";" in self.meta:
            parts = self.meta.split(";")[1:]
            for part in parts:
                kv = part.strip().split("=", 1)
                if len(kv) == 2 and kv[0].strip().lower() == "charset":
                    return kv[1].strip().strip('"').strip("'")
        return "utf-8"

    @property
    def charset(self) -> str:
        """Return the character encoding (alias for encoding)."""
        return self.encoding

    @property
    def text(self) -> str:
        """Return the response body decoded as a string using the response encoding."""
        enc = self.encoding
        try:
            return self.content.decode(enc)
        except (UnicodeDecodeError, LookupError):
            return self.content.decode("utf-8", errors="replace")

    @property
    def redirect_path(self) -> str | None:
        """Return the target redirect path if status is 3, otherwise None."""
        return self.meta if self.is_redirect else None

    @property
    def error_message(self) -> str | None:
        """Return the error message if status is 4 or 5, otherwise None."""
        return self.meta if self.is_error else None

    def raise_for_status(self) -> None:
        """Raise ClientError or ServerError if status code indicates an error."""
        if self.is_client_error:
            raise ClientError(self.meta, response=self)
        if self.is_server_error:
            raise ServerError(self.meta, response=self)

    def __repr__(self) -> str:
        return f"<Response [{self.status.value} {self.status.name}] uri='{self.uri}' meta='{self.meta}'>"
