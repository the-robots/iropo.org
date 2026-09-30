import pytest
import requests

from iropo_pipeline.cde import OFFICIAL_BASE, PUBLIC_BASE, CdeClient


class FakeResponse:
    status_code = 200
    ok = True
    headers: dict = {}

    def json(self):
        return {"ok": True}


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.calls = []

    def get(self, url, params=None, timeout=None, stream=False, headers=None):
        self.calls.append((url, dict(params or {}), dict(headers or {})))
        return FakeResponse()


def client_for(base, session, **kwargs):
    return CdeClient(base_url=base, api_key="secret-key", min_interval=0, session=session, **kwargs)


def test_from_env_uses_public_backend_without_key(monkeypatch):
    monkeypatch.delenv("FBI_API_KEY", raising=False)
    monkeypatch.delenv("CDE_API_BASE", raising=False)
    client = CdeClient.from_env()
    assert client.base_url == PUBLIC_BASE and client.api_key is None


def test_from_env_uses_official_gateway_with_key(monkeypatch):
    monkeypatch.setenv("FBI_API_KEY", "secret-key")
    monkeypatch.delenv("CDE_API_BASE", raising=False)
    client = CdeClient.from_env()
    assert client.base_url == OFFICIAL_BASE and client.api_key == "secret-key"


def test_api_key_is_sent_as_header_never_in_urls():
    session = FakeSession()
    client = client_for(OFFICIAL_BASE, session)
    assert client.get_json("agency/byStateAbbr/NC", {"type": "counts"}) == {"ok": True}
    url, params, headers = session.calls[0]
    assert headers == {"X-Api-Key": "secret-key"}
    assert "secret-key" not in url and "API_KEY" not in params
    assert "secret-key" not in client.url_for("agency/byStateAbbr/NC", {"type": "counts"})


def test_public_backend_never_receives_key():
    session = FakeSession()
    client_for(PUBLIC_BASE, session).get_json("nibrs/national/720", {"type": "counts"})
    _, params, headers = session.calls[0]
    assert "API_KEY" not in params and not headers


def test_request_errors_do_not_expose_the_key():
    class FailingSession(FakeSession):
        def get(self, url, params=None, timeout=None, stream=False, headers=None):
            raise requests.ConnectionError(f"Max retries exceeded with url: {url}?key=secret-key")

    client = client_for(OFFICIAL_BASE, FailingSession(), max_retries=1)
    with pytest.raises(RuntimeError) as excinfo:
        client.get_json("agency/byStateAbbr/NC")
    assert "secret-key" not in str(excinfo.value)
    assert excinfo.value.__cause__ is None
