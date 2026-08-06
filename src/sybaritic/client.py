from __future__ import annotations

import asyncio
import contextlib
from typing import Self

from sybaritic.exceptions import (
    HeaderError,
    RedirectLoopError,
    RequestError,
    ResponseError,
    SybariticConnectionError,
    TooManyRedirectsError,
)
from sybaritic.response import Response
from sybaritic.status import Status
from sybaritic.uri import SpartanURI


class Client:
    """An asynchronous Spartan protocol client.

    Args:
        timeout: Default connection and read timeout in seconds. Defaults to 10.0.
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self, exc_type: object, exc_val: object, exc_tb: object
    ) -> None:
        pass

    async def send_request(
        self,
        uri: SpartanURI,
        data: bytes | str | None = None,
        timeout: float | None = None,
    ) -> Response:
        """Send a single low-level Spartan request to the server without following redirects.

        Args:
            uri: Target SpartanURI object.
            data: Optional payload string or bytes.
            timeout: Optional connection timeout in seconds.

        Returns:
            Response object.
        """
        eff_timeout = timeout if timeout is not None else self.timeout

        if isinstance(data, str):
            payload = data.encode("utf-8")
        elif isinstance(data, bytes):
            payload = data
        else:
            payload = b""

        content_length = len(payload)
        request_line = f"{uri.punycode_host} {uri.path} {content_length}\r\n".encode(
            "ascii"
        )

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(uri.host, uri.port),
                timeout=eff_timeout,
            )
        except (TimeoutError, OSError) as exc:
            raise SybariticConnectionError(
                f"Failed to connect to {uri.host}:{uri.port}: {exc}"
            ) from exc

        try:
            writer.write(request_line + payload)
            await asyncio.wait_for(writer.drain(), timeout=eff_timeout)

            raw_line = await asyncio.wait_for(reader.readline(), timeout=eff_timeout)
            if not raw_line:
                raise ResponseError(
                    "Server closed connection without sending a response line"
                )

            line = raw_line.rstrip(b"\r\n")
            if not line:
                raise HeaderError("Empty status line received from server")

            first_char = chr(line[0])
            if not (first_char.isdigit() and first_char in "2345"):
                raise HeaderError(f"Invalid status code in response: {first_char!r}")

            status = Status(int(first_char))

            if len(line) > 1 and line[1:2] == b" ":
                meta_bytes = line[2:]
            else:
                meta_bytes = line[1:]

            meta = meta_bytes.decode("utf-8", errors="replace").strip()

            content = b""
            if status == Status.SUCCESS:
                content = await asyncio.wait_for(reader.read(), timeout=eff_timeout)

            return Response(
                uri=uri,
                status=status,
                meta=meta,
                content=content,
                requested_uri=uri,
                history=[],
            )

        except TimeoutError as exc:
            raise SybariticConnectionError(
                f"Timed out communicating with {uri.host}:{uri.port}"
            ) from exc
        except (ResponseError, SybariticConnectionError):
            raise
        except Exception as exc:
            raise RequestError(f"Error during request execution: {exc}") from exc
        finally:
            writer.close()
            with contextlib.suppress(OSError, RuntimeError, asyncio.CancelledError):
                await writer.wait_closed()

    async def request(
        self,
        uri: str | SpartanURI,
        data: bytes | str | None = None,
        *,
        timeout: float | None = None,
        follow_redirects: bool = True,
        max_redirects: int = 5,
    ) -> Response:
        """Perform a Spartan request with optional redirect following.

        Args:
            uri: Target Spartan URI string or SpartanURI.
            data: Optional data payload to upload.
            timeout: Optional override for connection timeout in seconds.
            follow_redirects: Whether to follow status 3 redirects automatically.
            max_redirects: Maximum number of redirects to follow before raising error.

        Returns:
            Response object containing final target URI, history, and status.
        """
        original_uri = SpartanURI.parse(uri)
        current_uri = original_uri
        history: list[Response] = []
        visited: set[str] = set()
        redirect_count = 0

        while True:
            uri_key = f"{current_uri.host}:{current_uri.port}{current_uri.path}"
            visited.add(uri_key)

            response = await self.send_request(current_uri, data=data, timeout=timeout)
            response.requested_uri = original_uri
            response.history = list(history)

            if not response.is_redirect or not follow_redirects:
                return response

            redirect_count += 1
            if redirect_count > max_redirects:
                raise TooManyRedirectsError(
                    f"Exceeded maximum redirect count of {max_redirects}"
                )

            redirect_path = response.meta
            target_uri = current_uri.resolve_redirect(redirect_path)
            target_key = f"{target_uri.host}:{target_uri.port}{target_uri.path}"

            if target_key in visited:
                raise RedirectLoopError(
                    f"Redirect loop detected for URI '{target_uri}'"
                )

            history.append(response)
            current_uri = target_uri
            data = None

    async def get(
        self,
        uri: str | SpartanURI,
        *,
        timeout: float | None = None,
        follow_redirects: bool = True,
        max_redirects: int = 5,
    ) -> Response:
        """Convenience method for GET request (no payload)."""
        return await self.request(
            uri=uri,
            data=None,
            timeout=timeout,
            follow_redirects=follow_redirects,
            max_redirects=max_redirects,
        )

    async def post(
        self,
        uri: str | SpartanURI,
        data: bytes | str,
        *,
        timeout: float | None = None,
        follow_redirects: bool = True,
        max_redirects: int = 5,
    ) -> Response:
        """Convenience method for POST request with data payload."""
        return await self.request(
            uri=uri,
            data=data,
            timeout=timeout,
            follow_redirects=follow_redirects,
            max_redirects=max_redirects,
        )


async def request(
    uri: str | SpartanURI,
    data: bytes | str | None = None,
    *,
    timeout: float = 10.0,
    follow_redirects: bool = True,
    max_redirects: int = 5,
) -> Response:
    """Top-level convenience function to make a Spartan request."""
    async with Client(timeout=timeout) as client:
        return await client.request(
            uri,
            data=data,
            timeout=timeout,
            follow_redirects=follow_redirects,
            max_redirects=max_redirects,
        )


async def get(
    uri: str | SpartanURI,
    *,
    timeout: float = 10.0,
    follow_redirects: bool = True,
    max_redirects: int = 5,
) -> Response:
    """Top-level convenience function to make a GET request."""
    return await request(
        uri,
        data=None,
        timeout=timeout,
        follow_redirects=follow_redirects,
        max_redirects=max_redirects,
    )


async def post(
    uri: str | SpartanURI,
    data: bytes | str,
    *,
    timeout: float = 10.0,
    follow_redirects: bool = True,
    max_redirects: int = 5,
) -> Response:
    """Top-level convenience function to make a POST request with payload data."""
    return await request(
        uri,
        data=data,
        timeout=timeout,
        follow_redirects=follow_redirects,
        max_redirects=max_redirects,
    )
