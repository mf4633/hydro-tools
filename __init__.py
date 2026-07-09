"""hydro-tools: open, auditable hydrology and open-channel hydraulics primitives.

Public-domain methods in plain, dependency-free Python (US customary units):
the Rational Method, SCS curve-number runoff, Manning capacity/velocity, circular
and trapezoidal depth solvers, HGL/EGL steps, simple reservoir routing, and a
small pure-Python ``.dbf`` reader.

Import the primitives directly, e.g. ``from hydro_tools import rational_peak``.
"""

__version__ = "0.2.0"

from .rational import (
    rational_peak,
    batch_rational,
    scs_runoff_depth,
    manning_full_flow_circular,
    manning_normal_flow_trapezoidal,
    manning_velocity,
    discharge_to_velocity,
    simple_linear_reservoir_routing,
    manning_friction_head_loss,
    energy_grade_line_step,
    critical_depth_circular,
    normal_depth_circular,
    normal_depth_trapezoidal,
    steady_network_hgl_profile,
)
from .dbf import read_dbf, dbf_to_list
from . import paths, dbf, cli, rational

__all__ = [
    "__version__",
    # rational method & runoff
    "rational_peak",
    "batch_rational",
    "scs_runoff_depth",
    # manning capacity & velocity
    "manning_full_flow_circular",
    "manning_normal_flow_trapezoidal",
    "manning_velocity",
    "discharge_to_velocity",
    # depth solvers
    "critical_depth_circular",
    "normal_depth_circular",
    "normal_depth_trapezoidal",
    # energy / hydraulic grade line & routing
    "manning_friction_head_loss",
    "energy_grade_line_step",
    "simple_linear_reservoir_routing",
    "steady_network_hgl_profile",
    # dbf reader
    "read_dbf",
    "dbf_to_list",
    # submodules
    "rational",
    "dbf",
    "paths",
    "cli",
]
