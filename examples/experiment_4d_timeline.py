import httpx
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "client"))
from experiment_client import EngineClient  # noqa: E402


def main() -> None:
    ec = EngineClient()
    brain = ec.create_brain("time_fly", scale="mini")
    sess = ec.create_session("timeline", brain, dimension=4)
    world_id = sess["world_id"]
    http = httpx.Client(base_url="http://127.0.0.1:8090", timeout=60)
    http.post(
        f"/v1/worlds/{world_id}/timeline/branch",
        json={"branch_id": "alt_history", "label": "what_if"},
    )
    for _ in range(6):
        print(ec.session_step(sess["session_id"], milliseconds=25))
    ec.close()
    http.close()


if __name__ == "__main__":
    main()
