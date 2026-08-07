# Sybaritic: Async Spartan Protocol Client Library

Sybaritic is an async-first, fully type-hinted Python client library for the [Spartan Protocol](https://portal.mozz.us/spartan/spartan.mozz.us/specification.gmi).

## Features

- **Async First**: Built on top of Python's standard `asyncio` networking loop.
- **Spartan Protocol Spec Compliant**: Supports text/binary downloads and uploads (`content-length` specification), default port `300`, and all status codes (`2` Success, `3` Redirect, `4` Client Error, `5` Server Error).
- **Type Safe**: Fully typed API with PEP 561 compliance (`py.typed`).
- **SpartanURI Representation**: Rich URI class to parse, inspect, validate, and manipulate Spartan URIs (including punycode support for IDNs).
- **Auto Redirect Handling**: Automatically handles redirects (`status 3`) with loop detection and max redirect threshold limits.
- **Zero Heavy Dependencies**: Built on top of Python's standard library.
- **CLI Utility**: Includes a `sybaritic` command-line utility out of the box.

---

## Installation

`sybaritic` requires Python 3.12 or later and can be installed with `uv` or `pip`:

With `uv`:

```shell
uv add sybaritic
```

With `pip`:

```shell
pip install sybaritic
```

---

## Quick Start

### 1. Make a Simple Request

Use `Client` with standard async context managers to query a Spartan server:

```python
import asyncio
from sybaritic import Client, SybariticError

async def main():
    async with Client() as client:
        try:
            # Query a Spartan document (defaults to port 300)
            response = await client.request("spartan://spartan.mozz.us/specification.gmi")

            print(f"Status: {response.status} ({response.meta})")
            print(f"Content Type: {response.mime_type}")
            print(response.text)

        except SybariticError as exc:
            print(f"Error querying Spartan server: {exc}")

asyncio.run(main())
```

### 2. Upload Data to a Server

Post data to a Spartan resource:

```python
import asyncio
from sybaritic import Client

async def main():
    async with Client() as client:
        # Send data payload
        response = await client.post("spartan://example.com/guestbook", data="Hello Spartan!")
        print(response.text)

asyncio.run(main())
```

---

## Command Line Interface (CLI)

`sybaritic` provides a command-line interface:

```shell
# Request a resource
sybaritic spartan://spartan.mozz.us/specification.gmi

# Output headers with body
sybaritic -i spartan://spartan.mozz.us/specification.gmi

# Upload data payload
sybaritic spartan://example.com/submit "My comment text"

# Post payload from a file
sybaritic spartan://example.com/upload -f payload.txt
```

---

## Running Tests

Run the test suite using `uv`:

```shell
uv run pytest
```

---

## License

MIT License
