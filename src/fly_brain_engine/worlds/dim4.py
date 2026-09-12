from __future__ import annotations

from dataclasses import dataclass

from fly_brain_engine.worlds.base import World, WorldSnapshot
from fly_brain_engine.worlds.dim3 import World3D


@dataclass
class TimelineBranch:
    branch_id: str
    parent_id: str | None
    t_world: float
    label: str
    snapshot: dict | None = None


class World4D(World):
    """
    4D world: 3D space + navigable world-time coordinate.
    Supports branching timelines for mental time-travel experiments (simulation metaphor).
    """

    dimension = 4

    def __init__(self, name: str = "hyperspace_4d") -> None:
        super().__init__(name)
        self.spatial = World3D(name + "_spatial")
        self.t_world = 0.0
        self.branches: dict[str, TimelineBranch] = {
            "main": TimelineBranch("main", None, 0.0, "origin"),
        }
        self.active_branch = "main"
        self._history: list[dict] = []

    def step(self, dt: float) -> WorldSnapshot:
        self.t_world += dt
        snap = self.spatial.step(dt)
        snap.dimension = 4
        snap.time_coordinate = self.t_world
        snap.fields["active_branch"] = self.active_branch
        snap.fields["branch_count"] = len(self.branches)
        self.branches[self.active_branch].t_world = self.t_world
        return snap

    def branch_timeline(self, new_branch_id: str, label: str = "fork") -> str:
        parent = self.branches[self.active_branch]
        self.branches[new_branch_id] = TimelineBranch(
            new_branch_id,
            parent.branch_id,
            self.t_world,
            label,
            snapshot={"pos": list(self.spatial.pos), "vel": list(self.spatial.vel)},
        )
        self.active_branch = new_branch_id
        return new_branch_id

    def rewind(self, delta_t: float) -> None:
        self.t_world = max(0.0, self.t_world - delta_t)

    def sensor_payloads(self, agent_position: list[float] | None = None) -> dict[str, float]:
        base = self.spatial.sensor_payloads(agent_position)
        base["time.warp"] = min(1.0, self.t_world / 1000.0)
        base["timeline.depth"] = len(self.branches) / 10.0
        return base
