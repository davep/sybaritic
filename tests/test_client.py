import asyncio

import pytest

import sybaritic
from sybaritic.client import Client
from sybaritic.exceptions import (
    HeaderError,
    RedirectLoopError,
    TooManyRedirectsError,
)
from sybaritic.status import Status


@pytest.mark.asyncio
async def test_client_get_success() -> None:
    async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        request_line = await reader.readline()
        assert request_line == b"127.0.0.1 /index.gmi 0\r\n"
        writer.write(b"2 text/gemini\r\n# Welcome to Spartan\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async with server, Client() as client:
        resp = await client.get(f"spartan://127.0.0.1:{port}/index.gmi")
        assert resp.status == Status.SUCCESS
        assert resp.mime_type == "text/gemini"
        assert await resp.text() == "# Welcome to Spartan\r\n"
        assert not resp.is_redirected
        assert resp.history == []


@pytest.mark.asyncio
async def test_top_level_get_and_post() -> None:
    async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        request_line = await reader.readline()
        if b"/get-test" in request_line:
            writer.write(b"2 text/plain\r\nTop level GET\r\n")
        elif b"/post-test" in request_line:
            payload_len = int(request_line.decode("ascii").split(" ")[2])
            payload = await reader.readexactly(payload_len)
            writer.write(
                f"2 text/plain\r\nTop level POST: {payload.decode('utf-8')}\r\n".encode()
            )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async with server:
        resp1 = await sybaritic.get(f"spartan://127.0.0.1:{port}/get-test")
        assert await resp1.text() == "Top level GET\r\n"

        resp2 = await sybaritic.post(
            f"spartan://127.0.0.1:{port}/post-test", data="hello world"
        )
        assert await resp2.text() == "Top level POST: hello world\r\n"


@pytest.mark.asyncio
async def test_client_redirect_following_with_history() -> None:
    async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        request_line = await reader.readline()
        path = request_line.decode("ascii").split(" ")[1]
        if path == "/old-path":
            writer.write(b"3 /new-path\r\n")
        elif path == "/new-path":
            writer.write(b"2 text/gemini\r\n# New Destination\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async with server, Client() as client:
        resp = await client.get(f"spartan://127.0.0.1:{port}/old-path")
        assert resp.status == Status.SUCCESS
        assert await resp.text() == "# New Destination\r\n"
        assert resp.uri is not None and resp.uri.path == "/new-path"
        assert resp.requested_uri is not None
        assert resp.requested_uri.path == "/old-path"
        assert resp.is_redirected
        assert len(resp.history) == 1
        assert resp.history[0].status == Status.REDIRECT
        assert (
            resp.history[0].uri is not None and resp.history[0].uri.path == "/old-path"
        )


@pytest.mark.asyncio
async def test_client_redirect_loop_detection() -> None:
    async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        request_line = await reader.readline()
        path = request_line.decode("ascii").split(" ")[1]
        if path == "/page1":
            writer.write(b"3 /page2\r\n")
        elif path == "/page2":
            writer.write(b"3 /page1\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async with server, Client() as client:
        with pytest.raises(RedirectLoopError):
            await client.get(f"spartan://127.0.0.1:{port}/page1")


@pytest.mark.asyncio
async def test_client_max_redirects_exceeded() -> None:
    async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        request_line = await reader.readline()
        path = request_line.decode("ascii").split(" ")[1]
        step = int(path.strip("/step")) if "/step" in path else 0
        writer.write(f"3 /step{step + 1}\r\n".encode("ascii"))
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async with server, Client() as client:
        with pytest.raises(TooManyRedirectsError):
            await client.get(f"spartan://127.0.0.1:{port}/step0", max_redirects=3)


@pytest.mark.asyncio
async def test_client_errors() -> None:
    async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        request_line = await reader.readline()
        path = request_line.decode("ascii").split(" ")[1]
        if path == "/notfound":
            writer.write(b"4 File not found\r\n")
        elif path == "/crash":
            writer.write(b"5 Server on fire\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async with server, Client() as client:
        resp4 = await client.get(f"spartan://127.0.0.1:{port}/notfound")
        assert resp4.status == Status.CLIENT_ERROR
        assert resp4.error_message == "File not found"

        resp5 = await client.get(f"spartan://127.0.0.1:{port}/crash")
        assert resp5.status == Status.SERVER_ERROR
        assert resp5.error_message == "Server on fire"


@pytest.mark.asyncio
async def test_client_invalid_status_line() -> None:
    async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        await reader.readline()
        writer.write(b"INVALID STATUS LINE\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async with server, Client() as client:
        with pytest.raises(HeaderError):
            await client.get(f"spartan://127.0.0.1:{port}/")
