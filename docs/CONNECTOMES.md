# Connectome profiles (what “Barry” can be)

**Barry** is the name for a **real** *Drosophila* connectome in the engine — not procedural wiring. Which atlas you load depends on the experiment. The HTTP API stays the same; you pick a **profile** via data + `connectome` mode.

## Two maps people actually use

| Profile | Scope | Scale (order of magnitude) | Typical experiments |
|---------|--------|------------------------------|---------------------|
| **`malecns_v1`** | Male **brain + VNC** (full CNS) | ~**166,700** neurons; ~**11,700** types; **~125M** synaptic contacts in the published map (graphs often use **~25M** retained connections after processing) | Synthetic senses, weird I/O, dopamine reward, KC→MBON plasticity, “make the fly do X” — e.g. [Stonkfly](https://github.com/nftechie/stonkfly) (BTC chart → photoreceptors → trade readout) |
| **`flywire_v783`** | Female **brain** (FlyWire FAFB) | ~**138,639** neurons; ~**15M** directed weighted synapses | Whole-brain LIF, embodied sims — e.g. [fly-brain](https://github.com/erojasoficial-byte/fly-brain) + FlyWire |

They are **not interchangeable**: sex, coverage (VNC vs brain-only), and annotation IDs differ. COMPASS, looming escape, and locomotion that needs the VNC should target **MaleCNS**. FlyWire-first is fine for vision-heavy brain circuits and alignment with the embodied FlyWire literature.

### Why Stonkfly’s numbers differ from “125 million”

- **125M** (Janelia / MaleCNS messaging) ≈ **synaptic contacts** in the full map (brain + nerve cord).
- **25.6M connections** in [Stonkfly’s README](https://github.com/nftechie/stonkfly) = their **retained simulation graph** (aggregated edges they run), not the raw contact count.
- Our [BACKEND_RESEARCH.md](../../docs/BACKEND_RESEARCH.md) neuPrint-style **~6.24M** = another aggregation (neuron–neuron summaries). Same biology, different on-disk shapes.

Always record **`connectome_profile` + dataset hash** in experiment `config.json`.

## Engine status (this repo)

| Profile | Loader in `fly-brain-engine` | Data setup |
|---------|------------------------------|------------|
| `malecns_v1` | **Yes** — Stonkfly-compatible `graph.npz` (166,700 neurons) | `scripts/setup_malecns_data.py` |
| `flywire_v783` | **Yes** — fly-brain parquet | `scripts/setup_flywire_data.py` |
| `procedural` | Dev/CI only | No download |

**Default server connectome:** `malecns_v1` (`FBE_CONNECTOME_DATA=./connectome-data`).

## What Stonkfly does (pattern we want)

From [stonkfly](https://github.com/nftechie/stonkfly):

1. **Real retained MaleCNS graph** (166,700 neurons).
2. **Engineered sensory injection** — chart pixels → thousands of brightness + R8 inputs (not “evolution gave it candlesticks”).
3. **Fixed or learned readout** — neural activity → buy/sell/hold.
4. **Reward engineering** — P&L → PAM11 / PPL101 dopamine cells; plasticity on **KC→MBON** (candidate memory rule).

That is exactly the architecture FlyBrain is for: **stable API**, honest provenance (`synthetic` vs `biological` mappings), consolidated experiment datasets under `experiments/runs/`.

## API (unchanged goal)

```http
POST /v1/brains
{ "name": "Barry", "connectome": "malecns_v1" }
```

Today use `"flywire_v783"` or `"barry"` (alias) when FlyWire data is installed. When MaleCNS lands, switch default in `config/default.yaml` without breaking clients.

## Citations

- MaleCNS: Janelia FlyEM / project download pages + your dataset version.
- FlyWire v783: [FlyWire](https://flywire.ai/), Dorkenwald et al. 2024, Zenodo/Codex downloads.
