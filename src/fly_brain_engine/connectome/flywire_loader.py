from __future__ import annotations

import csv
import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import sparse

from fly_brain_engine.connectome.generator import ConnectomeGraph
from fly_brain_engine.connectome.populations import BrainRegion, NeuronMetadata
from fly_brain_engine.connectome.profiles import ConnectomeDataError

FLYWIRE_WEIGHT_SCALE = 0.275
FLYWIRE_VERSION = "flywire_v783"


@dataclass(frozen=True)
class FlywireDataLayout:
    data_dir: Path
    manifest_path: Path
    connectivity_path: Path
    completeness_path: Path | None
    annotations_path: Path | None


def resolve_flywire_layout(data_dir: Path) -> FlywireDataLayout:
    data_dir = data_dir.expanduser().resolve()
    manifest_path = data_dir / "manifest.json"
    if manifest_path.is_file():
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        conn_name = raw.get("connectivity", "2025_Connectivity_783.parquet")
        comp_name = raw.get("completeness")
        ann_name = raw.get("annotations")
        connectivity_path = data_dir / conn_name
        completeness_path = data_dir / comp_name if comp_name else None
        annotations_path = data_dir / ann_name if ann_name else None
        if not completeness_path or not completeness_path.is_file():
            for candidate in (
                "2025_Completeness_783.csv",
                "completeness.csv",
                "neurons.csv",
            ):
                p = data_dir / candidate
                if p.is_file():
                    completeness_path = p
                    break
        if not annotations_path or not annotations_path.is_file():
            for candidate in ("flywire_annotations.tsv", "annotations.tsv"):
                p = data_dir / candidate
                if p.is_file():
                    annotations_path = p
                    break
    else:
        connectivity_path = data_dir / "2025_Connectivity_783.parquet"
        completeness_path = data_dir / "2025_Completeness_783.csv"
        annotations_path = data_dir / "flywire_annotations.tsv"
        if not annotations_path.is_file():
            annotations_path = None
        if not completeness_path.is_file():
            completeness_path = None

    return FlywireDataLayout(
        data_dir=data_dir,
        manifest_path=manifest_path,
        connectivity_path=connectivity_path,
        completeness_path=completeness_path if completeness_path and completeness_path.is_file() else None,
        annotations_path=annotations_path if annotations_path and annotations_path.is_file() else None,
    )


def flywire_data_status(data_dir: Path) -> dict:
    try:
        layout = resolve_flywire_layout(data_dir)
    except OSError as e:
        return {"ready": False, "error": str(e)}
    ready = layout.connectivity_path.is_file()
    out = {
        "profile": FLYWIRE_VERSION,
        "ready": ready,
        "version": FLYWIRE_VERSION,
        "data_dir": str(layout.data_dir),
        "connectivity": str(layout.connectivity_path),
        "connectivity_exists": ready,
        "completeness": str(layout.completeness_path) if layout.completeness_path else None,
        "annotations": str(layout.annotations_path) if layout.annotations_path else None,
    }
    if not ready:
        out["setup"] = "Run scripts/setup_flywire_data.py (see docs/CONNECTOMES.md)."
    return out


def _cache_path(layout: FlywireDataLayout) -> Path:
    cache_dir = layout.data_dir / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    stem = layout.connectivity_path.name.replace(".", "_")
    return cache_dir / f"{stem}_csr.pkl"


def _load_edges_parquet(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    import pyarrow.parquet as pq

    table = pq.read_table(
        path,
        columns=["Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"],
    )
    pre = table.column("Presynaptic_Index").to_numpy(zero_copy_only=False)
    post = table.column("Postsynaptic_Index").to_numpy(zero_copy_only=False)
    w = table.column("Excitatory x Connectivity").to_numpy(zero_copy_only=False)
    n = int(max(pre.max(), post.max())) + 1
    return pre.astype(np.int64), post.astype(np.int64), w.astype(np.float32), n


def _load_edges_csv(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    pre_list: list[int] = []
    post_list: list[int] = []
    w_list: list[float] = []
    max_id = 0
    with path.open(encoding="utf-8") as f:
        reader = csv.reader(f)
        for line in reader:
            if not line or line[0].startswith("#"):
                continue
            if line[0].lower() in ("pre", "pre_id", "presynaptic_index"):
                continue
            pre, post, w = int(line[0]), int(line[1]), float(line[2])
            max_id = max(max_id, pre, post)
            pre_list.append(pre)
            post_list.append(post)
            w_list.append(w)
    pre = np.array(pre_list, dtype=np.int64)
    post = np.array(post_list, dtype=np.int64)
    w = np.array(w_list, dtype=np.float32)
    return pre, post, w, max_id + 1


def _build_csr(pre: np.ndarray, post: np.ndarray, w: np.ndarray, n: int) -> sparse.csr_matrix:
    return sparse.coo_matrix((w, (post, pre)), shape=(n, n)).tocsr()


def _load_completeness_n(path: Path | None, fallback_n: int) -> int:
    if path is None or not path.is_file():
        return fallback_n
    count = 0
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if i == 0 and line.split(",")[0].lower() in ("root_id", "root", "id"):
                continue
            count += 1
    return max(fallback_n, count)


def _load_root_to_index(path: Path) -> dict[int, int]:
    mapping: dict[int, int] = {}
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            first = line.split(",")[0].strip()
            if i == 0 and first.lower() in ("root_id", "root", "id"):
                continue
            root = int(float(first))
            mapping[root] = len(mapping)
    return mapping


def _metadata_and_populations(
    n: int,
    layout: FlywireDataLayout,
) -> tuple[list[NeuronMetadata], dict[str, list[int]]]:
    meta: list[NeuronMetadata] = [
        NeuronMetadata(id=i, region=BrainRegion.central_brain, populations=[], cell_type="flywire")
        for i in range(n)
    ]
    pop_index: dict[str, list[int]] = {}
    if layout.annotations_path and layout.annotations_path.is_file():
        root_to_idx = (
            _load_root_to_index(layout.completeness_path)
            if layout.completeness_path
            else {i: i for i in range(n)}
        )
        _apply_annotations_tsv(layout.annotations_path, meta, pop_index, root_to_idx)
    return meta, pop_index


def _apply_annotations_tsv(
    path: Path,
    meta: list[NeuronMetadata],
    pop_index: dict[str, list[int]],
    root_to_idx: dict[int, int],
) -> None:
    rules: list[tuple[str, str, BrainRegion]] = [
        ("photoreceptor", "photoreceptor_R1_R6_left", BrainRegion.optic_lobe_l),
        ("R1-6", "photoreceptor_R1_R6_left", BrainRegion.optic_lobe_l),
        ("ORN", "ORN_glomeruli", BrainRegion.antennal_lobe),
        ("DNp09", "DNp09_escape", BrainRegion.descending),
        ("DNa02", "DNa02_steering", BrainRegion.descending),
        ("MDN", "MDN_walk", BrainRegion.motor),
        ("giant fiber", "GF_giant_fiber", BrainRegion.descending),
        ("GF", "GF_giant_fiber", BrainRegion.descending),
    ]
    with path.open(encoding="utf-8") as f:
        header = f.readline().strip().split("\t")
        try:
            id_col = header.index("root_id") if "root_id" in header else 0
            type_col = header.index("type") if "type" in header else 1
        except ValueError:
            id_col, type_col = 0, 1
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) <= max(id_col, type_col):
                continue
            try:
                root = int(float(parts[id_col]))
            except ValueError:
                continue
            idx = root_to_idx.get(root)
            if idx is None or idx < 0 or idx >= len(meta):
                continue
            type_str = parts[type_col].lower()
            for needle, pop_name, region in rules:
                if needle.lower() in type_str:
                    if pop_name not in meta[idx].populations:
                        meta[idx].populations.append(pop_name)
                    pop_index.setdefault(pop_name, []).append(idx)
                    meta[idx].region = region
                    break


def load_flywire_connectome(data_dir: Path, *, use_cache: bool = True) -> ConnectomeGraph:
    layout = resolve_flywire_layout(data_dir)
    if not layout.connectivity_path.is_file():
        raise ConnectomeDataError(
            f"FlyWire connectivity not found at {layout.connectivity_path}. "
            "Run scripts/setup_flywire_data.py."
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
            provenance="flywire",
            source=FLYWIRE_VERSION,
            weight_scale=FLYWIRE_WEIGHT_SCALE,
        )

    suffix = layout.connectivity_path.suffix.lower()
    if suffix == ".parquet":
        pre, post, w, n_edges = _load_edges_parquet(layout.connectivity_path)
    elif suffix == ".csv":
        pre, post, w, n_edges = _load_edges_csv(layout.connectivity_path)
    else:
        raise ConnectomeDataError(f"Unsupported connectivity format: {layout.connectivity_path}")

    n = _load_completeness_n(layout.completeness_path, n_edges)
    weights = _build_csr(pre, post, w, n)
    metadata, population_index = _metadata_and_populations(n, layout)
    graph = ConnectomeGraph(
        n_neurons=n,
        weights=weights,
        metadata=metadata,
        population_index=population_index,
        seed=0,
        provenance="flywire",
        source=FLYWIRE_VERSION,
        weight_scale=FLYWIRE_WEIGHT_SCALE,
    )
    if use_cache:
        with cache.open("wb") as f:
            pickle.dump(
                {
                    "n": n,
                    "weights": weights,
                    "metadata": metadata,
                    "population_index": population_index,
                },
                f,
                protocol=pickle.HIGHEST_PROTOCOL,
            )
    return graph
