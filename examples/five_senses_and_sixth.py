"""Five biological sensor channels + one synthetic (6th sense). Server: fly-brain-engine --demo"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "client"))

from experiment_client import EngineClient  # noqa: E402

FIVE = [
    ("vision.left", 0.7),
    ("vision.right", 0.3),
    ("olfaction.food", 0.2),
    ("gustation.sugar", 0.5),
    ("proprio.legs", 0.1),
    ("auditory.johnston", 0.15),
]
SIXTH = ("synthetic.compass.x", 0.82)


def main() -> None:
    ec = EngineClient()
    bid = ec.create_brain("barry_senses", connectome="procedural", scale="mini")
    for ch, val in FIVE:
        ec.inject(bid, ch, val, step_ms=0)
    out = ec.inject(bid, SIXTH[0], SIXTH[1], step_ms=25)
    print("sixth sense + five channels ->", out.get("motors"))
    ec.close()


if __name__ == "__main__":
    main()
