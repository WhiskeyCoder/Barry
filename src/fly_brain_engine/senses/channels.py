from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fly_brain_engine.core.lif_network import LIFNetwork


@dataclass
class SensorChannel:
    sensor_id: str
    population: str
    gain: float = 1.0
    synthetic: bool = False
    pending_value: Any = None

    def encode_to_hz(self, value: Any) -> float:
        if isinstance(value, (list, tuple)):
            value = sum(float(x) for x in value) / len(value)
        v = float(value) * self.gain
        return max(0.0, min(200.0, v * 100.0))


class SensorRegistry:
    def __init__(self) -> None:
        self._channels: dict[str, SensorChannel] = {}

    def install_defaults(self, net: LIFNetwork) -> None:
        defaults = [
            ("vision.left", "photoreceptor_R1_R6_left", False),
            ("vision.right", "photoreceptor_R1_R6_right", False),
            ("olfaction.food", "ORN_glomeruli", False),
            ("gustation.sugar", "ORN_glomeruli", False),
            ("proprio.legs", "proprio_leg", False),
            ("auditory.johnston", "johnstons_organ", False),
        ]
        for sid, pop, syn in defaults:
            self._channels[sid] = SensorChannel(sensor_id=sid, population=pop, synthetic=syn)

    def add(self, sensor_id: str, population: str, gain: float = 1.0, synthetic: bool = True) -> None:
        self._channels[sensor_id] = SensorChannel(sensor_id, population, gain, synthetic)

    def set(self, sensor_id: str, value: Any) -> None:
        if sensor_id not in self._channels:
            raise KeyError(sensor_id)
        self._channels[sensor_id].pending_value = value

    def flush_to_network(self, net: LIFNetwork) -> None:
        for ch in self._channels.values():
            if ch.pending_value is None:
                continue
            hz = ch.encode_to_hz(ch.pending_value)
            ids = net.population_ids(ch.population)
            if ids:
                net.stimulate_rate(ids, hz)
            ch.pending_value = None

    def export(self) -> dict[str, Any]:
        return {
            sid: {
                "population": c.population,
                "gain": c.gain,
                "synthetic": c.synthetic,
            }
            for sid, c in self._channels.items()
        }

    def import_config(self, data: dict[str, Any]) -> None:
        for sid, cfg in data.items():
            self._channels[sid] = SensorChannel(
                sensor_id=sid,
                population=cfg["population"],
                gain=cfg.get("gain", 1.0),
                synthetic=cfg.get("synthetic", False),
            )

    def list(self) -> list[dict[str, Any]]:
        return [
            {"sensor_id": c.sensor_id, "population": c.population, "synthetic": c.synthetic}
            for c in self._channels.values()
        ]
