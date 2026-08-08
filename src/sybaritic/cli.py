from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence
from pathlib import Path

from sybaritic import __version__
from sybaritic.client import Client
from sybaritic.exceptions import SybariticError
from sybaritic.uri import SPARTAN_DEFAULT_PORT, SpartanURI


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the sybaritic CLI utility."""
    parser = argparse.ArgumentParser(
        prog="sybaritic",
        description="Async client utility for the Spartan protocol.",
    )
    parser.add_argument(
        "url",
        help="Spartan URI to request (e.g. spartan://example.com/page.gmi or example.com/page.gmi).",
    )
    parser.add_argument(
        "data_positional",
        nargs="?",
        metavar="DATA",
        help="Optional data payload to post to the server.",
    )
    parser.add_argument(
        "-d",
        "--data",
        help="Data payload string to post to the server.",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="File path containing data payload to post to the server.",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help=f"Override target network port (default: {SPARTAN_DEFAULT_PORT}).",
    )
    parser.add_argument(
        "-L",
        "--no-follow",
        action="store_true",
        help="Do not follow redirects (status 3).",
    )
    parser.add_argument(
        "-m",
        "--max-redirects",
        type=int,
        default=5,
        help="Maximum redirects to follow before failing (default: 5).",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=10.0,
        help="Connection and communication timeout in seconds (default: 10.0).",
    )
    parser.add_argument(
        "-i",
        "--include",
        action="store_true",
        help="Include status line and metadata header in output.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Output raw response bytes directly to stdout stream.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose diagnostic and connection information to stderr.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args(args)


async def run_cli(args: argparse.Namespace) -> int:
    """Execute the CLI request based on parsed command-line arguments."""
    try:
        uri = SpartanURI.with_default_scheme(args.url)
        if args.port is not None:
            uri = uri.with_port(args.port)
    except (SybariticError, ValueError) as exc:
        print(f"sybaritic: error: invalid URI '{args.url}': {exc}", file=sys.stderr)
        return 1

    payload: bytes | None = None
    if args.file:
        try:
            payload = args.file.read_bytes()
        except OSError as exc:
            print(
                f"sybaritic: error reading file '{args.file}': {exc}", file=sys.stderr
            )
            return 1
    elif args.data is not None:
        payload = args.data.encode("utf-8")
    elif args.data_positional is not None:
        payload = args.data_positional.encode("utf-8")

    try:
        async with Client(timeout=args.timeout) as client:
            response = await client.request(
                uri=uri,
                data=payload,
                follow_redirects=not args.no_follow,
                max_redirects=args.max_redirects,
            )

        if args.verbose:
            print("--- Spartan Response ---", file=sys.stderr)
            if (
                response.requested_uri is not None
                and response.uri != response.requested_uri
            ):
                print(f"Requested URI: {response.requested_uri}", file=sys.stderr)
            if response.history:
                print("Redirections:", file=sys.stderr)
                for redirect_resp in response.history:
                    print(
                        f"  {redirect_resp.uri} -> {redirect_resp.meta.strip()}",
                        file=sys.stderr,
                    )
            print(f"URI: {response.uri}", file=sys.stderr)
            print(
                f"Status: {response.status.value} ({response.status.name})",
                file=sys.stderr,
            )
            print(f"Meta: {response.meta}", file=sys.stderr)
            print("------------------------", file=sys.stderr)

        if args.include:
            print(f"Status: {response.status.value}")
            print(f"Meta: {response.meta}")
            print()

        if args.raw:
            sys.stdout.buffer.write(await response.read())
            sys.stdout.buffer.flush()
        else:
            if response.is_success:
                text = await response.text()
                print(text, end="" if text.endswith("\n") else "\n")
            elif response.is_redirect:
                print(f"Redirect ({response.status.value}): {response.redirect_path}")
            elif response.is_error:
                print(
                    f"sybaritic: error: status {response.status.value}"
                    f" ({response.status.name}): {response.error_message}",
                    file=sys.stderr,
                )
                return 1

        return 0

    except SybariticError as exc:
        print(f"sybaritic: error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"sybaritic: unexpected error: {exc}", file=sys.stderr)
        return 1


def main(args: Sequence[str] | None = None) -> int:
    """Main CLI entry point."""
    parsed_args = parse_args(args)
    return asyncio.run(run_cli(parsed_args))


if __name__ == "__main__":
    sys.exit(main())
