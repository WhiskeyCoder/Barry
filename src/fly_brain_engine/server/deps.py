from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from fly_brain_engine.brains.registry import BrainRegistry
from fly_brain_engine.config import Settings
from fly_brain_engine.experiments.ensemble import EnsembleHub
from fly_brain_engine.experiments.session import ExperimentHub


@dataclass
class EngineState:
    settings: Settings
    brains: BrainRegistry
    experiments: ExperimentHub
    ensembles: EnsembleHub


def get_state(request: Request) -> EngineState:
    return request.app.state.engine  # type: ignore[attr-defined]


StateDep = Annotated[EngineState, Depends(get_state)]
