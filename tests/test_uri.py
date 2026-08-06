import pytest
from sybaritic.exceptions import InvalidURIError
from sybaritic.uri import DEFAULT_PORT, SpartanURI


def test_parse_basic_uri():
    uri = SpartanURI.parse("spartan://example.com/foo/bar")
    assert uri.host == "example.com"
    assert uri.port == DEFAULT_PORT
    assert uri.path == "/foo/bar"
    assert uri.scheme == "spartan"
    assert str(uri) == "spartan://example.com/foo/bar"


def test_parse_without_scheme():
    uri = SpartanURI.parse("example.com/test")
    assert uri.host == "example.com"
    assert uri.port == 300
    assert uri.path == "/test"
    assert str(uri) == "spartan://example.com/test"


def test_parse_explicit_port():
    uri = SpartanURI.parse("spartan://example.com:3000/path")
    assert uri.host == "example.com"
    assert uri.port == 3000
    assert uri.path == "/path"
    assert str(uri) == "spartan://example.com:3000/path"


def test_parse_default_path():
    uri = SpartanURI.parse("example.com")
    assert uri.path == "/"
    assert str(uri) == "spartan://example.com/"


def test_parse_with_query():
    uri = SpartanURI.parse("spartan://example.com/search?q=test")
    assert uri.path == "/search?q=test"


def test_punycode_host():
    uri = SpartanURI.parse("spartan://münchen.de/path")
    assert uri.punycode_host == "xn--mnchen-3ya.de"


def test_invalid_uri_empty():
    with pytest.raises(InvalidURIError):
        SpartanURI.parse("")


def test_invalid_port():
    with pytest.raises(InvalidURIError):
        SpartanURI(host="example.com", port=70000, path="/")


def test_invalid_path():
    with pytest.raises(InvalidURIError):
        SpartanURI(host="example.com", port=300, path="relative/path")


def test_resolve_redirect():
    uri = SpartanURI.parse("spartan://example.com/old/path")
    redirected = uri.resolve_redirect("/new/path")
    assert redirected.host == "example.com"
    assert redirected.port == 300
    assert redirected.path == "/new/path"
