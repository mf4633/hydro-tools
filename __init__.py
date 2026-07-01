"""
hydro-tools: Shared utilities for hydraulic modeling Python scripts.

Extracted from the 300+ one-off scripts in the root.
Goal: reduce duplication, add CLI, make things testable and reusable.

This is part of the open core (with stormsewer WASM + shared JS calc in hc-refactored)
for **knowledge sharing** (verifiable methods anyone can audit/use),
**improving lives** (better flood/dam/stormwater decisions via FieldHydro + HydroComplete),
and **sustainable profit** (pro tiers on top of the free engine).

Current modules:
- paths: safe handling of project paths, OneDrive, network shares
- dbf: pure Python .dbf reader matching common struct patterns
- rational: Rational Method + scs_runoff_depth (ported from root analyze_*/add_* patterns)
- cli: dbf-dump, rational, stormsewer bridge, etc.

More ports coming. Bridge to Rust stormsewer (WASM target) for full networks in web/CAD/pro tools.

See root APP_FACTORY_CONSOLIDATION_PLAN.md and strategy vision for how this fits the bigger picture.
"""

__version__ = "0.2.0"


from .rational import rational_peak, batch_rational, scs_runoff_depth, manning_full_flow_circular, manning_normal_flow_trapezoidal, simple_linear_reservoir_routing, manning_friction_head_loss, critical_depth_circular, energy_grade_line_step, normal_depth_circular, normal_depth_trapezoidal, steady_network_hgl_profile  # type: ignore
from . import paths, dbf, cli  # type: ignore

# 0.2 methods (Manning full flow circular) added to open engine per STRATEGY/Phase 3.
# Re-exported for pip consumers: from hydro_tools.rational import ... or from hydro_tools import manning_full_flow_circular

# 0.2 additional: manning_normal_flow_trapezoidal (trapezoidal channel normal flow; complements circular; for network hydraulics / Priya interest).
# Exact style of prior Manning spike; fully open/free/tier-agnostic. Cross-verif numeric identical.


from .rational import normal_depth_trapezoidal, steady_network_hgl_profile, manning_velocity, discharge_to_velocity  # type: ignore


