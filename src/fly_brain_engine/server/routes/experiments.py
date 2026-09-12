from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from fly_brain_engine.server.deps import StateDep

router = APIRouter(prefix="/v1/experiments", tags=["experiments"])


class CreateSessionBody(BaseModel):
    name: str
    brain_id: UUID
    dimension: int = 2


@router.post("/sessions")
def create_session(body: CreateSessionBody, state: StateDep) -> dict:
    try:
        state.brains.get(body.brain_id)
    except KeyError as e:
        raise HTTPException(404, "brain not found") from e
    sess = state.experiments.create_session(body.name, body.brain_id, body.dimension)
    return {
        "session_id": str(sess.id),
        "world_id": str(sess.world_id),
        "dimension": sess.dimension,
    }


@router.post("/sessions/{session_id}/step")
def session_step(session_id: UUID, state: StateDep, milliseconds: float = 10.0) -> dict:
    try:
        result = state.experiments.closed_loop_step(session_id, milliseconds)
    except KeyError as e:
        raise HTTPException(404, "session not found") from e
    world = result["world"]
    return {
        "motors": result.get("motors"),
        "payloads": result.get("payloads"),
        "world": {
            "dimension": world.dimension,
            "time_coordinate": world.time_coordinate,
            "fields": world.fields,
        },
    }


class InjectBody(BaseModel):
    """Universal inject — send arbitrary experimental data to a brain."""

    brain_id: UUID
    channel: str
    data: Any
    step_ms: float | None = 10.0


@router.post("/inject")
def inject_data(body: InjectBody, state: StateDep) -> dict:
    """Primary endpoint for external Python experiment scripts."""
    try:
        b = state.brains.get(body.brain_id)
    except KeyError as e:
        raise HTTPException(404, "brain not found") from e

    ch = body.channel
    if ch.startswith("neuron:"):
        nid = int(ch.split(":", 1)[1])
        val = float(body.data)
        b.network.stimulate_rate([nid], val)
    elif ch.startswith("bodyId:"):
        body_id = int(ch.split(":", 1)[1])
        idx = b.network.index_for_body_id(body_id)
        if idx is None:
            raise HTTPException(404, f"unknown MaleCNS/FlyWire bodyId {body_id}")
        b.network.stimulate_rate([idx], float(body.data))
    elif ch.startswith("population:"):
        pop = ch.split(":", 1)[1]
        ids = b.network.population_ids(pop)
        b.network.stimulate_rate(ids, float(body.data))
    else:
        try:
            b.sensors.set(ch, body.data)
        except KeyError:
            b.sensors.add(ch, "synthetic_mag", synthetic=True)
            b.sensors.set(ch, body.data)

    motors = {}
    if body.step_ms:
        b.step(body.step_ms)
        motors = b.motors.decode_all(b.network)

    return {
        "accepted": True,
        "channel": ch,
        "time_ms": b.network._state.time_ms,
        "motors": motors,
    }


class CreateMultiverseBody(BaseModel):
    """N cloned Barry instances — same seed, optional per-universe inject (6th sense, quantum tag, etc.)."""

    name: str
    count: int = 10
    connectome: str | None = None
    scale: str = "mini"
    seed: int = 42
    variants: list[dict[str, Any]] | None = None


@router.post("/multiverse")
def create_multiverse(body: CreateMultiverseBody, state: StateDep) -> dict:
    from fly_brain_engine.connectome.profiles import ConnectomeDataError

    connectome = body.connectome
    if connectome is None and state.settings.demo_mode:
        connectome = "procedural"
    try:
        ens = state.ensembles.create_multiverse(
            body.name,
            body.count,
            connectome=connectome,
            scale=body.scale,
            seed=body.seed,
            variants=body.variants,
        )
    except ConnectomeDataError as e:
        raise HTTPException(503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {
        "ensemble_id": str(ens.id),
        "name": ens.name,
        "brain_ids": [str(b) for b in ens.brain_ids],
        "count": len(ens.brain_ids),
    }


@router.get("/multiverse/{ensemble_id}")
def get_multiverse(ensemble_id: UUID, state: StateDep) -> dict:
    try:
        ens = state.ensembles.get(ensemble_id)
    except KeyError as e:
        raise HTTPException(404, "ensemble not found") from e
    brains = []
    for bid in ens.brain_ids:
        b = state.brains.get(bid)
        brains.append(
            {
                "id": str(bid),
                "name": b.name,
                "universe_index": b.metadata.get("universe_index"),
                "universe_label": b.metadata.get("universe_label"),
                "variant": b.metadata.get("universe_variant"),
            }
        )
    return {"ensemble_id": str(ens.id), "name": ens.name, "brains": brains}


@router.post("/multiverse/{ensemble_id}/step")
def step_multiverse(ensemble_id: UUID, state: StateDep, milliseconds: float = 10.0) -> dict:
    try:
        results = state.ensembles.step_all(ensemble_id, milliseconds)
    except KeyError as e:
        raise HTTPException(404, "ensemble not found") from e
    return {"ensemble_id": str(ensemble_id), "step_ms": milliseconds, "universes": results}
