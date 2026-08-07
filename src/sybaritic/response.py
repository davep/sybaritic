"""Response class for Spartan protocol requests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from types import TracebackType
from typing import Protocol, Self

from sybaritic.exceptions import ResponseError
from sybaritic.status import Status
from sybaritic.uri import SpartanURI


class ReaderProtocol(Protocol):
    """Protocol for async reader streams."""

    async def read(self, n: int = -1) -> bytes: ...


class Response:
    """Represents a response from a Spartan server."""

    def __init__(
        self,
        status: Status,
        meta: str,
        reader: ReaderProtocol | None = None,
        uri: SpartanURI | None = None,
        history: list[Response] | None = None,
        requested_uri: SpartanURI | None = None,
        content: bytes | None = None,
    ) -> None:
        """Initialise the Response object.

        Args:
            status: The Spartan status code.
            meta: The extra metadata line.
            reader: The stream reader for reading the response body.
            uri: The Spartan URI of the response.
            history: A history of response objects from any redirections.
            requested_uri: The originally requested Spartan URI.
            content: Pre-loaded raw response body bytes, if available.
        """
        self._status = status
        self._meta = meta
        self._reader = reader
        self._uri = uri
        self._history = list(history) if history is not None else []
        self._requested_uri = requested_uri if requested_uri is not None else uri
        self._body: bytes | None = content

    @property
    def status(self) -> Status:
        """The response status code."""
        return self._status

    @property
    def meta(self) -> str:
        """The extra info/meta string from the response header line."""
        return self._meta

    @property
    def reader(self) -> ReaderProtocol | None:
        """The stream reader for the response body."""
        return self._reader

    @property
    def uri(self) -> SpartanURI | None:
        """The SpartanURI of the response, or None if not set."""
        return self._uri

    @uri.setter
    def uri(self, value: SpartanURI | None) -> None:
        self._uri = value

    @property
    def history(self) -> list[Response]:
        """The history of response objects leading to this response via redirections."""
        return self._history

    @history.setter
    def history(self, value: list[Response]) -> None:
        self._history = value

    @property
    def requested_uri(self) -> SpartanURI | None:
        """The originally requested SpartanURI, or None if not set."""
        return self._requested_uri

    @requested_uri.setter
    def requested_uri(self, value: SpartanURI | None) -> None:
        self._requested_uri = value

    @property
    def is_success(self) -> bool:
        """Return True if response is status 2 (Success)."""
        return self._status.is_success

    @property
    def is_redirect(self) -> bool:
        """Return True if response is status 3 (Redirect)."""
        return self._status.is_redirect

    @property
    def is_client_error(self) -> bool:
        """Return True if response is status 4 (Client Error)."""
        return self._status.is_client_error

    @property
    def is_server_error(self) -> bool:
        """Return True if response is status 5 (Server Error)."""
        return self._status.is_server_error

    @property
    def is_error(self) -> bool:
        """Return True if response is status 4 or 5."""
        return self._status.is_error

    @property
    def is_redirected(self) -> bool:
        """Return True if this response is the result of following redirects."""
        return len(self._history) > 0

    @property
    def mime_type(self) -> str:
        """Return the raw MIME type for a successful response, defaulting to 'text/gemini; charset=utf-8'."""
        if not self._status.is_success:
            return ""
        meta = self._meta.strip()
        return meta if meta else "text/gemini; charset=utf-8"

    @property
    def content_type(self) -> str:
        """Return the base content type (e.g. 'text/gemini' or 'text/plain')."""
        return self.mime_type.split(";")[0].strip().lower()

    @property
    def charset(self) -> str:
        """Return the character encoding extracted from MIME type parameters, defaulting to 'utf-8'."""
        mime = self.mime_type
        if ";" in mime:
            parts = mime.split(";")[1:]
            for part in parts:
                kv = part.strip().split("=", 1)
                if len(kv) == 2 and kv[0].strip().lower() == "charset":
                    return kv[1].strip().strip('"').strip("'")
        return "utf-8"

    @property
    def redirect_path(self) -> str | None:
        """Return the target redirect path if status is 3, otherwise None."""
        return self._meta if self.is_redirect else None

    @property
    def error_message(self) -> str | None:
        """Return the error message if status is 4 or 5, otherwise None."""
        return self._meta if self.is_error else None

    @property
    def content(self) -> bytes:
        """Return cached response body bytes if already read, otherwise empty bytes."""
        return self._body if self._body is not None else b""

    async def read(self) -> bytes:
        """Read and return the entire response body.

        Returns:
            The raw response body bytes.

        Raises:
            ResponseError: If reading the response body fails.
        """
        if self._body is not None:
            return self._body

        if self._reader is None:
            self._body = b""
            return self._body

        try:
            self._body = await self._reader.read()
            return self._body
        except Exception as exc:
            raise ResponseError(f"Error reading response body: {exc}") from exc

    async def text(self, encoding: str | None = None) -> str:
        """Read and return the entire response body as a decoded string.

        Args:
            encoding: The text encoding to use. If None, uses the charset from response MIME type.

        Returns:
            The decoded response body text.

        Raises:
            ResponseError: If the response body cannot be decoded using the specified encoding.
        """
        body_bytes = await self.read()
        enc = encoding if encoding is not None else self.charset
        try:
            return body_bytes.decode(enc)
        except UnicodeDecodeError as exc:
            raise ResponseError(
                f"Failed to decode response body with encoding '{enc}': {exc}"
            ) from exc

    async def iter_chunks(self, chunk_size: int = 4096) -> AsyncIterator[bytes]:
        """Iterate over the response body in chunks as they arrive.

        Args:
            chunk_size: Maximum size of each chunk.

        Yields:
            Bytes chunks from the response body.

        Raises:
            ResponseError: If reading a response body chunk fails.
        """
        if self._body is not None:
            for i in range(0, len(self._body), chunk_size):
                yield self._body[i : i + chunk_size]
            return

        if self._reader is None:
            return

        chunks: list[bytes] = []
        try:
            while True:
                chunk = await self._reader.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
                yield chunk
            self._body = b"".join(chunks)
        except Exception as exc:
            raise ResponseError(f"Error reading response body chunk: {exc}") from exc

    async def close(self) -> None:
        """Close the underlying connection if it is still open."""
        if self._reader is not None:
            close_method = getattr(self._reader, "close", None)
            if close_method is not None:
                res = close_method()
                if hasattr(res, "__await__"):
                    await res

    async def __aenter__(self) -> Self:
        """Enter the async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the async context manager and close the connection."""
        await self.close()

    def __repr__(self) -> str:
        return f"<Response [{self._status.value} {self._status.name}] uri='{self._uri}' meta='{self._meta}'>"
