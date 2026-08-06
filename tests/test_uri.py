import pytest
from sybaritic.exceptions import InvalidURIError, URIError
from sybaritic.uri import DEFAULT_PORT, SpartanURI


def test_instantiate_basic_uri():
    uri = SpartanURI("spartan://example.com/foo/bar")
    assert uri.scheme == "spartan"
    assert uri.host == "example.com"
    assert uri.port == DEFAULT_PORT
    assert uri.path == "/foo/bar"
    assert str(uri) == "spartan://example.com/foo/bar"
    assert repr(uri) == "SpartanURI('spartan://example.com/foo/bar')"


def test_parse_without_scheme():
    uri = SpartanURI("example.com/test")
    assert uri.host == "example.com"
    assert uri.port == 300
    assert uri.path == "/test"
    assert str(uri) == "spartan://example.com/test"


def test_parse_explicit_port():
    uri = SpartanURI("spartan://example.com:3000/path")
    assert uri.host == "example.com"
    assert uri.port == 3000
    assert uri.path == "/path"
    assert str(uri) == "spartan://example.com:3000/path"


def test_parse_default_path():
    uri = SpartanURI("example.com")
    assert uri.path == "/"
    assert str(uri) == "spartan://example.com/"


def test_parse_with_query():
    uri = SpartanURI("spartan://example.com/search?q=test")
    assert uri.path == "/search"
    assert uri.query == "q=test"
    assert str(uri) == "spartan://example.com/search?q=test"


def test_punycode_host():
    uri = SpartanURI("spartan://münchen.de/path")
    assert uri.punycode_host == "xn--mnchen-3ya.de"


def test_invalid_uri_empty():
    with pytest.raises(URIError):
        SpartanURI("")
    with pytest.raises(URIError):
        SpartanURI("   ")


def test_invalid_scheme():
    with pytest.raises(URIError) as exc_info:
        SpartanURI("http://example.com/foo")
    assert "Invalid URI scheme 'http'" in str(exc_info.value)

    with pytest.raises(URIError) as exc_info:
        SpartanURI("gopher://example.com/foo")
    assert "Invalid URI scheme 'gopher'" in str(exc_info.value)


def test_empty_scheme():
    with pytest.raises(URIError) as exc_info:
        SpartanURI("://example.com/foo")
    assert "URI scheme cannot be empty" in str(exc_info.value)


def test_invalid_host():
    with pytest.raises(URIError):
        SpartanURI("spartan://")


def test_invalid_port():
    with pytest.raises(URIError):
        SpartanURI("spartan://example.com:70000/path")


def test_resolve_redirect():
    uri = SpartanURI("spartan://example.com/old/path")
    redirected = uri.resolve_redirect("/new/path")
    assert redirected.host == "example.com"
    assert redirected.port == 300
    assert redirected.path == "/new/path"


def test_with_methods():
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


def test_replace_method():
    uri = SpartanURI("spartan://example.com/foo")
    replaced = uri.replace(host="other.org", port=3000, path="/bar", query="search=1")
    assert replaced.host == "other.org"
    assert replaced.port == 3000
    assert replaced.path == "/bar"
    assert replaced.query == "search=1"
    assert str(replaced) == "spartan://other.org:3000/bar?search=1"


def test_uri_equality_and_hash():
    u1 = SpartanURI("spartan://example.com/foo")
    u2 = SpartanURI.parse("spartan://example.com/foo")
    u3 = SpartanURI("spartan://example.com/bar")
    assert u1 == u2
    assert u1 != u3
    assert u1 != "not a uri"
    assert hash(u1) == hash(u2)
    assert len({u1, u2, u3}) == 2



def test_invalid_uri_alias():
    assert issubclass(InvalidURIError, URIError)
