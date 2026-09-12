"""Deprecated: use flywire_loader."""

from fly_brain_engine.connectome.flywire_loader import (  # noqa: F401
    flywire_data_status as barry_data_status,
    load_flywire_connectome as load_barry_connectome,
)
from fly_brain_engine.connectome.profiles import ConnectomeDataError as BarryDataError
