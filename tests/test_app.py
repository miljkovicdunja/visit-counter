import fakeredis
import pytest

import app as app_module

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