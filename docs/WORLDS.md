# World dimensions

| Dim | Class | Meaning |
|-----|--------|---------|
| 2 | `World2D` | Arena: light, food, hazard, walls; differential vision |
| 3 | `World3D` | Volume navigation, obstacles, odor source |
| 4 | `World4D` | 3D + **world-time** coordinate; timeline branches (`POST .../timeline/branch`) |
| 5 | `World5D` | 4D base + **multi-brain ensemble**; entangled sensor mixing (`.../quantum/entangle`) |

5D “quantum” is a **research metaphor**: phase-coupled sensor superposition across brains, synchronized stepping — not a quantum physics simulator.

## Closed-loop sessions

`POST /v1/experiments/sessions` binds brain + world. Each `.../step`:

1. World generates sensor payloads
2. Brain receives stimulation + steps
3. Motor outputs move the agent (2D/3D)

## From your Python file

Use `client/experiment_client.py`:

```python
ec.inject(brain_id, "vision.left", 0.8, step_ms=10)
```

Channels:

- `vision.left`, `olfaction.food`, …
- `population:MDN_walk` — direct population rate
- `neuron:42` — direct neuron index
