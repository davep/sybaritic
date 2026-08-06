import pytest

from sybaritic.exceptions import InvalidURIError, URIError
from sybaritic.uri import (
    MAXIMUM_LENGTH,
    SPARTAN_DEFAULT_PORT,
    SPARTAN_SCHEME,
    SpartanURI,
)


def test_instantiate_basic_uri() -> None:
    uri = SpartanURI("spartan://example.com/foo/bar")
    assert uri.scheme == SPARTAN_SCHEME
    assert uri.host == "example.com"
    assert uri.hostname == "example.com"
    assert uri.port == SPARTAN_DEFAULT_PORT
    assert uri.netloc == "example.com"
    assert uri.path == "/foo/bar"
    assert str(uri) == "spartan://example.com/foo/bar"
    assert repr(uri) == "SpartanURI('spartan://example.com/foo/bar')"
    assert len(uri) == len("spartan://example.com/foo/bar")


def test_netloc_custom_port() -> None:
    uri = SpartanURI("spartan://example.com:3000/path")
    assert uri.netloc == "example.com:3000"


def test_parse_without_scheme() -> None:
    uri = SpartanURI("example.com/test")
    assert uri.host == "example.com"
    assert uri.port == 300
    assert uri.path == "/test"
    assert str(uri) == "spartan://example.com/test"


def test_with_default_scheme_and_from_str() -> None:
    u1 = SpartanURI.with_default_scheme("example.com/hello")
    assert u1.scheme == "spartan"
    assert u1.host == "example.com"
    assert u1.path == "/hello"

    u2 = SpartanURI.from_str("spartan://example.com/hello")
    assert u2 == u1


def test_length_properties() -> None:
    uri_str = "spartan://example.com/path"
    uri = SpartanURI(uri_str)
    assert len(uri) == len(uri_str)
    assert uri.bytes_left == MAXIMUM_LENGTH - len(uri_str.encode("utf-8"))
    assert not uri.too_long

    long_path = "/" + "a" * (MAXIMUM_LENGTH + 10)
    long_uri = SpartanURI(f"spartan://example.com{long_path}")
    assert long_uri.too_long
    assert long_uri.bytes_left < 0


def test_parent_and_root_and_without_query() -> None:
    uri = SpartanURI("spartan://example.com/a/b/c?key=val")

    assert uri.without_query == SpartanURI("spartan://example.com/a/b/c")
    assert uri.root == SpartanURI("spartan://example.com/")

    p1 = uri.parent
    assert p1 == SpartanURI("spartan://example.com/a/b/")
    assert p1.query is None

    p2 = p1.parent
    assert p2 == SpartanURI("spartan://example.com/a/")

    p3 = p2.parent
    assert p3 == SpartanURI("spartan://example.com/")

    p4 = p3.parent
    assert p4 == SpartanURI("spartan://example.com/")


def test_punycode_host() -> None:
    uri = SpartanURI("spartan://münchen.de/path")
    assert uri.punycode_host == "xn--mnchen-3ya.de"


def test_invalid_uri_empty() -> None:
    with pytest.raises(URIError):
        SpartanURI("")
    with pytest.raises(URIError):
        SpartanURI("   ")
    with pytest.raises(URIError):
        SpartanURI.with_default_scheme("")


def test_invalid_scheme() -> None:
    with pytest.raises(URIError) as exc_info:
        SpartanURI("http://example.com/foo")
    assert "Invalid URI scheme 'http'" in str(exc_info.value)


def test_empty_scheme() -> None:
    with pytest.raises(URIError) as exc_info:
        SpartanURI("://example.com/foo")
    assert "URI scheme cannot be empty" in str(exc_info.value)


def test_invalid_host() -> None:
    with pytest.raises(URIError):
        SpartanURI("spartan://")


def test_invalid_port() -> None:
    with pytest.raises(URIError):
        SpartanURI("spartan://example.com:70000/path")


def test_with_methods() -> None:
    uri = SpartanURI("spartan://example.com:3000/old/path?q=1")

    h_uri = uri.with_host("newdomain.org")
    assert h_uri.host == "newdomain.org"
    assert h_uri.port == 3000
    assert h_uri.path == "/old/path"
    assert h_uri.query == "q=1"

    p_uri = uri.with_port(4000)
    assert p_uri.port == 4000

    path_uri = uri.with_path("/new/path")
    assert path_uri.path == "/new/path"

    q_uri = uri.with_query("q=2")
    assert q_uri.query == "q=2"

    no_q_uri = uri.with_query(None)
    assert no_q_uri.query is None
    assert str(no_q_uri) == "spartan://example.com:3000/old/path"


def test_replace_method() -> None:
    uri = SpartanURI("spartan://example.com/foo")
    replaced = uri.replace(host="other.org", port=3000, path="/bar", query="search=1")
    assert replaced.host == "other.org"
    assert replaced.port == 3000
    assert replaced.path == "/bar"
    assert replaced.query == "search=1"
    assert str(replaced) == "spartan://other.org:3000/bar?search=1"


def test_uri_equality_and_hash() -> None:
    u1 = SpartanURI("spartan://example.com/foo")
    u2 = SpartanURI.parse("spartan://example.com/foo")
    u3 = SpartanURI("spartan://example.com/bar")
    assert u1 == u2
    assert u1 != u3
    assert u1 != "not a uri"
    assert hash(u1) == hash(u2)
    assert len({u1, u2, u3}) == 2


def test_invalid_uri_alias() -> None:
    assert issubclass(InvalidURIError, URIError)
