from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from fly_brain_engine.server.deps import StateDep
from fly_brain_engine.worlds.dim4 import World4D
from fly_brain_engine.worlds.dim5 import World5D

router = APIRouter(prefix="/v1/worlds", tags=["worlds"])


class CreateWorldBody(BaseModel):
    name: str
    dimension: int = 2


@router.post("")
def create_world(body: CreateWorldBody, state: StateDep) -> dict:
    w = state.experiments.create_world(body.dimension, body.name)
    return {"id": str(w.id), "name": w.name, "dimension": w.dimension}


@router.get("/{world_id}")
def get_world(world_id: UUID, state: StateDep) -> dict:
    try:
        w = state.experiments.get_world(world_id)
    except KeyError as e:
        raise HTTPException(404, "world not found") from e
    return {"id": str(w.id), "name": w.name, "dimension": w.dimension}


@router.post("/{world_id}/step")
def world_step(world_id: UUID, state: StateDep, dt: float = 0.01) -> dict:
    w = state.experiments.get_world(world_id)
    snap = w.step(dt)
    return {
        "dimension": snap.dimension,
        "time_coordinate": snap.time_coordinate,
        "entities": [e.__dict__ for e in snap.entities],
        "fields": snap.fields,
    }


@router.get("/{world_id}/sensors")
def world_sensors(world_id: UUID, state: StateDep) -> dict:
    w = state.experiments.get_world(world_id)
    return w.sensor_payloads()


class BranchBody(BaseModel):
    branch_id: str
    label: str = "fork"


@router.post("/{world_id}/timeline/branch")
def branch_timeline(world_id: UUID, body: BranchBody, state: StateDep) -> dict:
    w = state.experiments.get_world(world_id)
    if not isinstance(w, World4D):
        raise HTTPException(400, "world is not 4D")
    bid = w.branch_timeline(body.branch_id, body.label)
    return {"active_branch": bid}


class EntangleBody(BaseModel):
    sensor_id: str
    values: list[Any]


@router.post("/{world_id}/quantum/entangle")
def quantum_entangle(world_id: UUID, body: EntangleBody, state: StateDep) -> dict:
    w = state.experiments.get_world(world_id)
    if not isinstance(w, World5D):
        raise HTTPException(400, "world is not 5D")
    return w.entangle_sensors(body.sensor_id, body.values)


class AttachBrainBody(BaseModel):
    key: str
    brain_id: UUID


@router.post("/{world_id}/brains/attach")
def attach_brain(world_id: UUID, body: AttachBrainBody, state: StateDep) -> dict:
    w = state.experiments.get_world(world_id)
    if not isinstance(w, World5D):
        raise HTTPException(400, "world is not 5D")
    brain = state.brains.get(body.brain_id)
    w.attach_brain(body.key, brain)
    return {"attached": body.key, "brain_id": str(body.brain_id)}
