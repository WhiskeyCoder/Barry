# Barry — the fruit fly

**Barry** is not a random graph with fly-themed labels. He is a **real connectome** loaded from published wiring data — today **FlyWire v783**, with **MaleCNS v1.0** as the planned default for brain+VNC experiments (see [CONNECTOMES.md](CONNECTOMES.md)).

## Which atlas?

| You want… | Profile |
|-----------|---------|
| Brain + VNC, synthetic senses, Stonkfly-style hacks | **`malecns_v1`** (~166,700 neurons) — loader coming |
| Female whole brain, fly-brain / FlyWire sims | **`flywire_v783`** (~138,639 neurons) — **implemented** |
| Fast API plumbing only | **`procedural`** — not Barry |

Read the full comparison (125M contacts vs 25M graph edges, Stonkfly, etc.): **[CONNECTOMES.md](CONNECTOMES.md)**.

## FlyWire v783 (implemented)

| Property | Value |
|----------|--------|
| Neurons | 138,639 |
| Synapses | ~15.1M directed, weighted |
| Source | [FlyWire](https://flywire.ai/) / Dorkenwald et al. 2024 |
| Dynamics | Sparse LIF (Shiu et al., aligned with [fly-brain](https://github.com/erojasoficial-byte/fly-brain)) |

### Install data

Connectivity is **not** in git (hundreds of MB). One-time setup:

```powershell
cd fly-brain-engine
pip install -e ".[barry,dev]"
python scripts/setup_barry_data.py --fly-brain-repo C:\path\to\fly-brain
$env:FBE_BARRY_DATA = "$PWD\barry-data"
fly-brain-engine --port 8090
```

Check: `GET /v1/connectome/status`, `GET /v1/capabilities`.

### Create a brain

```http
POST /v1/brains
{ "name": "Barry", "connectome": "barry" }
```

(`barry` is an alias for `flywire_v783` until MaleCNS is the server default.)

Without data installed → **503** with setup text, not a silent stunt double.

## Procedural mode (dev only)

```json
{ "name": "stunt", "connectome": "procedural", "scale": "mini" }
```

## Honest limits (v0.1)

| Layer | Status |
|-------|--------|
| FlyWire topology + weights | Real (parquet) |
| MaleCNS full graph | Not loaded yet — priority for shared “experiment platform” |
| LIF on CPU | Simplified vs alpha/GPU fly-brain |
| Pathway-accurate I/O | Partial; needs type→neuron maps per atlas |
| Trading / crypto / sixth sense | **Your experiment layer** — engine provides inject + step + logs |

Roadmap: **MaleCNS v1 loader**, named-cell stimulation like Stonkfly’s PAM11/PPL101, plasticity hooks, optional Torch backend.

## Cite the connectome

Cite the dataset you actually loaded (MaleCNS or FlyWire) in papers and in each run’s `config.json`.
