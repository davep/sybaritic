import asyncio

import pytest

from sybaritic.cli import parse_args, run_cli


def test_cli_parse_args_defaults() -> None:
    args = parse_args(["spartan://example.com/foo"])
    assert args.url == "spartan://example.com/foo"
    assert args.data is None
    assert args.file is None
    assert args.port is None
    assert args.no_follow is False
    assert args.max_redirects == 5
    assert args.timeout == 10.0
    assert args.include is False
    assert args.raw is False
    assert args.verbose is False


def test_cli_parse_args_custom() -> None:
    args = parse_args(
        [
            "example.com/bar",
            "hello",
            "-p",
            "3000",
            "-L",
            "-m",
            "10",
            "-t",
            "5.0",
            "-i",
            "--raw",
            "-v",
        ]
    )
    assert args.url == "example.com/bar"
    assert args.data_positional == "hello"
    assert args.port == 3000
    assert args.no_follow is True
    assert args.max_redirects == 10
    assert args.timeout == 5.0
    assert args.include is True
    assert args.raw is True
    assert args.verbose is True


@pytest.mark.asyncio
async def test_cli_execution_success(capsys: pytest.CaptureFixture[str]) -> None:
    async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        await reader.readline()
        writer.write(b"2 text/plain\r\nHello from CLI Test\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async with server:
        args = parse_args([f"127.0.0.1:{port}/test"])
        exit_code = await run_cli(args)
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Hello from CLI Test" in captured.out


@pytest.mark.asyncio
async def test_cli_execution_with_headers_and_verbose(
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def handle_client(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        req = await reader.readline()
        path = req.decode("ascii").split(" ")[1]
        if path == "/old":
            writer.write(b"3 /new\r\n")
        else:
            writer.write(b"2 text/gemini\r\n# Hello Gemini\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    async with server:
        args = parse_args(["-i", "-v", f"127.0.0.1:{port}/old"])
        exit_code = await run_cli(args)
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Status: 2" in captured.out
        assert "Meta: text/gemini" in captured.out
        assert "# Hello Gemini" in captured.out
        assert "Redirect history" in captured.err
        assert "Final Response: 2 SUCCESS" in captured.err


@pytest.mark.asyncio
async def test_cli_invalid_uri_error(capsys: pytest.CaptureFixture[str]) -> None:
    args = parse_args(["http://invalid-scheme.com"])
    exit_code = await run_cli(args)
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "sybaritic: error: invalid URI" in captured.err
