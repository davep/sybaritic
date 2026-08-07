# Sybaritic: Async Spartan Protocol Client Library

Sybaritic is an asynchronous, object-oriented, fully type-hinted client library and command-line utility for the [Spartan Protocol](https://portal.mozz.us/spartan/spartan.mozz.us/specification.gmi). It is designed to target Python 3.12 and later, keeping zero runtime third-party dependencies and relying entirely on the Python standard library.

Features of the library:

- **Asynchronous throughout**: Built on top of standard `asyncio` for non-blocking network operations.
- **Zero runtime dependencies**: Pure Python standard library implementation using `asyncio`, `urllib.parse`, `dataclasses`, and `enum`.
- **Strictly typed**: Complete type safety utilizing modern Python standards, strictly avoiding `Any`.
- **Automatic redirect handling**: Transparently follows status 3 redirects, protects against redirect loops, and records complete redirect history.
- **POST payload support**: Native support for uploading text or binary data streams to Spartan endpoints.
- **CLI utility included**: Provides a command-line interface out of the box (`sybaritic`).

## Installation

You can install Sybaritic in your environment. The recommended tool for modern Python projects is `uv`, but standard `pip` is also fully supported.

### Using uv

To add Sybaritic to your project as a dependency:

```bash
uv add sybaritic
```

To install Sybaritic directly into your active virtual environment:

```bash
uv pip install sybaritic
```

To run the Sybaritic command-line interface without installing it globally:

```bash
uvx sybaritic spartan://spartan.mozz.us/
```

### Using pip

To install Sybaritic from PyPI using standard packaging tools:

```bash
pip install sybaritic
```
