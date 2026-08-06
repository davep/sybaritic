import pytest
from sybaritic.exceptions import ClientError, ServerError
from sybaritic.response import Response
from sybaritic.status import Status
from sybaritic.uri import SpartanURI


@pytest.fixture
def base_uri():
    return SpartanURI.parse("spartan://example.com/test")


def test_success_response(base_uri):
    resp = Response(
        uri=base_uri,
        status=Status.SUCCESS,
        meta="text/gemini; charset=utf-8",
        content=b"# Hello Spartan",
    )
    assert resp.is_success
    assert not resp.is_redirect
    assert not resp.is_error
    assert resp.mimetype == "text/gemini"
    assert resp.encoding == "utf-8"
    assert resp.text == "# Hello Spartan"
    assert resp.redirect_path is None
    assert resp.error_message is None
    resp.raise_for_status()  # Should not raise


def test_redirect_response(base_uri):
    resp = Response(
        uri=base_uri,
        status=Status.REDIRECT,
        meta="/new-location",
    )
    assert resp.is_redirect
    assert not resp.is_success
    assert resp.redirect_path == "/new-location"
    assert resp.mimetype == ""
    resp.raise_for_status()  # Redirect is not an error status code in raise_for_status


def test_client_error_response(base_uri):
    resp = Response(
        uri=base_uri,
        status=Status.CLIENT_ERROR,
        meta="Resource not found",
    )
    assert resp.is_client_error
    assert resp.is_error
    assert resp.error_message == "Resource not found"
    with pytest.raises(ClientError) as exc_info:
        resp.raise_for_status()
    assert exc_info.value.response is resp
    assert "Resource not found" in str(exc_info.value)


def test_server_error_response(base_uri):
    resp = Response(
        uri=base_uri,
        status=Status.SERVER_ERROR,
        meta="Internal server error",
    )
    assert resp.is_server_error
    assert resp.is_error
    assert resp.error_message == "Internal server error"
    with pytest.raises(ServerError) as exc_info:
        resp.raise_for_status()
    assert exc_info.value.response is resp


def test_text_decoding_fallback(base_uri):
    resp = Response(
        uri=base_uri,
        status=Status.SUCCESS,
        meta="text/plain; charset=invalid-charset-1234",
        content=b"hello world",
    )
    assert resp.text == "hello world"
