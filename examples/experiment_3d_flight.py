import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "client"))
from experiment_client import EngineClient  # noqa: E402


def main() -> None:
    ec = EngineClient()
    brain = ec.create_brain("fly_3d", scale="mini")
    sess = ec.create_session("volume_nav", brain, dimension=3)
    for i in range(10):
        ec.inject(brain, "proprio.legs", i / 10.0, step_ms=0)
        tick = ec.session_step(sess["session_id"], milliseconds=30)
        print(f"step {i}", tick.get("payloads"), tick.get("motors"))
    ec.close()


if __name__ == "__main__":
    main()
