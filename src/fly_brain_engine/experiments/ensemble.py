from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from fly_brain_engine.brains.brain_engine import FlyBrain
from fly_brain_engine.brains.registry import BrainRegistry


@dataclass
class UniverseEnsemble:
    id: UUID
    name: str
    brain_ids: list[UUID] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class EnsembleHub:
    """Multiple Barry instances (universes) for parallel experiments."""

    def __init__(self, brains: BrainRegistry) -> None:
        self.brains = brains
        self.ensembles: dict[UUID, UniverseEnsemble] = {}

    def create_multiverse(
        self,
        name: str,
        count: int,
        *,
        connectome: str | None,
        scale: str,
        seed: int,
        variants: list[dict[str, Any]] | None = None,
    ) -> UniverseEnsemble:
        if count < 1 or count > 64:
            raise ValueError("count must be between 1 and 64")
        variants = variants or [{} for _ in range(count)]
        if len(variants) < count:
            variants = variants + [{} for _ in range(count - len(variants))]

        template = self.brains.create(
            f"{name}_template",
            connectome=connectome,
            scale=scale,
            seed=seed,
        )
        template.metadata["ensemble_role"] = "template"
        ids: list[UUID] = []

        for i in range(count):
            label = str(variants[i].get("label", f"universe_{i}"))
            if i == 0:
                brain = template
                brain.name = f"{name}_{label}"
            else:
                brain = template.clone(f"{name}_{label}")
                self.brains.register(brain)
            brain.metadata.update(
                {
                    "ensemble": name,
                    "universe_index": i,
                    "universe_label": label,
                    "universe_variant": variants[i],
                }
            )
            inject_map = variants[i].get("initial_inject") or {}
            if isinstance(inject_map, dict):
                for channel, val in inject_map.items():
                    if str(channel).startswith("synthetic."):
                        pop = variants[i].get("synthetic_population", "synthetic_mag")
                        if channel not in {s["sensor_id"] for s in brain.sensors.list()}:
                            brain.sensors.add(str(channel), pop, synthetic=True)
                    try:
                        brain.sensors.set(str(channel), val)
                    except KeyError:
                        brain.sensors.add(str(channel), "synthetic_mag", synthetic=True)
                        brain.sensors.set(str(channel), val)
            ids.append(brain.id)

        ens = UniverseEnsemble(
            id=uuid4(),
            name=name,
            brain_ids=ids,
            metadata={"count": count, "seed": seed, "connectome": connectome or "default"},
        )
        self.ensembles[ens.id] = ens
        return ens

    def get(self, ensemble_id: UUID) -> UniverseEnsemble:
        if ensemble_id not in self.ensembles:
            raise KeyError(str(ensemble_id))
        return self.ensembles[ensemble_id]

    def step_all(self, ensemble_id: UUID, ms: float) -> list[dict[str, Any]]:
        ens = self.get(ensemble_id)
        out: list[dict[str, Any]] = []
        for bid in ens.brain_ids:
            b = self.brains.get(bid)
            b.step(ms)
            out.append(
                {
                    "brain_id": str(bid),
                    "universe_index": b.metadata.get("universe_index"),
                    "universe_label": b.metadata.get("universe_label"),
                    "motors": b.motors.decode_all(b.network),
                    "spikes_last_step": int(b.network._state.spikes.sum()),
                    "time_ms": b.network._state.time_ms,
                }
            )
        return out
