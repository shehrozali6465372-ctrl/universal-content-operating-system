import pytest

from services.ucos_browser.server import validate_url


def test_public_https_url_allowed():
    assert validate_url("https://example.com/path") == "https://example.com/path"


def test_non_http_scheme_rejected():
    with pytest.raises(ValueError):
        validate_url("file:///etc/passwd")


def test_localhost_rejected():
    with pytest.raises(ValueError):
        validate_url("http://localhost:8000/health")


def test_private_ipv4_rejected():
    with pytest.raises(ValueError):
        validate_url("http://127.0.0.1:8000/")
