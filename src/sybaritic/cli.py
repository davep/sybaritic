from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Sequence

from sybaritic import __version__
from sybaritic.client import Client
from sybaritic.exceptions import SybariticError
from sybaritic.uri import DEFAULT_PORT, SpartanURI


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sybaritic",
        description="Async client utility for the Spartan protocol.",
    )
    parser.add_argument(
        "url",
        help="Spartan URI to request (e.g. spartan://example.com/page.gmi)",
    )
    parser.add_argument(
        "data_positional",
        nargs="?",
        metavar="DATA",
        help="Optional data payload to post to the server",
    )
    parser.add_argument(
        "-d",
        "--data",
        help="Data payload string to post to the server",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="File path containing data payload to post",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help=f"Override target port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "-L",
        "--no-follow",
        action="store_true",
        help="Do not follow redirects (status 3)",
    )
    parser.add_argument(
        "-m",
        "--max-redirects",
        type=int,
        default=5,
        help="Maximum redirects to follow (default: 5)",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout in seconds (default: 10.0)",
    )
    parser.add_argument(
        "-i",
        "--include",
        action="store_true",
        help="Include status line and headers in output",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output raw bytes directly to stdout stream",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose connection information to stderr",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args(args)


async def run_cli(args: argparse.Namespace) -> int:
    try:
        uri = SpartanURI.parse(args.url)
        if args.port is not None:
            uri = SpartanURI(host=uri.host, port=args.port, path=uri.path, scheme=uri.scheme)
    except Exception as exc:
        print(f"Error parsing URI: {exc}", file=sys.stderr)
        return 1

    payload: bytes | None = None
    if args.file:
        try:
            payload = args.file.read_bytes()
        except OSError as exc:
            print(f"Error reading file '{args.file}': {exc}", file=sys.stderr)
            return 1
    elif args.data is not None:
        payload = args.data.encode("utf-8")
    elif args.data_positional is not None:
        payload = args.data_positional.encode("utf-8")

    if args.verbose:
        print(f"Requesting: {uri}", file=sys.stderr)
        if payload is not None:
            print(f"Payload size: {len(payload)} bytes", file=sys.stderr)

    try:
        async with Client(timeout=args.timeout) as client:
            response = await client.request(
                uri=uri,
                data=payload,
                follow_redirects=not args.no_follow,
                max_redirects=args.max_redirects,
            )

        if args.verbose:
            print(
                f"Response status: {response.status.value} {response.status.name} ({response.meta})",
                file=sys.stderr,
            )

        if args.include:
            print(f"Status: {response.status.value}")
            print(f"Meta: {response.meta}")
            print()

        if args.raw:
            sys.stdout.buffer.write(response.content)
            sys.stdout.buffer.flush()
        else:
            if response.is_success:
                print(response.text, end="" if response.text.endswith("\n") else "\n")
            elif response.is_redirect:
                print(f"Redirect: {response.redirect_path}")
            elif response.is_error:
                print(f"Error ({response.status.value}): {response.error_message}", file=sys.stderr)
                return 1

        return 0

    except SybariticError as exc:
        print(f"Sybaritic error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


def main(args: Sequence[str] | None = None) -> int:
    parsed_args = parse_args(args)
    return asyncio.run(run_cli(parsed_args))


if __name__ == "__main__":
    sys.exit(main())
