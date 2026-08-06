from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from urllib.parse import urlparse

from sybaritic.exceptions import InvalidURIError

DEFAULT_PORT = 300
DEFAULT_SCHEME = "spartan"


@dataclass(frozen=True)
class SpartanURI:
    """Represents a Spartan protocol URI.

    Attributes:
        host: The target hostname (or IP address).
        port: The target TCP port (defaults to 300).
        path: The target resource path (defaults to '/'). Must start with '/'.
        scheme: The URI scheme (defaults to 'spartan').
    """

    host: str
    port: int = DEFAULT_PORT
    path: str = "/"
    scheme: str = DEFAULT_SCHEME

    def __post_init__(self) -> None:
        if not self.host:
            raise InvalidURIError("Host cannot be empty")
        if not self.path.startswith("/"):
            raise InvalidURIError(f"Path must begin with '/', got '{self.path}'")
        if not (1 <= self.port <= 65535):
            raise InvalidURIError(f"Invalid port number: {self.port}")

    @property
    def punycode_host(self) -> str:
        """Return the host encoded in punycode for IDN compliance."""
        try:
            return self.host.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise InvalidURIError(f"Failed to convert host '{self.host}' to punycode") from exc

    @classmethod
    def parse(cls, uri_str: str | SpartanURI) -> SpartanURI:
        """Parse a URI string or return the SpartanURI instance as-is."""
        if isinstance(uri_str, SpartanURI):
            return uri_str

        uri_str = uri_str.strip()
        if not uri_str:
            raise InvalidURIError("Empty URI string")

        # Handle missing scheme (e.g., "example.com/foo")
        if "://" not in uri_str:
            uri_to_parse = f"{DEFAULT_SCHEME}://{uri_str}"
        else:
            uri_to_parse = uri_str

        parsed = urlparse(uri_to_parse)

        scheme = parsed.scheme.lower() if parsed.scheme else DEFAULT_SCHEME
        if scheme not in (DEFAULT_SCHEME, ""):
            # Allow spartan or missing scheme, but warn/fail if wrong scheme like http
            pass  # We accept spartan scheme

        if not parsed.hostname:
            raise InvalidURIError(f"Could not parse host from URI '{uri_str}'")

        host = parsed.hostname
        port = parsed.port if parsed.port is not None else DEFAULT_PORT
        path = parsed.path if parsed.path else "/"

        if parsed.query:
            # If query params exist, append them to path
            path = f"{path}?{parsed.query}"

        return cls(host=host, port=port, path=path, scheme=scheme)

    def resolve_redirect(self, target_path: str) -> SpartanURI:
        """Return a new SpartanURI for a redirect to target_path on the same host."""
        target = target_path.strip()
        if not target.startswith("/"):
            target = f"/{target}"
        return SpartanURI(
            host=self.host,
            port=self.port,
            path=target,
            scheme=self.scheme,
        )

    def __str__(self) -> str:
        if self.port == DEFAULT_PORT:
            return f"{self.scheme}://{self.host}{self.path}"
        return f"{self.scheme}://{self.host}:{self.port}{self.path}"
