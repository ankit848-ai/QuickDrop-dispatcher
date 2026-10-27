"""API tests using FastAPI's TestClient."""

import time

from fastapi.testclient import TestClient

from api.index import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_simulate_shape() -> None:
    body = {"riders": 10, "orders": 120, "city_size": 30, "strategy": "greedy", "seed": 7}
    r = client.post("/api/simulate", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["city"]["size"] == 30
    assert len(data["restaurants"]) >= 3
    assert len(data["orders"]) == 120
    assert 0 < len(data["frames"]) <= 302
    assert len(data["frames"][0]["riders"]) == 10
    assert data["metrics"]["delivered"] == 120
    o = data["orders"][0]
    assert o["path"][-1] == o["y"] * 30 + o["x"]


def test_simulate_is_deterministic() -> None:
    body = {"riders": 5, "orders": 40, "city_size": 20, "seed": 3}
    a = client.post("/api/simulate", json=body).json()
    b = client.post("/api/simulate", json=body).json()
    assert a["metrics"] == b["metrics"]


def test_validation_caps() -> None:
    assert client.post("/api/simulate", json={"riders": 500}).status_code == 422
    assert client.post("/api/simulate", json={"orders": 5000}).status_code == 422
    assert client.post("/api/simulate", json={"strategy": "random"}).status_code == 422


def test_compare() -> None:
    r = client.post("/api/compare", json={"riders": 20, "orders": 300, "seed": 1})
    assert r.status_code == 200
    data = r.json()
    for key in ("greedy", "naive"):
        assert data[key]["delivered"] == 300
    assert data["greedy"]["avg_delivery_time"] < data["naive"]["avg_delivery_time"]


def test_max_size_runs_fast() -> None:
    start = time.perf_counter()
    r = client.post("/api/simulate", json={"riders": 200, "orders": 2000, "city_size": 80})
    assert r.status_code == 200
    assert time.perf_counter() - start < 10
