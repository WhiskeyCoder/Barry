from __future__ import annotations

from threading import RLock
from uuid import UUID

from fly_brain_engine.brains.brain_engine import FlyBrain
from fly_brain_engine.config import Settings


class BrainRegistry:
    def __init__(self, settings: Settings | None = None) -> None:
        self._items: dict[UUID, FlyBrain] = {}
        self._lock = RLock()
        self.settings = settings or Settings.load()

    def create(
        self,
        name: str,
        connectome: str | None = None,
        scale: str = "medium",
        seed: int = 42,
    ) -> FlyBrain:
        with self._lock:
            b = FlyBrain.create(
                name=name,
                connectome=connectome or self.settings.default_connectome,
                scale=scale,
                seed=seed,
                dt_ms=self.settings.dt_ms,
                settings=self.settings,
            )
            self._items[b.id] = b
            return b

    def register(self, brain: FlyBrain) -> None:
        with self._lock:
            self._items[brain.id] = brain

    def get(self, brain_id: UUID) -> FlyBrain:
        with self._lock:
            if brain_id not in self._items:
                raise KeyError(str(brain_id))
            return self._items[brain_id]

    def list(self) -> list[FlyBrain]:
        with self._lock:
            return list(self._items.values())

    def delete(self, brain_id: UUID) -> None:
        with self._lock:
            self._items.pop(brain_id, None)
