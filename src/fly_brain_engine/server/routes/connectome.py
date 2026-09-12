from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from fly_brain_engine.connectome.profiles import connectome_data_status
from fly_brain_engine.connectome.generator import load_edges_csv
from fly_brain_engine.core.lif_network import LIFNetwork
from fly_brain_engine.server.deps import StateDep

router = APIRouter(prefix="/v1/connectome", tags=["connectome"])


@router.get("/status")
def connectome_status(state: StateDep, profile: str | None = None) -> dict:
    p = profile or state.settings.default_connectome
    status = connectome_data_status(state.settings.connectome_bundle_dir(p), p)
    status["default_connectome"] = state.settings.default_connectome
    status["data_root"] = str(state.settings.connectome_data_dir)
    return status


@router.get("/profiles")
def list_profiles(state: StateDep) -> dict:
    return {
        "default": state.settings.default_connectome,
        "profiles": {
            "malecns_v1": connectome_data_status(
                state.settings.connectome_bundle_dir("malecns_v1"), "malecns_v1"
            ),
            "flywire_v783": connectome_data_status(
                state.settings.connectome_bundle_dir("flywire_v783"), "flywire_v783"
            ),
        },
    }


class LoadCsvBody(BaseModel):
    path: str
    brain_id: UUID | None = None
    n_neurons: int | None = None


@router.post("/load")
def load_connectome(body: LoadCsvBody, state: StateDep) -> dict:
    try:
        graph = load_edges_csv(body.path, body.n_neurons)
    except OSError as e:
        raise HTTPException(400, str(e)) from e
    if body.brain_id:
        brain = state.brains.get(body.brain_id)
        brain.network = LIFNetwork(graph)
        return {"brain_id": str(body.brain_id), "neurons": graph.n_neurons}
    return {"neurons": graph.n_neurons, "populations": len(graph.population_index)}


@router.get("/populations")
def list_population_names(state: StateDep) -> dict:
    brains = state.brains.list()
    if not brains:
        b = state.brains.create("probe", connectome="procedural", scale="mini")
        idx = b.network.graph.population_index
    else:
        idx = brains[0].network.graph.population_index
    return {"populations": {k: len(v) for k, v in idx.items() if v}}
