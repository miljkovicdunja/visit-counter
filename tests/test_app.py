import fakeredis
import pytest

import app as app_module

from unittest.mock import MagicMock
import redis

@pytest.fixture
def client(monkeypatch):
    fake=fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(app_module, "get_redis", lambda:fake)
    app_module.app.config["TESTING"]=True
    return app_module.app.test_client()

def test_index_returns_200(client):
    response=client.get("/")
    assert response.status_code==200
    assert response.get_json()["message"]=="Hello DevOps"
    assert "host" in response.get_json()

def test_visits_increments(client):
    assert client.get("/visits").get_json() == {"visits":1}
    assert client.get("/visits").get_json() == {"visits":2}

def test_health_ok(client):
    response=client.get("/health")
    assert response.status_code==200
    assert response.get_json()=={"status" : "ok"}

def test_health_redis_down(monkeypatch):
    broken=MagicMock()
    broken.ping.side_effect = redis.exceptions.ConnectionError()
    monkeypatch.setattr(app_module, "get_redis", lambda: broken)

    response=app_module.app.test_client().get("/health")
    assert response.status_code==503
    assert response.get_json()=={"status" : "error"}