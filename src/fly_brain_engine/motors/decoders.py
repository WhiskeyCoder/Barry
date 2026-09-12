from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fly_brain_engine.core.lif_network import LIFNetwork


@dataclass
class MotorChannel:
    output_id: str
    population: str
    kind: str = "mean_rate"


class MotorRegistry:
    def __init__(self) -> None:
        self._channels: dict[str, MotorChannel] = {}

    def install_defaults(self, net: LIFNetwork) -> None:
        for oid, pop in [
            ("turn", "DNa02_steering"),
            ("escape", "DNp09_escape"),
            ("walk_forward", "MDN_walk"),
            ("wing_burst", "GF_giant_fiber"),
        ]:
            self._channels[oid] = MotorChannel(oid, pop)

    def decode_all(self, net: LIFNetwork) -> dict[str, float]:
        out: dict[str, float] = {}
        for oid, ch in self._channels.items():
            rate = net.mean_population_rate(ch.population)
            if ch.kind == "mean_rate":
                out[oid] = min(1.0, rate / 50.0)
            else:
                out[oid] = rate
        # differential steering proxy: left vs right vision populations
        left = net.mean_population_rate("photoreceptor_R1_R6_left")
        right = net.mean_population_rate("photoreceptor_R1_R6_right")
        out["vision_balance"] = (left - right) / max(1.0, left + right)
        return out

    def export(self) -> dict[str, Any]:
        return {oid: {"population": c.population, "kind": c.kind} for oid, c in self._channels.items()}

    def import_config(self, data: dict[str, Any]) -> None:
        for oid, cfg in data.items():
            self._channels[oid] = MotorChannel(oid, cfg["population"], cfg.get("kind", "mean_rate"))
