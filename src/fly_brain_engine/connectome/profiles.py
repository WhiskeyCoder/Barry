from __future__ import annotations

import pickle
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from fly_brain_engine.connectome.generator import ConnectomeGraph


class ConnectomeDataError(FileNotFoundError):
    """Raised when a real connectome bundle is missing or invalid."""


class ConnectomeProfile(str, Enum):
    MALECNS_V1 = "malecns_v1"
    FLYWIRE_V783 = "flywire_v783"
    PROCEDURAL = "procedural"

    @classmethod
    def normalize(cls, name: str | None) -> ConnectomeProfile:
        if not name or name in ("barry", "default", "malecns", "malecns_v1"):
            return cls.MALECNS_V1
        if name in ("flywire", "flywire_v783", "fafb_783"):
            return cls.FLYWIRE_V783
        if name == "procedural":
            return cls.PROCEDURAL
        raise ValueError(f"unknown connectome profile: {name}")


@dataclass(frozen=True)
class ConnectomeStatus:
    profile: str
    ready: bool
    data_dir: str
    detail: dict

    def to_dict(self) -> dict:
        return {"profile": self.profile, "ready": self.ready, "data_dir": self.data_dir, **self.detail}


def connectome_data_status(data_dir: Path, profile: str | None = None) -> dict:
    from fly_brain_engine.connectome import flywire_loader, malecns_loader

    p = ConnectomeProfile.normalize(profile or "malecns_v1")
    if p == ConnectomeProfile.MALECNS_V1:
        return malecns_loader.malecns_data_status(data_dir)
    if p == ConnectomeProfile.FLYWIRE_V783:
        return flywire_loader.flywire_data_status(data_dir)
    return {"profile": "procedural", "ready": True, "data_dir": str(data_dir)}


def load_real_connectome(
    data_dir: Path,
    profile: str,
    *,
    use_cache: bool = True,
) -> ConnectomeGraph:
    from fly_brain_engine.connectome import flywire_loader, malecns_loader

    p = ConnectomeProfile.normalize(profile)
    if p == ConnectomeProfile.MALECNS_V1:
        return malecns_loader.load_malecns_connectome(data_dir, use_cache=use_cache)
    if p == ConnectomeProfile.FLYWIRE_V783:
        return flywire_loader.load_flywire_connectome(data_dir, use_cache=use_cache)
    raise ValueError("load_real_connectome called with procedural")
