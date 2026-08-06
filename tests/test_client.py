import asyncio
import pytest
from sybaritic.client import Client
from sybaritic.exceptions import (
    HeaderError,
    RedirectLoopError,
    SybariticConnectionError,
    TooManyRedirectsError,
)
from sybaritic.status import Status


@pytest.mark.asyncio
async def test_client_get_success():
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        request_line = await reader.readline()
        assert request_line == b"127.0.0.1 /index.gmi 0\r\n"
        writer.write(b"2 text/gemini\r\n# Welcome to Spartan\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async with server:
        async with Client() as client:
            resp = await client.get(f"spartan://127.0.0.1:{port}/index.gmi")
            assert resp.status == Status.SUCCESS
            assert resp.mimetype == "text/gemini"
            assert resp.text == "# Welcome to Spartan\r\n"


@pytest.mark.asyncio
async def test_client_post_payload():
    received_data = bytearray()
    received_header = b""

    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        nonlocal received_header
        received_header = await reader.readline()
        # Header format: host path length\r\n
        parts = received_header.decode("ascii").rstrip("\r\n").split(" ")
        content_len = int(parts[2])
        data = await reader.readexactly(content_len)
        received_data.extend(data)
        writer.write(b"2 text/plain\r\nReceived payload\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async with server:
        async with Client() as client:
            payload = "Hello, Spartan server!"
            resp = await client.post(f"127.0.0.1:{port}/submit", data=payload)
            assert resp.status == Status.SUCCESS
            assert resp.text == "Received payload\r\n"
            assert received_header == f"127.0.0.1 /submit {len(payload.encode('utf-8'))}\r\n".encode("ascii")
            assert received_data == payload.encode("utf-8")


@pytest.mark.asyncio
async def test_client_redirect_following():
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
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

    async with server:
        async with Client() as client:
            resp = await client.get(f"127.0.0.1:{port}/old-path")
            assert resp.status == Status.SUCCESS
            assert resp.text == "# New Destination\r\n"
            assert resp.uri.path == "/new-path"


@pytest.mark.asyncio
async def test_client_redirect_loop_detection():
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
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

    async with server:
        async with Client() as client:
            with pytest.raises(RedirectLoopError):
                await client.get(f"127.0.0.1:{port}/page1")


@pytest.mark.asyncio
async def test_client_max_redirects_exceeded():
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        request_line = await reader.readline()
        path = request_line.decode("ascii").split(" ")[1]
        step = int(path.strip("/step")) if "/step" in path else 0
        writer.write(f"3 /step{step + 1}\r\n".encode("ascii"))
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async with server:
        async with Client() as client:
            with pytest.raises(TooManyRedirectsError):
                await client.get(f"127.0.0.1:{port}/step0", max_redirects=3)


@pytest.mark.asyncio
async def test_client_errors():
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
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

    async with server:
        async with Client() as client:
            resp4 = await client.get(f"127.0.0.1:{port}/notfound")
            assert resp4.status == Status.CLIENT_ERROR
            assert resp4.error_message == "File not found"

            resp5 = await client.get(f"127.0.0.1:{port}/crash")
            assert resp5.status == Status.SERVER_ERROR
            assert resp5.error_message == "Server on fire"


@pytest.mark.asyncio
async def test_client_invalid_status_line():
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        await reader.readline()
        writer.write(b"INVALID STATUS LINE\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async with server:
        async with Client() as client:
            with pytest.raises(HeaderError):
                await client.get(f"127.0.0.1:{port}/")
