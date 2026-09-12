# Getting started with fly-brain-engine

Barry is a **MaleCNS v1.0** fruit-fly CNS simulation exposed as a **REST API**. You run experiments from Python (or any HTTP client) without importing the connectome into your code.

## Requirements

- Python **3.10+**
- **16 GB RAM** recommended for full MaleCNS graph load
- Windows, macOS, or Linux

## Path A — Demo (GitHub try-out, no data)

```powershell
cd fly-brain-engine
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e ".[dev]"

fly-brain-engine --demo --port 8090
```

`--demo` uses a **procedural mini** graph so CI and first-time users work immediately. Biology experiments should use Path B.

```powershell
pip install httpx
python examples/hello_barry.py
python examples/five_senses_and_sixth.py
python examples/multiverse_10_universes.py
```

Or set `FBE_DEMO=1` instead of `--demo`.

## Path B — Real MaleCNS (166,700 neurons)

```powershell
pip install -e ".[barry,dev]"
python scripts/setup_malecns_data.py --run-stonkfly-prepare
```

This builds a Stonkfly-compatible `graph.npz` under `connectome-data/malecns_v1/`. Alternative:

```powershell
python scripts/setup_malecns_data.py --from-stonkfly-data C:\path\to\stonkfly\data
```

Run the server:

```powershell
$env:FBE_CONNECTOME_DATA = "$PWD\connectome-data"
fly-brain-engine --port 8090
```

Verify:

```powershell
curl http://127.0.0.1:8090/health
curl http://127.0.0.1:8090/v1/connectome/profiles
```

Create Barry:

```http
POST /v1/brains
Content-Type: application/json

{ "name": "Barry" }
```

First brain creation may take several minutes while the CSR cache is built (`.cache/` under your data dir).

## Path C — FlyWire v783 (female brain-only)

```powershell
python scripts/setup_flywire_data.py --fly-brain-repo C:\path\to\fly-brain
# installs into connectome-data/flywire/
```

```http
POST /v1/brains
{ "name": "Barry", "connectome": "flywire_v783" }
```

## Docker

```powershell
docker compose up --build
```

Server listens on **8090** in demo mode by default in `docker-compose.yml`.

## Configuration

| Variable | Meaning |
|----------|---------|
| `FBE_CONNECTOME_DATA` | Root folder for connectome bundles |
| `FBE_DEMO=1` | Procedural default connectome |
| `FBE_PORT` | HTTP port (default 8090) |

Edit `config/default.yaml` for persistent settings.

## Building experiments

1. Start the engine (demo or MaleCNS).
2. Use `client/experiment_client.py` or `/docs` OpenAPI.
3. Log runs in your own repo (see parent `FlyBrain/experiments/` for dataset layout).

**Inject channels:**

- `vision.left`, `olfaction.food`, … — see [docs/SENSES.md](docs/SENSES.md)
- `synthetic.compass.x` — sixth sense (auto-registered)
- `population:DNp09_escape`
- `bodyId:1234567890` — MaleCNS root ID

**Multiverse (10 Barry, one tweak each):**

```http
POST /v1/experiments/multiverse
{
  "name": "study_01",
  "count": 10,
  "connectome": "procedural",
  "seed": 42,
  "variants": [
    { "label": "control", "initial_inject": {} },
    { "label": "compass_east", "initial_inject": { "synthetic.compass.x": 1.0 } }
  ]
}
```

```http
POST /v1/experiments/multiverse/{ensemble_id}/step?milliseconds=20
```

## Tests

```powershell
pytest
```

## Share on GitHub

This folder is **self-contained**: `LICENSE`, `README`, docs, examples, CI under `.github/workflows/`. Do **not** commit `connectome-data/`, `.venv/`, or `.cache/` (see `.gitignore`).

Cite MaleCNS / FlyWire when you publish results using real wiring.

## Next steps (your lab)

1. Platform smoke on MaleCNS — parent repo `experiments/00_platform_smoke/`
2. Five senses + sixth sense calibration
3. Multiverse / quantum-tagged ensembles at scale
4. COMPASS navigation experiment
