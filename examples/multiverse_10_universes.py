"""Ten Barry clones — same seed, one small difference per universe (6th sense direction).

Run: fly-brain-engine --demo
Then: python examples/multiverse_10_universes.py
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "client"))

from experiment_client import EngineClient  # noqa: E402


def main() -> None:
    ec = EngineClient()
    variants = []
    for i in range(10):
        angle = (i / 10) * 2 * math.pi
        variants.append(
            {
                "label": f"u{i}",
                "initial_inject": {
                    "synthetic.compass.x": math.cos(angle),
                    "synthetic.compass.y": math.sin(angle),
                },
            }
        )
    ens = ec.create_multiverse(
        "quantum_multiverse_demo",
        count=10,
        connectome="procedural",
        scale="mini",
        seed=42,
        variants=variants,
    )
    print("ensemble:", ens["ensemble_id"])
    tick = ec.step_multiverse(ens["ensemble_id"], milliseconds=30)
    for u in tick["universes"]:
        print(
            u["universe_label"],
            "turn=",
            round(u["motors"].get("turn", 0), 4),
            "spikes=",
            u["spikes_last_step"],
        )
    ec.close()


if __name__ == "__main__":
    main()
