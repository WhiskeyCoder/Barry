from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class BrainRegion(str, Enum):
    optic_lobe_l = "optic_lobe_left"
    optic_lobe_r = "optic_lobe_right"
    antennal_lobe = "antennal_lobe"
    central_brain = "central_brain"
    subesophageal = "subesophageal_zone"
    vnc = "ventral_nerve_cord"
    descending = "descending_neurons"
    motor = "motor_neurons"
    synthetic = "synthetic_experimental"


@dataclass(frozen=True)
class PopulationSpec:
    name: str
    region: BrainRegion
    count: int
    role: str
    biological: bool = True


# Fraction of total neurons per region (Fly-like layout, synthetic wiring)
REGION_FRACTIONS: list[tuple[BrainRegion, float]] = [
    (BrainRegion.optic_lobe_l, 0.18),
    (BrainRegion.optic_lobe_r, 0.18),
    (BrainRegion.antennal_lobe, 0.08),
    (BrainRegion.central_brain, 0.22),
    (BrainRegion.subesophageal, 0.06),
    (BrainRegion.vnc, 0.20),
    (BrainRegion.descending, 0.04),
    (BrainRegion.motor, 0.03),
    (BrainRegion.synthetic, 0.01),
]

NAMED_POPULATIONS: list[PopulationSpec] = [
    PopulationSpec("photoreceptor_R1_R6_left", BrainRegion.optic_lobe_l, 0, "vision"),
    PopulationSpec("photoreceptor_R1_R6_right", BrainRegion.optic_lobe_r, 0, "vision"),
    PopulationSpec("LMC_layer", BrainRegion.optic_lobe_l, 0, "vision_interneuron"),
    PopulationSpec("lobula_plate_motion", BrainRegion.optic_lobe_l, 0, "motion"),
    PopulationSpec("ORN_glomeruli", BrainRegion.antennal_lobe, 0, "olfaction"),
    PopulationSpec("PN_projection", BrainRegion.antennal_lobe, 0, "olfaction"),
    PopulationSpec("KC_mushroom_body", BrainRegion.central_brain, 0, "learning"),
    PopulationSpec("DNp09_escape", BrainRegion.descending, 0, "escape"),
    PopulationSpec("DNa02_steering", BrainRegion.descending, 0, "steering"),
    PopulationSpec("MDN_walk", BrainRegion.motor, 0, "locomotion"),
    PopulationSpec("GF_giant_fiber", BrainRegion.descending, 0, "escape_fast"),
    PopulationSpec("johnstons_organ", BrainRegion.antennal_lobe, 0, "mechanosound"),
    PopulationSpec("proprio_leg", BrainRegion.vnc, 0, "proprioception"),
    PopulationSpec("synthetic_mag", BrainRegion.synthetic, 0, "magnetoreception", biological=False),
    PopulationSpec("synthetic_quantum", BrainRegion.synthetic, 0, "quantum_channel", biological=False),
]


SCALE_NEURON_COUNTS: dict[str, int] = {
    "mini": 2_048,
    "medium": 16_384,
    "large": 65_536,
    "flywire_target": 138_639,
}


@dataclass
class NeuronMetadata:
    id: int
    region: BrainRegion
    populations: list[str] = field(default_factory=list)
    cell_type: str = "unknown"
    neurotransmitter: str = "glutamate"
    is_sensory: bool = False
    is_motor: bool = False
