from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fly_brain_engine.brains.brain_engine import FlyBrain
from fly_brain_engine.brains.registry import BrainRegistry
from fly_brain_engine.worlds.base import World
from fly_brain_engine.worlds.dim2 import World2D
from fly_brain_engine.worlds.dim3 import World3D
from fly_brain_engine.worlds.dim4 import World4D
from fly_brain_engine.worlds.dim5 import World5D


@dataclass
class ExperimentSession:
    id: UUID
    name: str
    brain_id: UUID | None = None
    world_id: UUID | None = None
    dimension: int = 2
    log: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ExperimentHub:
    def __init__(self, brains: BrainRegistry) -> None:
        self.brains = brains
        self.worlds: dict[UUID, World] = {}
        self.sessions: dict[UUID, ExperimentSession] = {}

    def create_world(self, dimension: int, name: str) -> World:
        if dimension == 2:
            w: World = World2D(name)
        elif dimension == 3:
            w = World3D(name)
        elif dimension == 4:
            w = World4D(name)
        elif dimension == 5:
            w = World5D(name)
        else:
            raise ValueError("dimension must be 2, 3, 4, or 5")
        self.worlds[w.id] = w
        return w

    def get_world(self, world_id: UUID) -> World:
        if world_id not in self.worlds:
            raise KeyError(str(world_id))
        return self.worlds[world_id]

    def create_session(self, name: str, brain_id: UUID, dimension: int = 2) -> ExperimentSession:
        world = self.create_world(dimension, f"{name}_world")
        if dimension == 5 and isinstance(world, World5D):
            brain = self.brains.get(brain_id)
            world.attach_brain("primary", brain)
        sess = ExperimentSession(
            id=uuid4(),
            name=name,
            brain_id=brain_id,
            world_id=world.id,
            dimension=dimension,
        )
        self.sessions[sess.id] = sess
        return sess

    def closed_loop_step(
        self,
        session_id: UUID,
        ms: float,
    ) -> dict[str, Any]:
        sess = self.sessions[session_id]
        world = self.worlds[sess.world_id]  # type: ignore[arg-type]
        brain = self.brains.get(sess.brain_id)  # type: ignore[arg-type]

        if isinstance(world, World5D):
            world_snap = world.step(ms / 1000.0)
            motors = world.synchronized_step(ms)
            result = {"world": world_snap, "motors": motors}
        else:
            world_snap = world.step(ms / 1000.0)
            payloads = world.sensor_payloads()
            for sid, val in payloads.items():
                try:
                    brain.sensors.set(sid, val)
                except KeyError:
                    pass
            brain.step(ms)
            motors = brain.motors.decode_all(brain.network)
            if isinstance(world, World2D):
                world.apply_motor(motors.get("turn", 0) * 2 - 1, motors.get("walk_forward", 0))
            elif isinstance(world, World3D):
                world.apply_motor(motors.get("walk_forward", 0), motors.get("turn", 0), 0.0)
            result = {"world": world_snap, "motors": motors, "payloads": payloads}

        sess.log.append(f"step {ms}ms dim={sess.dimension}")
        return result

    def save_session(self, storage: Path, session_id: UUID) -> Path:
        sess = self.sessions[session_id]
        brain = self.brains.get(sess.brain_id)  # type: ignore[arg-type]
        out = storage / "sessions" / str(session_id)
        out.mkdir(parents=True, exist_ok=True)
        (out / "session.json").write_text(json.dumps({"name": sess.name, "dimension": sess.dimension}, indent=2))
        (out / "brain.json").write_text(json.dumps(brain.snapshot(), indent=2))
        return out
