from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

from fly_brain_engine.connectome.profiles import ConnectomeProfile


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FBE_", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8090
    default_scale: str = "medium"
    default_connectome: str = "malecns_v1"
    connectome_data_dir: Path = Path("./connectome-data")
    demo_mode: bool = False
    dt_ms: float = 0.1
    device: str = "auto"
    storage_dir: Path = Path("./engine-data")

    @property
    def barry_data_dir(self) -> Path:
        """Legacy alias for connectome_data_dir."""
        return self.connectome_data_dir

    def connectome_bundle_dir(self, profile: str | None = None) -> Path:
        p = ConnectomeProfile.normalize(profile or self.default_connectome)
        base = self.connectome_data_dir.expanduser().resolve()
        if p == ConnectomeProfile.MALECNS_V1:
            nested = base / "malecns_v1"
            return nested if nested.is_dir() else base
        if p == ConnectomeProfile.FLYWIRE_V783:
            nested = base / "flywire"
            return nested if nested.is_dir() else base
        return base

    @classmethod
    def load(cls, config_path: Path | None = None) -> Settings:
        data: dict[str, Any] = {}
        path = config_path or Path(__file__).resolve().parents[2] / "config" / "default.yaml"
        if not path.is_file():
            path = Path("config/default.yaml")
        if path.is_file():
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if srv := raw.get("server"):
                data["host"] = srv.get("host", "0.0.0.0")
                data["port"] = srv.get("port", 8090)
            if eng := raw.get("engine"):
                data["default_scale"] = eng.get("default_scale", "medium")
                data["default_connectome"] = eng.get("default_connectome", "malecns_v1")
                data["dt_ms"] = eng.get("dt_ms", 0.1)
                data["device"] = eng.get("device", "auto")
                if cdir := eng.get("connectome_data_dir"):
                    data["connectome_data_dir"] = Path(cdir)
                elif bdir := eng.get("barry_data_dir"):
                    data["connectome_data_dir"] = Path(bdir)
                data["demo_mode"] = bool(eng.get("demo_mode", False))
            if stor := raw.get("storage"):
                data["storage_dir"] = Path(stor.get("directory", "./engine-data"))
        inst = cls(**data)
        import os

        if os.environ.get("FBE_DEMO", "").lower() in ("1", "true", "yes"):
            inst.demo_mode = True
            inst.default_connectome = "procedural"
        return inst
