from fastapi.testclient import TestClient

from fly_brain_engine.config import Settings
from fly_brain_engine.core.lif_network import LIFNetwork
from fly_brain_engine.server.app import create_app


def test_lif_steps() -> None:
    net = LIFNetwork.from_scale("mini", seed=0)
    net.stimulate_rate(net.population_ids("photoreceptor_R1_R6_left")[:3], 80.0)
    net.step(10.0)
    assert net._state.time_ms > 0


def test_api_inject(tmp_path) -> None:
    app = create_app(Settings(storage_dir=tmp_path))
    with TestClient(app) as c:
        r = c.post("/v1/brains", json={"name": "t", "connectome": "procedural", "scale": "mini"})
        bid = r.json()["id"]
        r = c.post(
            "/v1/experiments/inject",
            json={"brain_id": bid, "channel": "vision.left", "data": 0.7, "step_ms": 5},
        )
        assert r.status_code == 200
        assert "motors" in r.json()


def test_multiverse_demo(tmp_path) -> None:
    app = create_app(Settings(storage_dir=tmp_path, demo_mode=True, default_connectome="procedural"))
    with TestClient(app) as c:
        r = c.post(
            "/v1/experiments/multiverse",
            json={
                "name": "ten",
                "count": 3,
                "connectome": "procedural",
                "scale": "mini",
                "seed": 1,
                "variants": [
                    {"label": "a", "initial_inject": {"synthetic.compass.x": 0.1}},
                    {"label": "b", "initial_inject": {"synthetic.compass.x": 0.9}},
                    {"label": "c", "initial_inject": {}},
                ],
            },
        )
        assert r.status_code == 200
        eid = r.json()["ensemble_id"]
        step = c.post(f"/v1/experiments/multiverse/{eid}/step", params={"milliseconds": 5})
        assert step.status_code == 200
        assert len(step.json()["universes"]) == 3


def test_session_2d(tmp_path) -> None:
    app = create_app(Settings(storage_dir=tmp_path))
    with TestClient(app) as c:
        bid = c.post("/v1/brains", json={"name": "w", "connectome": "procedural", "scale": "mini"}).json()["id"]
        sid = c.post(
            "/v1/experiments/sessions",
            json={"name": "s", "brain_id": bid, "dimension": 2},
        ).json()["session_id"]
        r = c.post(f"/v1/experiments/sessions/{sid}/step", params={"milliseconds": 20})
        assert r.status_code == 200
