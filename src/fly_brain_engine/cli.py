from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from fly_brain_engine.config import Settings
from fly_brain_engine.server.app import create_app


def main() -> None:
    p = argparse.ArgumentParser(description="Fly Brain Engine — Barry (MaleCNS) HTTP API")
    p.add_argument("--config", type=str, default=None, help="Path to config YAML")
    p.add_argument("--host", type=str, default=None)
    p.add_argument("--port", type=int, default=None)
    p.add_argument(
        "--demo",
        action="store_true",
        help="Procedural mini connectome — no download required (try the API locally)",
    )
    args = p.parse_args()
    settings = Settings.load(Path(args.config) if args.config else None)
    if args.demo:
        settings.demo_mode = True
        settings.default_connectome = "procedural"
        settings.default_scale = "mini"
    if args.host:
        settings.host = args.host
    if args.port:
        settings.port = args.port
    if settings.demo_mode:
        print(
            "fly-brain-engine DEMO: procedural mini graph. "
            "For real MaleCNS: python scripts/setup_malecns_data.py",
            flush=True,
        )
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
