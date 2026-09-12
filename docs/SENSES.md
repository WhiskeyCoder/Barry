# Default biological sensor IDs (procedural + mapped populations on MaleCNS)

| Sensor ID | Modality | Population target |
|-----------|----------|---------------------|
| `vision.left` | Vision | photoreceptor_R1_R6_left |
| `vision.right` | Vision | photoreceptor_R1_R6_right |
| `olfaction.food` | Smell | ORN_glomeruli |
| `gustation.sugar` | Taste | ORN_glomeruli |
| `proprio.legs` | Proprioception | proprio_leg |
| `auditory.johnston` | Hearing (Johnston's organ) | johnstons_organ |

## Sixth sense and beyond

Any `synthetic.*` channel can be injected without pre-registration; the engine attaches it to `synthetic_mag` (or specify via `POST /v1/brains/{id}/sensors`).

Examples:

- `synthetic.compass.x` / `synthetic.compass.y` — COMPASS experiment
- `synthetic.quantum.phase` — your experiment-defined encoding (not physics simulation in-engine)

Record provenance: biological vs synthetic in experiment `config.json`.

## Direct stimulation

| Channel prefix | Example |
|----------------|---------|
| `population:` | `population:DNp09_escape` |
| `neuron:` | `neuron:42` |
| `bodyId:` | `bodyId:1234567890` (MaleCNS root id) |
