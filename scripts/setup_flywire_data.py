#!/usr/bin/env python3
"""Point FBE_BARRY_DATA at a FlyWire v783 connectivity bundle."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Barry (FlyWire v783) data for fly-brain-engine")
    parser.add_argument(
        "--target",
        type=Path,
        default=Path("connectome-data/flywire"),
        help="Directory to populate (default: ./barry-data)",
    )
    parser.add_argument(
        "--fly-brain-repo",
        type=Path,
        default=None,
        help="Existing clone of erojasoficial-byte/fly-brain (uses data/ inside)",
    )
    parser.add_argument(
        "--clone",
        action="store_true",
        help="Clone fly-brain repo into ./vendor/fly-brain and pull LFS data",
    )
    args = parser.parse_args()
    target = args.target.resolve()
    target.mkdir(parents=True, exist_ok=True)

    data_src: Path | None = None
    if args.fly_brain_repo:
        data_src = args.fly_brain_repo.resolve() / "data"
    elif args.clone:
        vendor = Path("vendor") / "fly-brain"
        if not vendor.is_dir():
            subprocess.check_call(
                ["git", "clone", "https://github.com/erojasoficial-byte/fly-brain.git", str(vendor)]
            )
        subprocess.check_call(["git", "lfs", "pull"], cwd=vendor)
        data_src = vendor / "data"

    if not data_src or not data_src.is_dir():
        print(
            "No data source. Either:\n"
            "  python scripts/setup_barry_data.py --fly-brain-repo C:/path/to/fly-brain\n"
            "  python scripts/setup_barry_data.py --clone\n"
            "Or download Zenodo FlyWire v783 and place 2025_Connectivity_783.parquet here.",
            file=sys.stderr,
        )
        return 1

    for name in (
        "2025_Connectivity_783.parquet",
        "2025_Completeness_783.csv",
        "flywire_annotations.tsv",
    ):
        src = data_src / name
        if src.is_file():
            dest = target / name
            if not dest.exists():
                print(f"Link/copy {src} -> {dest}")
                try:
                    os.link(src, dest)
                except OSError:
                    shutil.copy2(src, dest)

    manifest = {
        "version": "flywire_v783",
        "connectivity": "2025_Connectivity_783.parquet",
        "completeness": "2025_Completeness_783.csv",
        "annotations": "flywire_annotations.tsv",
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Barry data ready under {target}")
    print(f"Set env: FBE_BARRY_DATA={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
