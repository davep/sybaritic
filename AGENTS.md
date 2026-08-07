# AGENTS.md

Instructions and repository guidelines for AI coding agents working on **`sybaritic`**.

---

## Overview

`sybaritic` is an async-first, fully type-hinted Python client library and command-line utility for the [Spartan Protocol](https://portal.mozz.us/spartan/spartan.mozz.us/specification.gmi) (`spartan://`).

It is part of a family of small-web protocol client libraries developed alongside `wasat` (Gemini), `port70` (Gopher), and `port79` (Finger).

---

## Development Environment & Tooling

- **Python Version**: Python 3.12+
- **Package & Virtualenv Manager**: `uv`
- **Build Backend**: `uv_build`

### Essential Development Commands

| Command | Description |
| :--- | :--- |
| `make test` / `uv run pytest` | Run the unit test suite |
| `make lint` / `uv run ruff check src/ tests/` | Run `ruff` linter check |
| `make codestyle` / `uv run ruff format --check src/ tests/` | Verify `ruff` code formatting |
| `make stricttypecheck` / `uv run mypy --scripts-are-modules --strict src/ tests/` | Run strict static type checks via `mypy` |
| `make checkall` | Run all checks (spellcheck, codestyle, lint, stricttypecheck, test) |
| `make tidy` | Automatically reformat code and fix lint issues |

---

## Architecture & Codebase Structure

All library source files are located in `src/sybaritic/`:

- **`uri.py` (`SpartanURI`)**:
  - Represents and validates Spartan URIs (`spartan://host[:port]/path`).
  - Default port is **300** (`SPARTAN_DEFAULT_PORT`).
  - Provides component modifiers (`replace()`, `with_host()`, `with_port()`, `with_path()`, `with_query()`).
  - Provides path navigation properties (`parent`, `root`, `without_query`).
- **`status.py` (`Status`)**:
  - `IntEnum` for Spartan status codes: `2` (Success), `3` (Redirect), `4` (Client Error), `5` (Server Error).
- **`exceptions.py`**:
  - Exception hierarchy rooted at `SybariticError`.
  - Includes `URIError` (aliased to `InvalidURIError`), `SybariticConnectionError`, `ResponseError`, `HeaderError`, `RedirectError` (`RedirectLoopError`, `TooManyRedirectsError`), `RequestError`, and `StatusError` (`ClientError`, `ServerError`).
- **`response.py` (`Response`)**:
  - Encapsulates Spartan server responses.
  - Exposes `requested_uri`, `uri`, `history`, `is_redirected`, `status`, `meta`, `content`, `text`, `mimetype`, `encoding`, `charset`, and `raise_for_status()`.
- **`client.py` (`Client`)**:
  - Async client supporting `async with Client() as client:` and methods `get()`, `post()`, `request()`, `send_request()`.
  - Exposes top-level convenience functions: `sybaritic.get()`, `sybaritic.post()`, `sybaritic.request()`.
- **`cli.py` & `__main__.py`**:
  - Executable entry points for the `sybaritic` command-line utility.

---

## Guidelines for Modifying Code

1. **Zero Runtime Dependencies**: Keep the core library free of third-party runtime dependencies. Standard library (`asyncio`, `urllib.parse`, `dataclasses`, `enum`, `argparse`) should be used.
2. **Type Safety & Mypy**: All functions, methods, and variables must have explicit type annotations and pass `make stricttypecheck` (`mypy --strict`).
3. **API Consistency**: Keep public APIs aligned with sibling libraries (`wasat`, `port70`, `port79`) where it makes sense for Spartan.
4. **Verification**: Always run `make checkall` before declaring a task complete.
