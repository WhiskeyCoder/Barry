"""5D: multi-brain quantum-time coupling experiment."""

import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "client"))
from experiment_client import EngineClient  # noqa: E402


def main() -> None:
    ec = EngineClient()
    a = ec.create_brain("brain_alpha", scale="mini", seed=1)
    b = ec.create_brain("brain_beta", scale="mini", seed=2)
    sess = ec.create_session("quantum_pair", a, dimension=5)
    world_id = sess["world_id"]

    http = httpx.Client(base_url="http://127.0.0.1:8090", timeout=60)
    http.post(f"/v1/worlds/{world_id}/brains/attach", json={"key": "beta", "brain_id": b})

    for t in range(8):
        http.post(
            f"/v1/worlds/{world_id}/quantum/entangle",
            json={"sensor_id": "synthetic.quantum_probe", "values": [0.2 + t * 0.1, 0.8 - t * 0.05]},
        )
        tick = ec.session_step(sess["session_id"], milliseconds=40)
        print("5d step", t, tick.get("motors"), tick.get("world", {}).get("fields"))
    ec.close()
    http.close()


if __name__ == "__main__":
    main()
