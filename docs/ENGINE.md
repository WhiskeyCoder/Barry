# Engine internals

## LIF dynamics

Sparse CSR synaptic matrix `W[post, pre]`. Each step:

1. Synaptic input from previous binary spike vector
2. Leaky integration of membrane voltage
3. Threshold → spike → refractory period

Default `dt_ms = 0.1` (configurable).

## Connectome

- **Generated**: region-fraction layout inspired by optic lobe / AL / CB / VNC with named populations.
- **Loaded**: CSV `pre,post,weight` via API.

Replace generated wiring with FlyWire/MaleCNS edge lists when you have them on disk — the engine does not download Janelia datasets automatically.

## Brains

Each `FlyBrain` owns one `LIFNetwork`, `SensorRegistry`, `MotorRegistry`. Clone duplicates graph + state blob.

## Plasticity

`plasticity/stdp.py` tracks baseline vs delta weights; enable for long-run learning experiments (experimental, not biophysical STDP at full scale).
