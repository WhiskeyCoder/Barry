from pathlib import Path

import pytest

from fly_brain_engine.connectome.flywire_loader import flywire_data_status, load_flywire_connectome
from fly_brain_engine.connectome.malecns_loader import load_malecns_connectome, malecns_data_status
from fly_brain_engine.connectome.profiles import ConnectomeProfile, load_real_connectome
from fly_brain_engine.brains.brain_engine import FlyBrain
from fly_brain_engine.config import Settings

FLYWIRE_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "barry_tiny"
MALECNS_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "malecns_tiny"


def test_malecns_data_status_missing(tmp_path: Path) -> None:
    st = malecns_data_status(tmp_path / "nope")
    assert st["ready"] is False


def test_load_malecns_tiny_fixture() -> None:
    g = load_malecns_connectome(MALECNS_FIXTURE, use_cache=False)
    assert g.provenance == "malecns"
    assert g.n_neurons == 4
    assert g.source_ids is not None
    assert len(g.source_ids) == 4


def test_load_flywire_tiny_fixture() -> None:
    g = load_flywire_connectome(FLYWIRE_FIXTURE, use_cache=False)
    assert g.provenance == "flywire"
    assert g.n_neurons == 4


def test_create_brain_malecns_mode() -> None:
    settings = Settings(connectome_data_dir=MALECNS_FIXTURE, default_connectome="malecns_v1")
    brain = FlyBrain.create("Barry", connectome="malecns_v1", settings=settings)
    assert brain.metadata["connectome"] == "malecns_v1"
    assert brain.network.n == 4
    assert brain.network.index_for_body_id(101) == 1


def test_profile_normalize_barry_alias() -> None:
    assert ConnectomeProfile.normalize("barry") == ConnectomeProfile.MALECNS_V1
