from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fly_brain_engine.connectome.profiles import connectome_data_status
from fly_brain_engine.brains.registry import BrainRegistry
from fly_brain_engine.config import Settings
from fly_brain_engine.experiments.session import ExperimentHub
from fly_brain_engine.experiments.ensemble import EnsembleHub
from fly_brain_engine.server.deps import EngineState
from fly_brain_engine.server.routes import brains, connectome, experiments, worlds
from fly_brain_engine.server import websocket as ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings  # type: ignore[attr-defined]
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    registry = BrainRegistry(settings)
    hub = ExperimentHub(registry)
    app.state.engine = EngineState(
        settings=settings,
        brains=registry,
        experiments=hub,
        ensembles=EnsembleHub(registry),
    )
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or Settings.load()
    app = FastAPI(
        title="Fly Brain Engine — Experimental Server",
        description="Full connectome LIF engine. Send data from any Python experiment script.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = cfg
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(brains.router)
    app.include_router(worlds.router)
    app.include_router(experiments.router)
    app.include_router(connectome.router)
    app.include_router(ws.router)

    @app.get("/health")
    def health() -> dict:
        conn = connectome_data_status(
            cfg.connectome_bundle_dir(cfg.default_connectome), cfg.default_connectome
        )
        return {
            "status": "ok",
            "engine": "fly-brain-engine",
            "version": "0.1.0",
            "demo_mode": cfg.demo_mode,
            "default_connectome": cfg.default_connectome,
            "connectome_ready": conn.get("ready", False),
        }

    @app.get("/v1/capabilities")
    def capabilities() -> dict:
        conn = connectome_data_status(
            cfg.connectome_bundle_dir(cfg.default_connectome), cfg.default_connectome
        )
        return {
            "engine": "lif_sparse",
            "identity": "Barry — MaleCNS v1.0 CNS experiment engine (166,700 neurons)",
            "default_connectome": cfg.default_connectome,
            "connectome_data_dir": str(cfg.connectome_data_dir),
            "connectome": conn,
            "connectome_modes": ["malecns_v1", "barry", "flywire_v783", "procedural"],
            "inject_channels": [
                "sensor_id (e.g. vision.left, synthetic.compass.x)",
                "population:name",
                "neuron:index",
                "bodyId:MaleCNS_root_id",
            ],
            "procedural_scales": ["mini", "medium", "large", "flywire_target"],
            "world_dimensions": [2, 3, 4, 5],
            "inject_endpoint": "/v1/experiments/inject",
            "multiverse_endpoint": "/v1/experiments/multiverse",
            "websocket": "/ws/stream",
        }

    return app
