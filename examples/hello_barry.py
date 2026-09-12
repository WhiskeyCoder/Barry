"""Try the API in 30 seconds. Start server first: fly-brain-engine --demo"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "client"))

from experiment_client import EngineClient  # noqa: E402


def main() -> None:
    ec = EngineClient()
    print("health:", ec.health())
    bid = ec.create_brain("hello_barry", connectome="procedural", scale="mini")
    out = ec.inject(bid, "vision.left", 0.85, step_ms=20)
    print("inject vision.left -> motors:", out.get("motors"))
    ec.close()
    print("OK — open http://127.0.0.1:8090/docs for full API")


if __name__ == "__main__":
    main()
