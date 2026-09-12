"""Load MaleCNS v1.0 retained graph (166,700 neurons; Stonkfly-compatible graph.npz)."""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import sparse

from fly_brain_engine.connectome.generator import ConnectomeGraph
from fly_brain_engine.connectome.populations import BrainRegion, NeuronMetadata
from fly_brain_engine.connectome.profiles import ConnectomeDataError

MALECNS_VERSION = "malecns_v1"
MALECNS_NEURONS = 166_700
# Signed synaptic weights in compiled graph use this scale (Stonkfly / fly-brain convention).
WEIGHT_SCALE = 0.275


@dataclass(frozen=True)
class MaleCNSLayout:
    data_dir: Path
    graph_path: Path
    manifest_path: Path | None
    neurons_feather: Path | None
    annotations_feather: Path | None


def resolve_layout(data_dir: Path) -> MaleCNSLayout:
    data_dir = data_dir.expanduser().resolve()
    manifest_path = data_dir / "manifest.json"
    graph_path = data_dir / "graph.npz"
    neurons_feather = None
    annotations_feather = None

    if manifest_path.is_file():
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        if g := raw.get("graph"):
            graph_path = data_dir / g
        if n := raw.get("neurons"):
            neurons_feather = data_dir / n
        if a := raw.get("annotations"):
            annotations_feather = data_dir / a

    for candidate in ("normalized/neurons.feather", "neurons.feather"):
        p = data_dir / candidate
        if neurons_feather is None and p.is_file():
            neurons_feather = p
    for candidate in ("annotations.feather",):
        p = data_dir / candidate
        if annotations_feather is None and p.is_file():
            annotations_feather = p
    if not graph_path.is_file():
        alt = data_dir / "malecns_v1" / "graph.npz"
        if alt.is_file():
            graph_path = alt

    return MaleCNSLayout(
        data_dir=data_dir,
        graph_path=graph_path,
        manifest_path=manifest_path if manifest_path.is_file() else None,
        neurons_feather=neurons_feather,
        annotations_feather=annotations_feather,
    )


def malecns_data_status(data_dir: Path) -> dict:
    layout = resolve_layout(data_dir)
    ready = layout.graph_path.is_file()
    out: dict = {
        "profile": MALECNS_VERSION,
        "ready": ready,
        "data_dir": str(layout.data_dir),
        "graph": str(layout.graph_path),
        "graph_exists": ready,
        "expected_neurons": MALECNS_NEURONS,
        "neurons_metadata": str(layout.neurons_feather) if layout.neurons_feather else None,
    }
    if not ready:
        out["setup"] = (
            "Install MaleCNS v1 graph: python scripts/setup_malecns_data.py "
            "(uses Stonkfly prepare) or copy data/graph.npz from a Stonkfly install into "
            "connectome-data/. Set FBE_CONNECTOME_DATA."
        )
    return out


def _cache_path(layout: MaleCNSLayout) -> Path:
    cache = layout.data_dir / ".cache"
    cache.mkdir(parents=True, exist_ok=True)
    return cache / "malecns_v1_csr.pkl"


def _csr_from_stonkfly_npz(path: Path) -> tuple[sparse.csr_matrix, np.ndarray, dict]:
    with np.load(path, allow_pickle=False) as archive:
        required = {"ptr", "post", "weight", "ids"}
        missing = required - set(archive.files)
        if missing:
            raise ConnectomeDataError(f"{path} missing arrays: {sorted(missing)}")
        ptr = archive["ptr"].astype(np.int64)
        post_idx = archive["post"].astype(np.int64)
        weight = archive["weight"].astype(np.float32)
        ids = archive["ids"].astype(np.int64)
        extras = {k: archive[k] for k in archive.files if k not in required}

    n = int(len(ptr) - 1)
    if len(ids) != n:
        raise ConnectomeDataError(f"graph.npz ids length {len(ids)} != n {n}")

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for pre in range(n):
        for k in range(int(ptr[pre]), int(ptr[pre + 1])):
            rows.append(int(post_idx[k]))
            cols.append(pre)
            data.append(float(weight[k]))
    w = sparse.coo_matrix((data, (rows, cols)), shape=(n, n)).tocsr()
    return w, ids, extras


def _population_rules() -> list[tuple[str, str, BrainRegion]]:
    return [
        ("R1-6", "photoreceptor_R1_R6_left", BrainRegion.optic_lobe_l),
        ("photoreceptor", "photoreceptor_R1_R6_left", BrainRegion.optic_lobe_l),
        ("ORN", "ORN_glomeruli", BrainRegion.antennal_lobe),
        ("KC", "KC_mushroom_body", BrainRegion.central_brain),
        ("MBON", "KC_mushroom_body", BrainRegion.central_brain),
        ("PAM11", "KC_mushroom_body", BrainRegion.central_brain),
        ("PPL101", "KC_mushroom_body", BrainRegion.central_brain),
        ("DNp09", "DNp09_escape", BrainRegion.descending),
        ("DNa02", "DNa02_steering", BrainRegion.descending),
        ("DNp20", "DNa02_steering", BrainRegion.descending),
        ("DNpe017", "DNp09_escape", BrainRegion.descending),
        ("MDN", "MDN_walk", BrainRegion.motor),
        ("giant fiber", "GF_giant_fiber", BrainRegion.descending),
    ]


def _metadata_from_feather(
    path: Path,
    n: int,
    source_ids: np.ndarray,
) -> tuple[list[NeuronMetadata], dict[str, list[int]]]:
    import pyarrow.feather as feather

    table = feather.read_table(path)
    df = table.to_pandas()
    if "source_id" in df.columns and len(df) == n:
        id_col = df["source_id"].to_numpy()
        if not np.array_equal(id_col.astype(np.int64), source_ids):
            raise ConnectomeDataError("neurons.feather order does not match graph.npz ids")
        cell_types = df.get("cell_type", df.get("type", [""] * n)).astype(str).tolist()
        superclasses = df.get("superclass", [""] * n).astype(str).tolist()
    else:
        cell_types = [""] * n
        superclasses = [""] * n

    meta: list[NeuronMetadata] = []
    pop_index: dict[str, list[int]] = {}
    rules = _population_rules()

    for i in range(n):
        ct = cell_types[i] if i < len(cell_types) else ""
        sc = superclasses[i] if i < len(superclasses) else ""
        region = BrainRegion.vnc if "motor" in sc.lower() else BrainRegion.central_brain
        pops: list[str] = []
        hay = f"{ct} {sc}".lower()
        for needle, pop_name, reg in rules:
            if needle.lower() in hay or needle.lower() in ct.lower():
                pops.append(pop_name)
                pop_index.setdefault(pop_name, []).append(i)
                region = reg
        meta.append(
            NeuronMetadata(
                id=i,
                region=region,
                populations=list(dict.fromkeys(pops)),
                cell_type=ct or "unknown",
                neurotransmitter="",
                is_sensory="R1" in ct or "ORN" in ct,
                is_motor="MDN" in ct or "MN" in ct,
            )
        )
    return meta, pop_index


def _default_metadata(n: int, extras: dict) -> tuple[list[NeuronMetadata], dict[str, list[int]]]:
    meta = [
        NeuronMetadata(id=i, region=BrainRegion.central_brain, populations=[], cell_type="malecns")
        for i in range(n)
    ]
    pop_index: dict[str, list[int]] = {}
    if "superclass" in extras:
        sc = extras["superclass"]
        for i in range(min(n, len(sc))):
            meta[i].cell_type = str(sc[i])
    return meta, pop_index


def load_malecns_connectome(data_dir: Path, *, use_cache: bool = True) -> ConnectomeGraph:
    layout = resolve_layout(data_dir)
    if not layout.graph_path.is_file():
        raise ConnectomeDataError(
            f"MaleCNS graph not found at {layout.graph_path}. "
            "Run scripts/setup_malecns_data.py (see docs/CONNECTOMES.md)."
        )

    cache = _cache_path(layout)
    if use_cache and cache.is_file():
        with cache.open("rb") as f:
            cached = pickle.load(f)
        return ConnectomeGraph(
            n_neurons=cached["n"],
            weights=cached["weights"],
            metadata=cached["metadata"],
            population_index=cached["population_index"],
            seed=0,
            provenance="malecns",
            source=MALECNS_VERSION,
            weight_scale=1.0,
            source_ids=cached.get("source_ids"),
        )

    weights, source_ids, extras = _csr_from_stonkfly_npz(layout.graph_path)
    n = weights.shape[0]

    if layout.neurons_feather and layout.neurons_feather.is_file():
        metadata, population_index = _metadata_from_feather(layout.neurons_feather, n, source_ids)
    else:
        metadata, population_index = _default_metadata(n, extras)

    graph = ConnectomeGraph(
        n_neurons=n,
        weights=weights,
        metadata=metadata,
        population_index=population_index,
        seed=0,
        provenance="malecns",
        source=MALECNS_VERSION,
        weight_scale=1.0,
        source_ids=source_ids.tolist(),
    )

    if use_cache:
        with cache.open("wb") as f:
            pickle.dump(
                {
                    "n": n,
                    "weights": weights,
                    "metadata": metadata,
                    "population_index": population_index,
                    "source_ids": source_ids.tolist(),
                },
                f,
                protocol=pickle.HIGHEST_PROTOCOL,
            )
    return graph
