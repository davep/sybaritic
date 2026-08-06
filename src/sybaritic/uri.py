from __future__ import annotations

from typing import Final
from urllib.parse import urlparse

from sybaritic.exceptions import URIError

SPARTAN_SCHEME: Final[str] = "spartan"
"""The default URL scheme for the Spartan protocol."""

SPARTAN_PREFIX: Final[str] = f"{SPARTAN_SCHEME}://"
"""The standard prefix for Spartan URIs."""

SPARTAN_DEFAULT_PORT: Final[int] = 300
"""The default TCP network port for the Spartan protocol."""

# Aliases for convenience
DEFAULT_PORT: Final[int] = SPARTAN_DEFAULT_PORT
DEFAULT_SCHEME: Final[str] = SPARTAN_SCHEME
MAXIMUM_LENGTH: Final[int] = 1024
"""The maximum length of a Spartan URI in bytes."""


class _UnsetType:
    """Sentinel class to distinguish between omitted arguments and None."""


_UNSET: Final[_UnsetType] = _UnsetType()


def _normalise_scheme(uri: str) -> str:
    """Normalise the scheme portion of a URI to lowercase."""
    scheme, separator, rest = uri.partition("://")
    return f"{scheme.lower()}{separator}{rest}" if separator else uri


class SpartanURI:
    """Represents a validated Spartan protocol URI."""

    MAXIMUM_LENGTH: Final[int] = MAXIMUM_LENGTH
    """The maximum length of a Spartan URI in bytes."""

    def __init__(
        self,
        uri: str | SpartanURI,
        *,
        host: str | None = None,
        port: int | None = None,
        path: str | None = None,
        scheme: str | None = None,
    ) -> None:
        """Initialise and validate a Spartan URI.

        Args:
            uri: The raw URI string or an existing SpartanURI to clone.
            host: Optional host override.
            port: Optional port override.
            path: Optional path override.
            scheme: Optional scheme override.

        Raises:
            URIError: If the URI is empty, scheme is missing or not 'spartan',
                host is missing, or URI parsing fails.
        """
        if isinstance(uri, SpartanURI):
            self._scheme = scheme or uri.scheme
            self._host = host if host is not None else uri.host
            self._port = port if port is not None else uri.port
            self._path = path if path is not None else uri.path
            self._query = uri.query
        else:
            cleaned = uri.strip()
            if not cleaned:
                raise URIError("URI cannot be empty")

            normalised = _normalise_scheme(cleaned)

            if "://" in normalised:
                raw_scheme, _, _ = normalised.partition("://")
                if not raw_scheme:
                    raise URIError("URI scheme cannot be empty")
                if raw_scheme != SPARTAN_SCHEME:
                    raise URIError(
                        f"Invalid URI scheme '{raw_scheme}', expected '{SPARTAN_SCHEME}'"
                    )
                to_parse = normalised
            else:
                to_parse = f"{SPARTAN_PREFIX}{normalised}"

            parsed = urlparse(to_parse)

            extracted_scheme = (
                parsed.scheme.lower() if parsed.scheme else SPARTAN_SCHEME
            )
            if extracted_scheme != SPARTAN_SCHEME:
                raise URIError(
                    f"Invalid URI scheme '{extracted_scheme}', expected '{SPARTAN_SCHEME}'"
                )

            if not parsed.hostname:
                raise URIError("URI must contain a valid host")

            try:
                extracted_port = parsed.port
            except ValueError as exc:
                raise URIError(f"Invalid port in URI: {exc}") from exc

            self._scheme = SPARTAN_SCHEME
            self._host = host if host is not None else parsed.hostname
            self._port = (
                port
                if port is not None
                else (
                    extracted_port
                    if extracted_port is not None
                    else SPARTAN_DEFAULT_PORT
                )
            )

            raw_path = (
                path if path is not None else (parsed.path if parsed.path else "/")
            )
            if not raw_path.startswith("/"):
                raw_path = f"/{raw_path}"
            self._path = raw_path
            self._query = parsed.query if parsed.query else None

        if not self._host:
            raise URIError("Host cannot be empty")
        if not (1 <= self._port <= 65535):
            raise URIError(f"Invalid port number: {self._port}")

    @property
    def scheme(self) -> str:
        """The scheme portion of the URI (always 'spartan')."""
        return self._scheme

    @property
    def host(self) -> str:
        """The target hostname or IP address."""
        return self._host

    @property
    def hostname(self) -> str:
        """The target hostname or IP address (alias for host)."""
        return self._host

    @property
    def port(self) -> int:
        """The target port number, defaulting to 300."""
        return self._port

    @property
    def path(self) -> str:
        """The path portion of the URI, starting with '/'."""
        return self._path

    @property
    def query(self) -> str | None:
        """The query string portion of the URI, or None."""
        return self._query

    @property
    def netloc(self) -> str:
        """Return the network location portion ('host' or 'host:port' if non-default)."""
        if self._port == SPARTAN_DEFAULT_PORT:
            return self._host
        return f"{self._host}:{self._port}"

    @property
    def punycode_host(self) -> str:
        """Return the host encoded in punycode for IDN compliance."""
        try:
            return self._host.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise URIError(
                f"Failed to convert host '{self._host}' to punycode"
            ) from exc

    @property
    def bytes_left(self) -> int:
        """Return the number of bytes remaining before reaching MAXIMUM_LENGTH."""
        return self.MAXIMUM_LENGTH - len(str(self).encode("utf-8"))

    @property
    def too_long(self) -> bool:
        """Return True if the URI byte representation exceeds MAXIMUM_LENGTH."""
        return len(str(self).encode("utf-8")) > self.MAXIMUM_LENGTH

    @property
    def without_query(self) -> SpartanURI:
        """Return a new SpartanURI with any query string removed."""
        return self.replace(query=None)

    @property
    def root(self) -> SpartanURI:
        """Return a new SpartanURI pointing to the root path '/' without query."""
        return self.replace(path="/", query=None)

    @property
    def parent(self) -> SpartanURI:
        """Return a new SpartanURI pointing to the parent directory path without query."""
        if self._path in ("/", ""):
            return self.without_query

        path = self._path.rstrip("/")
        if "/" not in path:
            parent_path = "/"
        else:
            parent_path = path.rsplit("/", 1)[0] + "/"

        if not parent_path.startswith("/"):
            parent_path = f"/{parent_path}"

        return self.replace(path=parent_path, query=None)

    @classmethod
    def parse(cls, uri_str: str | SpartanURI) -> SpartanURI:
        """Parse a URI string or return a SpartanURI instance."""
        if isinstance(uri_str, SpartanURI):
            return uri_str
        return cls(uri_str)

    @classmethod
    def from_str(cls, uri_str: str) -> SpartanURI:
        """Construct a SpartanURI from a string."""
        return cls(uri_str)

    @classmethod
    def with_default_scheme(cls, uri_str: str) -> SpartanURI:
        """Construct a SpartanURI from a string, prepending 'spartan://' if missing."""
        cleaned = uri_str.strip()
        if not cleaned:
            raise URIError("URI cannot be empty")
        if "://" not in cleaned:
            cleaned = f"{SPARTAN_PREFIX}{cleaned}"
        return cls(cleaned)

    def replace(
        self,
        *,
        host: str | _UnsetType = _UNSET,
        port: int | _UnsetType = _UNSET,
        path: str | _UnsetType = _UNSET,
        query: str | None | _UnsetType = _UNSET,
    ) -> SpartanURI:
        """Return a new SpartanURI with specified fields replaced."""
        new_host = self._host if isinstance(host, _UnsetType) else host
        new_port = self._port if isinstance(port, _UnsetType) else port
        new_path = self._path if isinstance(path, _UnsetType) else path
        new_query = self._query if isinstance(query, _UnsetType) else query

        target_path = new_path
        if not target_path.startswith("/"):
            target_path = f"/{target_path}"

        if new_query and "?" not in target_path:
            target_path = f"{target_path}?{new_query}"

        host_port = (
            new_host if new_port == SPARTAN_DEFAULT_PORT else f"{new_host}:{new_port}"
        )
        return SpartanURI(f"{SPARTAN_PREFIX}{host_port}{target_path}")

    def with_host(self, host: str) -> SpartanURI:
        """Return a new SpartanURI with the specified host."""
        return self.replace(host=host)

    def with_port(self, port: int) -> SpartanURI:
        """Return a new SpartanURI with the specified port."""
        return self.replace(port=port)

    def with_path(self, path: str) -> SpartanURI:
        """Return a new SpartanURI with the specified path."""
        return self.replace(path=path)

    def with_query(self, query: str | None) -> SpartanURI:
        """Return a new SpartanURI with the specified query string (or None to clear)."""
        return self.replace(query=query)

    def resolve_redirect(self, target_path: str) -> SpartanURI:
        """Return a new SpartanURI for a redirect target on the same host."""
        target = target_path.strip()
        if not target.startswith("/"):
            target = f"/{target}"
        return SpartanURI(f"{SPARTAN_PREFIX}{self._host}:{self._port}{target}")

    def __str__(self) -> str:
        path_str = self._path
        if self._query and "?" not in path_str:
            path_str = f"{path_str}?{self._query}"

        if self._port == SPARTAN_DEFAULT_PORT:
            return f"{self._scheme}://{self._host}{path_str}"
        return f"{self._scheme}://{self._host}:{self._port}{path_str}"

    def __repr__(self) -> str:
        return f"SpartanURI({str(self)!r})"

    def __len__(self) -> int:
        return len(str(self))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SpartanURI):
            return (
                self._scheme == other._scheme
                and self._host == other._host
                and self._port == other._port
                and self._path == other._path
                and self._query == other._query
            )
        return False

    def __hash__(self) -> int:
        return hash((self._scheme, self._host, self._port, self._path, self._query))
