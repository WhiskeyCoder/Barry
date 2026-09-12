from __future__ import annotations

import math
from dataclasses import dataclass

from fly_brain_engine.worlds.base import World, WorldEntity, WorldSnapshot


@dataclass
class Agent2D:
    x: float = 0.0
    y: float = 0.0
    heading: float = 0.0


class World2D(World):
    dimension = 2

    def __init__(self, name: str = "arena_2d", size: float = 100.0) -> None:
        super().__init__(name)
        self.size = size
        self.agent = Agent2D()
        self.light = ( -20.0, 0.0)
        self.food = (30.0, 10.0)
        self.hazard = (5.0, -15.0)
        self.walls: list[tuple[float, float, float, float]] = [
            (-size, -size, size, -size),
            (size, -size, size, size),
            (size, size, -size, size),
            (-size, size, -size, -size),
        ]

    def _dist(self, ax: float, ay: float, bx: float, by: float) -> float:
        return math.hypot(ax - bx, ay - by)

    def step(self, dt: float) -> WorldSnapshot:
        return WorldSnapshot(
            world_id=self.id,
            dimension=2,
            time_coordinate=0.0,
            entities=[
                WorldEntity("agent", "fly", [self.agent.x, self.agent.y]),
                WorldEntity("food", "food", list(self.food)),
                WorldEntity("light", "light", list(self.light)),
                WorldEntity("hazard", "hazard", list(self.hazard)),
            ],
        )

    def apply_motor(self, turn: float, forward: float) -> None:
        self.agent.heading += turn * 0.1
        self.agent.x += math.cos(self.agent.heading) * forward * 0.5
        self.agent.y += math.sin(self.agent.heading) * forward * 0.5

    def sensor_payloads(self, agent_position: list[float] | None = None) -> dict[str, float]:
        x, y = self.agent.x, self.agent.y
        d_light = self._dist(x, y, *self.light)
        d_food = self._dist(x, y, *self.food)
        d_hazard = self._dist(x, y, *self.hazard)
        left_angle = math.atan2(self.light[1] - y, self.light[0] - x) - self.agent.heading
        right_angle = math.pi - left_angle
        return {
            "vision.left": max(0.0, 1.0 - d_light / (self.size * 0.8)) * (0.5 + 0.5 * math.cos(left_angle)),
            "vision.right": max(0.0, 1.0 - d_light / (self.size * 0.8)) * (0.5 + 0.5 * math.cos(right_angle)),
            "olfaction.food": max(0.0, 1.0 - d_food / (self.size * 0.5)),
            "hazard.proximity": max(0.0, 1.0 - d_hazard / 20.0),
        }
