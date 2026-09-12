from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass
class WorldEntity:
    entity_id: str
    kind: str
    position: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorldSnapshot:
    world_id: UUID
    dimension: int
    time_coordinate: float
    entities: list[WorldEntity]
    fields: dict[str, Any] = field(default_factory=dict)


class World(ABC):
    dimension: int = 0

    def __init__(self, name: str) -> None:
        self.id = uuid4()
        self.name = name
        self.entities: dict[str, WorldEntity] = {}

    @abstractmethod
    def step(self, dt: float) -> WorldSnapshot: ...

    @abstractmethod
    def sensor_payloads(self, agent_position: list[float]) -> dict[str, Any]: ...

    def add_entity(self, entity: WorldEntity) -> None:
        self.entities[entity.entity_id] = entity
