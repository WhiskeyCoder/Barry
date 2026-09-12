# Fly Brain Engine — Barry

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Barry** is a shareable HTTP engine for the *Drosophila* nervous system: **MaleCNS v1.0** (166,700 neurons, brain + VNC), sparse LIF dynamics, and an experiment API for anything you can encode as inject/step/readout — navigation, trading, puzzles, sixth senses, multiverse ensembles.

![image](https://raw.githubusercontent.com/WhiskeyCoder/Barry/refs/heads/main/images/2026.png)


## Try it in 2 minutes (no connectome download)

```powershell
git clone https://github.com/WhiskeyCoder/Barry
cd fly-brain-engine
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
fly-brain-engine --demo --port 8090
```

Second terminal:

```powershell
pip install httpx
python examples/hello_barry.py
python examples/multiverse_10_universes.py
```

Open **http://127.0.0.1:8090/docs**

## Real MaleCNS Barry (production)

```powershell
pip install -e ".[barry,dev]"
python scripts/setup_malecns_data.py --run-stonkfly-prepare
$env:FBE_CONNECTOME_DATA = "$PWD\connectome-data"
fly-brain-engine --port 8090
```

```http
POST /v1/brains
{ "name": "Barry" }
```

See **[GETTING_STARTED.md](GETTING_STARTED.md)** for Docker, FlyWire alt atlas, and experiment layout.

## What you can build

| Feature | API |
|---------|-----|
| Any sensor / sixth sense | `POST /v1/experiments/inject` |
| Named MaleCNS cells | `channel: "bodyId:…"` |
| 10 parallel universes | `POST /v1/experiments/multiverse` |
| Closed-loop 2D world | `POST /v1/experiments/sessions` |
| Clone / snapshot | `POST /v1/brains/{id}/clone` |

## Docs

| Doc | Topic |
|-----|--------|
| [GETTING_STARTED.md](GETTING_STARTED.md) | Install, demo, real data, Docker |
| [EXPERIMENT_ENGINE.md](docs/EXPERIMENT_ENGINE.md) | World → inject → step pattern |
| [CONNECTOMES.md](docs/CONNECTOMES.md) | MaleCNS vs FlyWire |
| [docs/SENSES.md](docs/SENSES.md) | Five senses + synthetic |

## Examples

| Script | Description |
|--------|-------------|
| `examples/hello_barry.py` | Health + one inject |
| `examples/five_senses_and_sixth.py` | 5 + synthetic compass |
| `examples/multiverse_10_universes.py` | 10 clones, different 6th sense |
| `examples/experiment_2d_light.py` | Closed-loop arena |

## Client

```python
from experiment_client import EngineClient  # add client/ to PYTHONPATH

ec = EngineClient("http://127.0.0.1:8090")
bid = ec.create_brain("Barry", connectome="procedural", scale="mini")
ec.inject(bid, "synthetic.compass.x", 0.5)
```

## IMPORTANT NOTE:
```txt
Barry simulates neural activity using connectome-derived connectivity and simplified neuronal dynamics. It is not a complete biological simulation of a living fruit fly, and no claim is made that the system is conscious, sentient, or experiences subjective states. Synthetic sensory mappings and experimental additions are explicitly distinguished from biologically established circuits.... so no ... THEY HAVE NOT IMPRISONED A FLY'S SOUL IN PYTHON
```

## License

MIT — see [LICENSE](LICENSE). Connectome **data** is cited separately (Janelia MaleCNS, FlyWire, Stonkfly bundles).
