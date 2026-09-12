"""Run with server up: fly-brain-engine --port 8090"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "client"))

from experiment_client import EngineClient  # noqa: E402


def main() -> None:
    ec = EngineClient("http://127.0.0.1:8090")
    brain = ec.create_brain("barry_2d", scale="mini")
    for brightness in (0.1, 0.5, 0.95):
        out = ec.inject(brain, "vision.left", brightness, step_ms=20)
        print("light", brightness, "motors", out.get("motors"))
    sess = ec.create_session("light_arena", brain, dimension=2)
    for _ in range(5):
        tick = ec.session_step(sess["session_id"], milliseconds=50)
        print("closed loop", tick.get("motors"))
    ec.close()


if __name__ == "__main__":
    main()
