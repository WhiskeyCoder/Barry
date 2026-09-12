# FlyBrain Engine — experiment platform

**Barry** is the full **MaleCNS v1.0** connectome (166,700 neurons, brain + VNC) exposed as an HTTP API. Your experiment owns everything else: crypto charts, Rubik’s cube state, compass vectors, reward dopamine — via **`POST /v1/experiments/inject`**.

Pattern (same idea as [Stonkfly](https://github.com/nftechie/stonkfly)):

```text
Your world  →  encode  →  inject (sensors / bodyId / populations)
                              ↓
                         MaleCNS LIF step
                              ↓
                         read activity / motors / custom decode
                              ↓
                         act in world + log dataset
```

## Install the brain

```powershell
pip install -e ".[barry,dev]"
python scripts/setup_malecns_data.py --run-stonkfly-prepare
# or: --from-stonkfly-data C:\path\to\stonkfly\data

$env:FBE_CONNECTOME_DATA = "$PWD\connectome-data"
fly-brain-engine --port 8090
```

## Create Barry

```http
POST /v1/brains
{ "name": "Barry" }
```

Default connectome is **`malecns_v1`**. Aliases: `"barry"`, `"malecns"`.

## Inject anything

| Channel | Example |
|---------|---------|
| Synthetic sensor | `{ "channel": "synthetic.compass.x", "data": 0.72 }` |
| Population | `{ "channel": "population:ORN_glomeruli", "data": 50 }` |
| Tensor index | `{ "channel": "neuron:42", "data": 80 }` |
| **MaleCNS body ID** | `{ "channel": "bodyId:1234567890", "data": 100 }` |

Use **`bodyId:`** for named cells from literature (PAM11, DNp20, …) once you map type → IDs from annotations.

## Profiles

| Profile | Use |
|---------|-----|
| `malecns_v1` | Default — weird experiments, VNC, Stonkfly-compatible `graph.npz` |
| `flywire_v783` | Female brain-only — `connectome-data/flywire/` |
| `procedural` | CI / plumbing only |

See [CONNECTOMES.md](CONNECTOMES.md), [BARRY.md](BARRY.md).

Repo experiments: [`../experiments/`](../experiments/).
