from __future__ import annotations

import math

from fly_brain_engine.worlds.base import World, WorldEntity, WorldSnapshot


class World3D(World):
    dimension = 3

    def __init__(self, name: str = "volume_3d", extent: float = 50.0) -> None:
        super().__init__(name)
        self.extent = extent
        self.pos = [0.0, 0.0, 1.0]
        self.vel = [0.0, 0.0, 0.0]
        self.obstacles: list[tuple[float, float, float, float]] = [
            (10, 0, 0, 5),
            (-8, 6, 2, 4),
            (0, -12, 1, 6),
        ]
        self.odor = (15.0, 5.0, 0.5)

    def step(self, dt: float) -> WorldSnapshot:
        for i in range(3):
            self.pos[i] += self.vel[i] * dt
        return WorldSnapshot(
            world_id=self.id,
            dimension=3,
            time_coordinate=0.0,
            entities=[WorldEntity("agent", "fly", list(self.pos))],
            fields={"wind": [0.01, 0.0, 0.0]},
        )

    def apply_motor(self, thrust: float, yaw: float, climb: float) -> None:
        self.vel[0] += thrust * math.cos(yaw) * 0.1
        self.vel[1] += thrust * math.sin(yaw) * 0.1
        self.vel[2] += climb * 0.05

    def sensor_payloads(self, agent_position: list[float] | None = None) -> dict[str, float]:
        x, y, z = self.pos
        ox, oy, oz = self.odor
        d = math.sqrt((x - ox) ** 2 + (y - oy) ** 2 + (z - oz) ** 2)
        nearest_obs = min(
            (math.sqrt((x - a) ** 2 + (y - b) ** 2 + (z - c) ** 2) - r for a, b, c, r in self.obstacles),
            default=999.0,
        )
        return {
            "vision.left": max(0.0, 1.0 - nearest_obs / 30.0),
            "vision.right": max(0.0, 1.0 - nearest_obs / 35.0),
            "olfaction.food": max(0.0, 1.0 - d / 40.0),
            "proprio.legs": min(1.0, abs(z) / 10.0),
        }
