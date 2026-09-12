#!/usr/bin/env python3
"""Install MaleCNS v1.0 graph.npz for fly-brain-engine (Stonkfly-compatible)."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, default=Path("connectome-data/malecns_v1"))
    parser.add_argument("--from-stonkfly-data", type=Path, help="Path to stonkfly data/ folder with graph.npz")
    parser.add_argument("--run-stonkfly-prepare", action="store_true", help="pip install stonkfly and run prepare")
    args = parser.parse_args()
    target = args.target.resolve()
    target.mkdir(parents=True, exist_ok=True)

    graph_src: Path | None = None
    if args.from_stonkfly_data:
        graph_src = args.from_stonkfly_data / "graph.npz"
    elif args.run_stonkfly_prepare:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "stonkfly", "-q"])
        subprocess.check_call([sys.executable, "-m", "stonkfly", "prepare"], cwd=Path.cwd())
        graph_src = Path("data/graph.npz")

    if not graph_src or not graph_src.is_file():
        print(
            "Provide MaleCNS graph.npz:\n"
            "  python scripts/setup_malecns_data.py --from-stonkfly-data ./data\n"
            "  python scripts/setup_malecns_data.py --run-stonkfly-prepare\n"
            "See docs/CONNECTOMES.md",
            file=sys.stderr,
        )
        return 1

    dest = target / "graph.npz"
    if not dest.exists() or dest.stat().st_size != graph_src.stat().st_size:
        shutil.copy2(graph_src, dest)
        print(f"Copied {graph_src} -> {dest}")

    manifest = {
        "version": "malecns_v1",
        "graph": "graph.npz",
        "notes": "Stonkfly-compatible CSR graph (166,700 neurons). Optional: normalized/neurons.feather",
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"MaleCNS ready under {target}")
    print(f"Set: FBE_CONNECTOME_DATA={target.parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
