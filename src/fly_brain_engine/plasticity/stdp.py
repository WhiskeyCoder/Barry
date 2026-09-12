from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse


@dataclass
class PlasticityState:
    enabled: bool = False
    baseline: sparse.csr_matrix | None = None
    delta: sparse.csr_matrix | None = None


class STDPModule:
    """Optional experimental plasticity — tracks delta from baseline weights."""

    def __init__(self, weights: sparse.csr_matrix) -> None:
        self.state = PlasticityState(
            enabled=False,
            baseline=weights.copy(),
            delta=sparse.csr_matrix(weights.shape),
        )

    def enable(self, on: bool = True) -> None:
        self.state.enabled = on

    def on_spikes(self, pre: np.ndarray, post: np.ndarray, lr: float = 1e-5) -> None:
        if not self.state.enabled or self.state.delta is None:
            return
        # lightweight global mod — full pair STDP is O(n²)
        scale = 1.0 + lr * (float(post.sum()) - float(pre.sum()))
        if abs(scale - 1.0) > 1e-9 and self.state.baseline is not None:
            self.state.delta = self.state.baseline * (scale - 1.0)
