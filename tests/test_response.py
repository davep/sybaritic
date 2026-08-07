import pytest

from sybaritic.exceptions import ResponseError
from sybaritic.response import Response
from sybaritic.status import Status
from sybaritic.uri import SpartanURI


class DummyReader:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self._offset = 0
        self.closed = False

    async def read(self, n: int = -1) -> bytes:
        if self._offset >= len(self._data):
            return b""
        if n == -1:
            chunk = self._data[self._offset :]
            self._offset = len(self._data)
            return chunk
        chunk = self._data[self._offset : self._offset + n]
        self._offset += len(chunk)
        return chunk

    async def close(self) -> None:
        self.closed = True


@pytest.fixture
def base_uri() -> SpartanURI:
    return SpartanURI.parse("spartan://example.com/test")


@pytest.mark.asyncio
async def test_success_response(base_uri: SpartanURI) -> None:
    resp = Response(
        uri=base_uri,
        status=Status.SUCCESS,
        meta="text/gemini; charset=utf-8",
        content=b"# Hello Spartan",
    )
    assert resp.is_success
    assert not resp.is_redirect
    assert not resp.is_error
    assert not resp.is_redirected
    assert resp.requested_uri == base_uri
    assert resp.history == []
    assert resp.mime_type == "text/gemini; charset=utf-8"
    assert resp.content_type == "text/gemini"
    assert resp.charset == "utf-8"
    assert await resp.read() == b"# Hello Spartan"
    assert await resp.text() == "# Hello Spartan"
    assert resp.content == b"# Hello Spartan"
    assert resp.redirect_path is None
    assert resp.error_message is None


def test_response_mime_type_default_and_parameters(base_uri: SpartanURI) -> None:
    empty_meta_resp = Response(uri=base_uri, status=Status.SUCCESS, meta="")
    assert empty_meta_resp.mime_type == "text/gemini; charset=utf-8"
    assert empty_meta_resp.content_type == "text/gemini"

    spaces_meta_resp = Response(uri=base_uri, status=Status.SUCCESS, meta="   ")
    assert spaces_meta_resp.mime_type == "text/gemini; charset=utf-8"

    param_resp = Response(
        uri=base_uri, status=Status.SUCCESS, meta="text/plain; charset=iso-8859-1"
    )
    assert param_resp.mime_type == "text/plain; charset=iso-8859-1"
    assert param_resp.content_type == "text/plain"
    assert param_resp.charset == "iso-8859-1"


def test_redirect_history_response() -> None:
    req_uri = SpartanURI("spartan://example.com/initial")
    final_uri = SpartanURI("spartan://example.com/final")

    redirect_resp = Response(
        uri=req_uri,
        status=Status.REDIRECT,
        meta="/final",
    )

    final_resp = Response(
        uri=final_uri,
        status=Status.SUCCESS,
        meta="text/plain",
        content=b"Final page content",
        requested_uri=req_uri,
        history=[redirect_resp],
    )

    assert final_resp.is_redirected
    assert final_resp.requested_uri == req_uri
    assert len(final_resp.history) == 1
    assert final_resp.history[0] == redirect_resp


def test_client_error_response(base_uri: SpartanURI) -> None:
    resp = Response(
        uri=base_uri,
        status=Status.CLIENT_ERROR,
        meta="Resource not found",
    )
    assert resp.is_client_error
    assert resp.is_error
    assert resp.error_message == "Resource not found"


def test_server_error_response(base_uri: SpartanURI) -> None:
    resp = Response(
        uri=base_uri,
        status=Status.SERVER_ERROR,
        meta="Internal server error",
    )
    assert resp.is_server_error
    assert resp.is_error
    assert resp.error_message == "Internal server error"


@pytest.mark.asyncio
async def test_text_encoding_error(base_uri: SpartanURI) -> None:
    resp = Response(
        uri=base_uri,
        status=Status.SUCCESS,
        meta="text/plain; charset=utf-8",
        content=b"\xff\xfe",
    )
    with pytest.raises(ResponseError):
        await resp.text()


@pytest.mark.asyncio
async def test_response_streaming_reader(base_uri: SpartanURI) -> None:
    dummy_reader = DummyReader(b"Chunk1Chunk2Chunk3")
    resp = Response(
        uri=base_uri,
        status=Status.SUCCESS,
        meta="text/plain",
        reader=dummy_reader,
    )
    chunks = []
    async for chunk in resp.iter_chunks(chunk_size=6):
        chunks.append(chunk)

    assert chunks == [b"Chunk1", b"Chunk2", b"Chunk3"]
    assert await resp.read() == b"Chunk1Chunk2Chunk3"


@pytest.mark.asyncio
async def test_response_async_context_manager(base_uri: SpartanURI) -> None:
    dummy_reader = DummyReader(b"hello")
    resp = Response(
        uri=base_uri,
        status=Status.SUCCESS,
        meta="text/plain",
        reader=dummy_reader,
    )
    async with resp as r:
        assert r is resp
        assert await r.text() == "hello"

    await resp.close()
    assert dummy_reader.closed
