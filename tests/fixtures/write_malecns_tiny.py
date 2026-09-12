import numpy as np
from pathlib import Path

n = 4
ptr = np.array([0, 1, 2, 3, 4], dtype=np.int64)
post = np.array([1, 2, 3, 0], dtype=np.int32)
weight = np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float32)
ids = np.array([100, 101, 102, 103], dtype=np.int64)
p = Path(__file__).resolve().parent / "malecns_tiny"
p.mkdir(parents=True, exist_ok=True)
np.savez(p / "graph.npz", ptr=ptr, post=post, weight=weight, ids=ids)
(p / "manifest.json").write_text('{"version":"malecns_v1","graph":"graph.npz"}\n', encoding="utf-8")
