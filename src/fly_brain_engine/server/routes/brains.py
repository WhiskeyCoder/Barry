from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from fly_brain_engine.server.deps import StateDep

router = APIRouter(prefix="/v1/brains", tags=["brains"])


class CreateBrainBody(BaseModel):
    name: str
    connectome: str | None = None  # barry | procedural; default from server config
    scale: str = "medium"
    seed: int = 42


@router.post("")
def create_brain(body: CreateBrainBody, state: StateDep) -> dict:
    from fly_brain_engine.connectome.profiles import ConnectomeDataError

    try:
        b = state.brains.create(
            body.name,
            connectome=body.connectome,
            scale=body.scale,
            seed=body.seed,
        )
    except ConnectomeDataError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    g = b.network.graph
    return {
        "id": str(b.id),
        "name": b.name,
        "neurons": b.network.n,
        "connectome": b.metadata.get("connectome"),
        "connectome_source": getattr(g, "source", None),
        "populations": {k: len(v) for k, v in g.population_index.items() if v},
    }


@router.get("")
def list_brains(state: StateDep) -> list[dict]:
    return [{"id": str(b.id), "name": b.name, "neurons": b.network.n} for b in state.brains.list()]


@router.get("/{brain_id}")
def get_brain(brain_id: UUID, state: StateDep) -> dict:
    try:
        b = state.brains.get(brain_id)
    except KeyError as e:
        raise HTTPException(404, "brain not found") from e
    return {
        "id": str(b.id),
        "name": b.name,
        "neurons": b.network.n,
        "time_ms": b.network._state.time_ms,
        "sensors": b.sensors.list(),
        "motors": list(b.motors._channels.keys()),
    }


@router.post("/{brain_id}/step")
def step_brain(brain_id: UUID, state: StateDep, milliseconds: float = 10.0) -> dict:
    b = state.brains.get(brain_id)
    b.step(milliseconds)
    return {
        "time_ms": b.network._state.time_ms,
        "motors": b.motors.decode_all(b.network),
        "spikes_last_step": int(b.network._state.spikes.sum()),
    }


class StimBody(BaseModel):
    neurons: list[int] = Field(default_factory=list)
    population: str | None = None
    hz: float = 50.0
    duration_ms: float | None = None


@router.post("/{brain_id}/stimulate")
def stimulate(brain_id: UUID, body: StimBody, state: StateDep) -> dict:
    b = state.brains.get(brain_id)
    ids = body.neurons
    if body.population:
        ids = b.network.population_ids(body.population)
    b.network.stimulate_rate(ids, body.hz, body.duration_ms)
    return {"stimulated": len(ids)}


class SensorValueBody(BaseModel):
    value: Any


@router.post("/{brain_id}/sensors/{sensor_id}")
def sensor_input(brain_id: UUID, sensor_id: str, body: SensorValueBody, state: StateDep) -> dict:
    try:
        b = state.brains.get(brain_id)
    except KeyError as e:
        raise HTTPException(404, "brain not found") from e
    try:
        b.sensors.set(sensor_id, body.value)
    except KeyError as e:
        raise HTTPException(404, "sensor not found") from e
    return {"ok": True}


class AddSensorBody(BaseModel):
    sensor_id: str
    population: str = "synthetic_mag"
    gain: float = 1.0
    synthetic: bool = True


@router.post("/{brain_id}/sensors")
def add_sensor(brain_id: UUID, body: AddSensorBody, state: StateDep) -> dict:
    b = state.brains.get(brain_id)
    b.sensors.add(body.sensor_id, body.population, body.gain, body.synthetic)
    return {"created": body.sensor_id}


@router.get("/{brain_id}/activity")
def activity(
    brain_id: UUID,
    state: StateDep,
    population: str | None = None,
    limit: int = 100,
) -> dict:
    b = state.brains.get(brain_id)
    ids = b.network.population_ids(population) if population else list(range(min(limit, b.network.n)))
    rates = b.network.read_rates(ids[:limit])
    return {"rates": rates}


@router.post("/{brain_id}/clone")
def clone_brain(brain_id: UUID, state: StateDep, name: str) -> dict:
    parent = state.brains.get(brain_id)
    clone = parent.clone(name)
    state.brains.register(clone)
    return {"id": str(clone.id), "name": clone.name}


@router.get("/{brain_id}/snapshot")
def snapshot(brain_id: UUID, state: StateDep) -> dict:
    return state.brains.get(brain_id).snapshot()
