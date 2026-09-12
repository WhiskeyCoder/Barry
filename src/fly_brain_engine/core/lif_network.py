from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import sparse

from fly_brain_engine.connectome.generator import ConnectomeGraph, generate_connectome


@dataclass
class LIFParams:
    dt_ms: float = 0.1
    tau_ms: float = 20.0
    v_rest: float = -65.0
    v_reset: float = -70.0
    v_thresh: float = -50.0
    r_mem: float = 1.0
    refractory_ms: float = 2.0

    @classmethod
    def barry(cls) -> LIFParams:
        """FlyWire v783 LIF parameters (fly-brain / Shiu et al. reference)."""
        return cls(
            dt_ms=0.1,
            tau_ms=20.0,
            v_rest=-52.0,
            v_reset=-52.0,
            v_thresh=-45.0,
            r_mem=1.0,
            refractory_ms=2.2,
        )


@dataclass
class NetworkState:
    v: np.ndarray
    spikes: np.ndarray
    refractory: np.ndarray
    time_ms: float
    spike_history: list[tuple[int, float]] = field(default_factory=list)


class LIFNetwork:
    """Sparse LIF whole-brain-style engine."""

    def __init__(self, graph: ConnectomeGraph, params: LIFParams | None = None) -> None:
        self.graph = graph
        self.params = params or LIFParams()
        self.n = graph.n_neurons
        self._w = graph.weights.astype(np.float32)
        self._weight_scale = float(getattr(graph, "weight_scale", 1.0))
        self._source_id_to_index: dict[int, int] = {}
        if getattr(graph, "source_ids", None):
            self._source_id_to_index = {int(sid): i for i, sid in enumerate(graph.source_ids)}
        self._external = np.zeros(self.n, dtype=np.float32)
        self._stim_until: dict[int, float] = {}
        self._state = self._fresh_state()

    @classmethod
    def from_scale(cls, scale: str = "medium", seed: int = 42, dt_ms: float = 0.1) -> LIFNetwork:
        g = generate_connectome(scale=scale, seed=seed)
        return cls(g, LIFParams(dt_ms=dt_ms))

    def _fresh_state(self) -> NetworkState:
        v = np.full(self.n, self.params.v_rest, dtype=np.float32)
        return NetworkState(
            v=v,
            spikes=np.zeros(self.n, dtype=np.bool_),
            refractory=np.zeros(self.n, dtype=np.float32),
            time_ms=0.0,
        )

    def reset(self, seed: int | None = None) -> None:
        if seed is not None:
            self.graph = generate_connectome(
                custom_n=self.n,
                seed=seed,
            )
            self._w = self.graph.weights.astype(np.float32)
        self._external.fill(0)
        self._stim_until.clear()
        self._state = self._fresh_state()

    def set_external_current(self, neuron_ids: np.ndarray | list[int], amps: np.ndarray | list[float]) -> None:
        for i, a in zip(neuron_ids, amps, strict=False):
            if 0 <= i < self.n:
                self._external[i] = float(a)

    def stimulate_rate(self, neuron_ids: list[int], hz: float, duration_ms: float | None = None) -> None:
        """Convert firing rate set-point to sustained current injection."""
        current = hz * 0.05
        until = self._state.time_ms + (duration_ms or 1e9)
        for nid in neuron_ids:
            if 0 <= nid < self.n:
                self._external[nid] = current
                self._stim_until[nid] = until

    def inhibit(self, neuron_ids: list[int], duration_ms: float = 100.0) -> None:
        until = self._state.time_ms + duration_ms
        for nid in neuron_ids:
            if 0 <= nid < self.n:
                self._external[nid] = -0.5
                self._stim_until[nid] = until

    def step(self, duration_ms: float) -> NetworkState:
        p = self.params
        steps = max(1, int(round(duration_ms / p.dt_ms)))
        s = self._state
        for _ in range(steps):
            s.refractory = np.maximum(0, s.refractory - p.dt_ms)
            # synaptic input from previous spikes
            syn_in = self._w.dot(s.spikes.astype(np.float32)) * self._weight_scale
            dv = (
                (-(s.v - p.v_rest) + p.r_mem * (syn_in + self._external)) * (p.dt_ms / p.tau_ms)
            )
            s.v = s.v + dv
            can_spike = s.refractory <= 0
            s.spikes = (s.v >= p.v_thresh) & can_spike
            s.v[s.spikes] = p.v_reset
            s.refractory[s.spikes] = p.refractory_ms
            s.time_ms += p.dt_ms
            fired = np.flatnonzero(s.spikes)
            for nid in fired[:500]:
                s.spike_history.append((int(nid), s.time_ms))
            if len(s.spike_history) > 100_000:
                s.spike_history = s.spike_history[-50_000:]
            # clear expired stim
            expired = [k for k, t in self._stim_until.items() if s.time_ms > t]
            for k in expired:
                self._external[k] = 0.0
                del self._stim_until[k]
        self._state = s
        return s

    def population_ids(self, name: str) -> list[int]:
        return list(self.graph.population_index.get(name, []))

    def index_for_body_id(self, body_id: int) -> int | None:
        return self._source_id_to_index.get(int(body_id))

    def read_rates(self, neuron_ids: list[int]) -> dict[int, float]:
        out: dict[int, float] = {}
        for i in neuron_ids:
            if 0 <= i < self.n:
                out[i] = float(max(0, (self._state.v[i] - self.params.v_rest) * 2.0))
        return out

    def mean_population_rate(self, population: str) -> float:
        ids = self.population_ids(population)
        if not ids:
            return 0.0
        r = self.read_rates(ids)
        return sum(r.values()) / len(r)

    def get_state_blob(self) -> dict[str, Any]:
        return {
            "v": self._state.v.tolist(),
            "time_ms": self._state.time_ms,
            "external": self._external.tolist(),
            "refractory": self._state.refractory.tolist(),
            "seed": self.graph.seed,
            "n": self.n,
            "provenance": getattr(self.graph, "provenance", "procedural"),
            "source": getattr(self.graph, "source", None),
        }

    def restore_state_blob(self, blob: dict[str, Any]) -> None:
        self._state.v = np.array(blob["v"], dtype=np.float32)
        self._state.time_ms = float(blob["time_ms"])
        self._external = np.array(blob["external"], dtype=np.float32)
        self._state.refractory = np.array(blob["refractory"], dtype=np.float32)
