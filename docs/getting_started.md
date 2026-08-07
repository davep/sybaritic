# Getting Started

This guide introduces the primary components of Sybaritic and demonstrates how to perform GET and POST requests, work with Spartan URIs, manage redirects, and handle errors.

All public classes, functions, status codes, and exceptions are exposed at the top level of the package. You can import them directly from `sybaritic`.

---

## Core Components

The following classes form the core interface of the library:

- **[Client][sybaritic.client.Client]**: The asynchronous client used to dispatch requests and manage connections.
- **[Response][sybaritic.response.Response]**: Represents the server's response, exposing the target URI (`uri`), original URI (`requested_uri`), redirect history (`history`), status code (`status`), header metadata (`meta`), raw body (`content`), decoded text (`text`), MIME type (`mimetype`), and status helpers.
- **[SpartanURI][sybaritic.uri.SpartanURI]**: An immutable utility class to parse, validate, manipulate, and resolve Spartan URIs safely.
- **[Status][sybaritic.status.Status]**: An integer enumeration representing official Spartan protocol response status codes (`SUCCESS`, `REDIRECT`, `CLIENT_ERROR`, `SERVER_ERROR`).

---

## Basic GET Request

To execute a request, instantiate a [Client][sybaritic.client.Client] using an asynchronous context manager or call top-level convenience functions such as [get][sybaritic.client.get].

```python
import asyncio
from sybaritic import Client, SybariticError

async def main() -> None:
    async with Client() as client:
        try:
            response = await client.get("spartan://spartan.mozz.us/specification.gmi")
            print(f"Status: {response.status.value} ({response.status.name})")
            print(f"MIME type: {response.mimetype}")
            print(f"Content length: {len(response.content)} bytes")
            print("\n--- Response Text ---")
            print(response.text)
        except SybariticError as exc:
            print(f"Request failed: {exc}")

if __name__ == "__main__":
    asyncio.run(main())
```

Alternatively, you can use the top-level shortcut function without explicitly instantiating a client:

```python
import asyncio
import sybaritic

async def main() -> None:
    response = await sybaritic.get("spartan://spartan.mozz.us/")
    print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Posting Data (POST Requests)

The Spartan protocol supports sending a data payload along with a request header. You can pass a string or bytes payload using the [post][sybaritic.client.Client.post] method:

```python
import asyncio
from sybaritic import Client

async def submit_comment() -> None:
    async with Client() as client:
        # Send a UTF-8 string payload
        response = await client.post(
            "spartan://example.com/guestbook",
            data="Hello from Sybaritic!",
        )

        if response.is_success:
            print("Successfully submitted comment!")
            print(response.text)
        elif response.is_error:
            print(f"Server returned error: {response.error_message}")

if __name__ == "__main__":
    asyncio.run(submit_comment())
```

---

## Working with Spartan URIs

The [SpartanURI][sybaritic.uri.SpartanURI] class provides validation, component extraction, and path navigation methods:

```python
from sybaritic import SpartanURI

# Parse a URI (defaults scheme to 'spartan' and port to 300 if missing)
uri = SpartanURI("example.com/docs/page.gmi?search=python")

print(uri.scheme)    # 'spartan'
print(uri.host)      # 'example.com'
print(uri.port)      # 300
print(uri.path)      # '/docs/page.gmi'
print(uri.query)     # 'search=python'
print(uri.netloc)    # 'example.com'

# Path navigation
print(uri.parent)        # SpartanURI('spartan://example.com/docs/')
print(uri.root)          # SpartanURI('spartan://example.com/')
print(uri.without_query) # SpartanURI('spartan://example.com/docs/page.gmi')

# Component modification
new_uri = uri.replace(path="/other.gmi", query=None)
print(new_uri)           # 'spartan://example.com/other.gmi'
```

---

## Redirect Handling & History

Sybaritic automatically follows status `3` (Redirect) responses by default. You can control this behavior using `follow_redirects` and `max_redirects`:

```python
import asyncio
from sybaritic import Client, RedirectLoopError, TooManyRedirectsError

async def fetch_with_redirects() -> None:
    async with Client(timeout=15.0) as client:
        try:
            response = await client.get(
                "spartan://example.com/old-location",
                follow_redirects=True,
                max_redirects=5,
            )

            if response.is_redirected:
                print(f"Original URI: {response.requested_uri}")
                print(f"Final URI:    {response.uri}")
                print(f"Redirect count: {len(response.history)}")

                for step in response.history:
                    print(f"  -> {step.status.value} to {step.redirect_path}")

        except TooManyRedirectsError:
            print("Exceeded maximum allowed redirects!")
        except RedirectLoopError:
            print("Detected a redirect loop!")

if __name__ == "__main__":
    asyncio.run(fetch_with_redirects())
```

---

## Exception Hierarchy

All exceptions raised by the library inherit from the base class [SybariticError][sybaritic.exceptions.SybariticError]. You can catch specific subclasses to handle fine-grained error conditions:

- **[URIError][sybaritic.exceptions.URIError]** (aliased as `InvalidURIError`): Raised when a given Spartan URI string cannot be parsed or has an unsupported scheme.
- **[SybariticConnectionError][sybaritic.exceptions.SybariticConnectionError]**: Raised when network connections fail, drop, or time out.
- **[ResponseError][sybaritic.exceptions.ResponseError]**: Base class for response processing failures.
  - **[HeaderError][sybaritic.exceptions.HeaderError]**: Raised when response status lines are missing or malformed.
- **[RedirectError][sybaritic.exceptions.RedirectError]**: Base class for redirect issues.
  - **[TooManyRedirectsError][sybaritic.exceptions.TooManyRedirectsError]**: Raised when exceeding `max_redirects`.
  - **[RedirectLoopError][sybaritic.exceptions.RedirectLoopError]**: Raised when a redirect loop is detected.
  - **[InvalidRedirectError][sybaritic.exceptions.InvalidRedirectError]**: Raised when a redirect path header is invalid.
- **[RequestError][sybaritic.exceptions.RequestError]**: Raised when an error occurs during request execution.
- **[StatusError][sybaritic.exceptions.StatusError]**: Raised by `response.raise_for_status()` when the response indicates an error.
  - **[ClientError][sybaritic.exceptions.ClientError]**: Raised when server returns a client error status (`4`).
  - **[ServerError][sybaritic.exceptions.ServerError]**: Raised when server returns a server error status (`5`).
