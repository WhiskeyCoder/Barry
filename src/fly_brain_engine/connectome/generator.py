from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse

from fly_brain_engine.connectome.populations import (
    REGION_FRACTIONS,
    BrainRegion,
    NeuronMetadata,
    NAMED_POPULATIONS,
    SCALE_NEURON_COUNTS,
)


@dataclass
class ConnectomeGraph:
    n_neurons: int
    weights: sparse.csr_matrix
    metadata: list[NeuronMetadata]
    population_index: dict[str, list[int]]
    seed: int
    provenance: str = "procedural"
    source: str | None = None
    weight_scale: float = 1.0
    source_ids: list[int] | None = None


def _assign_regions(n: int, rng: np.random.Generator) -> list[BrainRegion]:
    regions: list[BrainRegion] = []
    cursor = 0
    for region, frac in REGION_FRACTIONS:
        count = int(round(n * frac))
        regions.extend([region] * count)
    while len(regions) < n:
        regions.append(BrainRegion.central_brain)
    regions = regions[:n]
    rng.shuffle(regions)
    return regions


def _tag_populations(n: int, regions: list[BrainRegion], rng: np.random.Generator) -> tuple[list[NeuronMetadata], dict[str, list[int]]]:
    meta: list[NeuronMetadata] = []
    pop_index: dict[str, list[int]] = {p.name: [] for p in NAMED_POPULATIONS}

    region_to_pops: dict[BrainRegion, list[str]] = {}
    for spec in NAMED_POPULATIONS:
        region_to_pops.setdefault(spec.region, []).append(spec.name)

    for i in range(n):
        reg = regions[i]
        pops: list[str] = []
        choices = region_to_pops.get(reg, [])
        if choices and rng.random() < 0.15:
            pname = rng.choice(choices)
            pops.append(pname)
            pop_index[pname].append(i)
        ct = f"{reg.value}_t{i % 23}"
        nt = "GABA" if rng.random() < 0.2 else "glutamate"
        is_sensory = reg in (BrainRegion.optic_lobe_l, BrainRegion.optic_lobe_r, BrainRegion.antennal_lobe)
        is_motor = reg == BrainRegion.motor
        meta.append(
            NeuronMetadata(
                id=i,
                region=reg,
                populations=pops,
                cell_type=ct,
                neurotransmitter=nt,
                is_sensory=is_sensory,
                is_motor=is_motor,
            )
        )

    # Ensure key demo populations have neurons
    _ensure_min_pop(pop_index, meta, "photoreceptor_R1_R6_left", BrainRegion.optic_lobe_l, min_count=max(6, n // 2000))
    _ensure_min_pop(pop_index, meta, "photoreceptor_R1_R6_right", BrainRegion.optic_lobe_r, min_count=max(6, n // 2000))
    _ensure_min_pop(pop_index, meta, "ORN_glomeruli", BrainRegion.antennal_lobe, min_count=max(4, n // 3000))
    _ensure_min_pop(pop_index, meta, "DNa02_steering", BrainRegion.descending, min_count=max(3, n // 5000))
    _ensure_min_pop(pop_index, meta, "DNp09_escape", BrainRegion.descending, min_count=max(3, n // 5000))
    _ensure_min_pop(pop_index, meta, "MDN_walk", BrainRegion.motor, min_count=max(3, n // 5000))
    _ensure_min_pop(pop_index, meta, "synthetic_mag", BrainRegion.synthetic, min_count=max(3, n // 8000), biological=False)
    _ensure_min_pop(pop_index, meta, "synthetic_quantum", BrainRegion.synthetic, min_count=max(3, n // 8000), biological=False)

    return meta, pop_index


def _ensure_min_pop(
    pop_index: dict[str, list[int]],
    meta: list[NeuronMetadata],
    name: str,
    region: BrainRegion,
    min_count: int,
    biological: bool = True,
) -> None:
    while len(pop_index[name]) < min_count:
        for i, m in enumerate(meta):
            if m.region == region and name not in m.populations:
                m.populations.append(name)
                pop_index[name].append(i)
                break
        else:
            break


def _build_sparse_weights(n: int, rng: np.random.Generator, density: float) -> sparse.csr_matrix:
    # Target ~ density * n^2 synapses — use fixed avg degree instead for scale
    avg_degree = max(20, int(density * n))
    if n > 50_000:
        avg_degree = min(avg_degree, 40)
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for post in range(n):
        pres = rng.integers(0, n, size=avg_degree)
        for pre in pres:
            if pre == post:
                continue
            w = float(rng.normal(0, 0.05))
            if abs(w) < 0.01:
                w = 0.02 if rng.random() > 0.5 else -0.02
            rows.append(post)
            cols.append(int(pre))
            data.append(w)
    coo = sparse.coo_matrix((data, (rows, cols)), shape=(n, n))
    return coo.tocsr()


def generate_connectome(scale: str = "medium", seed: int = 42, custom_n: int | None = None) -> ConnectomeGraph:
    n = custom_n or SCALE_NEURON_COUNTS.get(scale, SCALE_NEURON_COUNTS["medium"])
    rng = np.random.default_rng(seed)
    regions = _assign_regions(n, rng)
    metadata, population_index = _tag_populations(n, regions, rng)
    density = 0.002 if n < 10_000 else 0.0005 if n < 100_000 else 0.0002
    weights = _build_sparse_weights(n, rng, density)
    return ConnectomeGraph(
        n_neurons=n,
        weights=weights,
        metadata=metadata,
        population_index=population_index,
        seed=seed,
    )


def load_edges_csv(path: str, n_neurons: int | None = None) -> ConnectomeGraph:
    """Load pre,post,weight CSV; optional header."""
    import csv
    from pathlib import Path

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    max_id = 0
    with Path(path).open(encoding="utf-8") as f:
        reader = csv.reader(f)
        for line in reader:
            if not line or line[0].startswith("#"):
                continue
            if line[0].lower() in ("pre", "pre_id"):
                continue
            pre, post, w = int(line[0]), int(line[1]), float(line[2])
            max_id = max(max_id, pre, post)
            rows.append(post)
            cols.append(pre)
            data.append(w)
    n = n_neurons or (max_id + 1)
    weights = sparse.coo_matrix((data, (rows, cols)), shape=(n, n)).tocsr()
    rng = np.random.default_rng(0)
    regions = _assign_regions(n, rng)
    metadata, population_index = _tag_populations(n, regions, rng)
    return ConnectomeGraph(n, weights, metadata, population_index, seed=0)
