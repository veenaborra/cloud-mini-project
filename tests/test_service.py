"""API behaviour with a fake model (no weights, no network)."""
import pytest
from fastapi.testclient import TestClient
import app as service

GOOD = '{"intent": "alarm_set", "date": "tomorrow", "time": "seven am", "place": null}'


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setitem(service.state, "ready", True)
    monkeypatch.setattr(service.inference, "generate", lambda *a: GOOD)
    monkeypatch.setattr(service, "FAULT_INJECT", False)
    return TestClient(service.app)          # no `with`: model download does not start


def test_parse_ok(client):
    r = client.post("/parse", json={"text": "x"})
    assert r.status_code == 200 and list(r.json()) == ["intent", "date", "time", "place"]
    assert "X-Model-Version" in r.headers and "X-Served-By" in r.headers


def test_invalid_output_and_fault_inject(client, monkeypatch):
    monkeypatch.setattr(service.inference, "generate", lambda *a: '{"intent": "nope"}')
    assert client.post("/parse", json={"text": "x"}).json() == {"error": "invalid_model_output"}
    monkeypatch.setattr(service.inference, "generate", lambda *a: GOOD)
    monkeypatch.setattr(service, "FAULT_INJECT", True)
    r = client.post("/parse", json={"text": "x"})
    assert r.status_code == 500 and r.json() == {"error": "invalid_model_output"}


def test_probes(client, monkeypatch):
    assert client.get("/readyz").status_code == 200
    monkeypatch.setitem(service.state, "ready", False)
    assert client.get("/readyz").status_code == 503
    assert client.get("/healthz").status_code == 200
