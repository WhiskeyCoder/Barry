from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from fly_brain_engine.config import Settings
from fly_brain_engine.connectome.profiles import ConnectomeProfile, load_real_connectome
from fly_brain_engine.core.lif_network import LIFNetwork, LIFParams
from fly_brain_engine.motors.decoders import MotorRegistry
from fly_brain_engine.senses.channels import SensorRegistry


@dataclass
class FlyBrain:
    id: UUID
    name: str
    network: LIFNetwork
    sensors: SensorRegistry = field(default_factory=SensorRegistry)
    motors: MotorRegistry = field(default_factory=MotorRegistry)
    paused: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        name: str,
        *,
        connectome: str | None = None,
        scale: str = "medium",
        seed: int = 42,
        dt_ms: float = 0.1,
        settings: Settings | None = None,
    ) -> FlyBrain:
        cfg = settings or Settings.load()
        mode = ConnectomeProfile.normalize(connectome or cfg.default_connectome)

        if mode == ConnectomeProfile.PROCEDURAL:
            net = LIFNetwork.from_scale(scale=scale, seed=seed, dt_ms=dt_ms)
            meta = {"connectome": "procedural", "scale": scale, "seed": seed}
        else:
            bundle_dir = cfg.connectome_bundle_dir(mode.value)
            graph = load_real_connectome(bundle_dir, mode.value)
            params = LIFParams.barry()
            params.dt_ms = dt_ms
            net = LIFNetwork(graph, params)
            meta = {
                "connectome": mode.value,
                "connectome_source": graph.source,
                "neurons": graph.n_neurons,
                "provenance": graph.provenance,
            }

        brain = cls(id=uuid4(), name=name, network=net, metadata=meta)
        brain.sensors.install_defaults(net)
        brain.motors.install_defaults(net)
        return brain

    def step(self, ms: float) -> None:
        if self.paused:
            return
        self.sensors.flush_to_network(self.network)
        self.network.step(ms)

    def snapshot(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "network": self.network.get_state_blob(),
            "sensors": self.sensors.export(),
            "motors": self.motors.export(),
            "metadata": self.metadata,
        }

    def restore(self, data: dict[str, Any]) -> None:
        self.name = data.get("name", self.name)
        self.network.restore_state_blob(data["network"])
        self.sensors.import_config(data.get("sensors", {}))
        self.motors.import_config(data.get("motors", {}))
        self.metadata = data.get("metadata", {})

    def clone(self, new_name: str) -> FlyBrain:
        snap = self.snapshot()
        net = LIFNetwork(self.network.graph, self.network.params)
        net.restore_state_blob(snap["network"])
        clone = FlyBrain(id=uuid4(), name=new_name, network=net)
        clone.sensors.import_config(snap.get("sensors", {}))
        clone.motors.import_config(snap.get("motors", {}))
        clone.metadata = dict(snap.get("metadata", {}))
        return clone
