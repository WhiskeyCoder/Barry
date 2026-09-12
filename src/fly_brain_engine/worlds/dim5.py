from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import numpy as np

from fly_brain_engine.brains.brain_engine import FlyBrain
from fly_brain_engine.worlds.base import World, WorldSnapshot
from fly_brain_engine.worlds.dim4 import World4D


@dataclass
class QuantumCoupling:
    """Experimental metaphor: entangled sensor mixing across brains."""

    brain_ids: list[UUID]
    coupling_strength: float = 0.5
    phase_offsets: list[float] = field(default_factory=list)


class World5D(World):
    """
    5D experimental space: 4D world + ensemble dimension (multi-brain quantum-time).
    'Quantum' here means superposed sensory mixing and synchronized stepping — not physics simulation.
    """

    dimension = 5

    def __init__(self, name: str = "ensemble_5d") -> None:
        super().__init__(name)
        self.base_4d = World4D(name + "_4d")
        self.brains: dict[str, FlyBrain] = {}
        self.coupling = QuantumCoupling(brain_ids=[])
        self.superposition_state: np.ndarray | None = None
        self.global_phase = 0.0

    def attach_brain(self, key: str, brain: FlyBrain) -> None:
        self.brains[key] = brain
        self.coupling.brain_ids = [b.id for b in self.brains.values()]
        if not self.coupling.phase_offsets:
            self.coupling.phase_offsets = [0.0] * len(self.brains)

    def step(self, dt: float) -> WorldSnapshot:
        self.global_phase += dt * 0.01
        snap = self.base_4d.step(dt)
        snap.dimension = 5
        snap.fields["brain_count"] = len(self.brains)
        snap.fields["coupling"] = self.coupling.coupling_strength
        snap.fields["global_phase"] = self.global_phase
        return snap

    def entangle_sensors(self, sensor_id: str, values: list[Any]) -> dict[str, Any]:
        """Mix sensor values across brains with phase-weighted coupling."""
        keys = list(self.brains.keys())
        if not keys:
            return {}
        n = len(keys)
        vec = np.array([float(v) if not isinstance(v, list) else sum(v) / len(v) for v in values[:n]])
        if len(vec) < n:
            vec = np.pad(vec, (0, n - len(vec)), constant_values=0.0)
        phases = np.array(self.coupling.phase_offsets[:n] or [0.0] * n)
        mix = self.coupling.coupling_strength * np.cos(phases + self.global_phase)
        superposed = vec * (1 - self.coupling.coupling_strength) + mix * vec.mean()
        self.superposition_state = superposed
        applied: dict[str, Any] = {}
        for i, key in enumerate(keys):
            brain = self.brains[key]
            val = float(superposed[i])
            if sensor_id not in brain.sensors._channels:
                brain.sensors.add(sensor_id, "synthetic_quantum", synthetic=True)
            brain.sensors.set(sensor_id, val)
            applied[key] = val
        return applied

    def synchronized_step(self, ms: float) -> dict[str, dict[str, float]]:
        motors: dict[str, dict[str, float]] = {}
        payloads = self.base_4d.sensor_payloads()
        for key, brain in self.brains.items():
            for sid, val in payloads.items():
                if sid in brain.sensors._channels:
                    brain.sensors.set(sid, val)
            brain.step(ms)
            motors[key] = brain.motors.decode_all(brain.network)
        return motors

    def sensor_payloads(self, agent_position: list[float] | None = None) -> dict[str, float]:
        base = self.base_4d.sensor_payloads(agent_position)
        base["quantum.coherence"] = float(
            np.linalg.norm(self.superposition_state) if self.superposition_state is not None else 0.0
        )
        return base
