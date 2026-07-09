# hydro-tools

Shared Python utilities extracted from the hundreds of one-off hydraulic modeling scripts.

## Quick start

```bash
# From this directory
pip install -e .

# PyPI (when published)
pip install hydro-tools

# Or just use the module directly
python -m hydro_tools.cli dbf-dump path/to/some.dbf -n 3
```

## Publish to PyPI

```bash
cd hydro-tools
pip install build twine
python -m build
twine upload dist/*   # requires PyPI token
```


### 0.1 Open Engine — Polished Status & Consumption (Phase 3 visibility)



`hydro-tools` + `stormsewer` v0.1.0 (Rust cdylib + WASM) + `hc-refactored/src/calc` (JS) = the mirrored, auditable foundation of standard public-domain methods (Rational Method, SCS runoff, Manning hydraulics, network accumulation).

**0.1 status (post publish polish):**
- Methods: Rational peak flow (C i A, composites, freq factors, network), SCS runoff depth + triangular hydrograph, Manning-based hydraulics (normal/critical depth, capacity, velocity for conduits). **0.2 spike (this cycle)**: concrete `manning_full_flow_circular` primitive added (full circular pipe capacity) — mirrored + exposed.
- Mirrored across 3 languages for verifiability, education, and embedding.
- Consumption is now documented at the root level with professional release notes.

**Exact beginner commands (repo root):**
```bash
# Python / hydro-tools (scripting, CLI, CAD, tests)
pip install -e hydro-tools
python -m hydro_tools.cli rational --c 0.7 --i 4.0 --a 5.0
python -c "
from hydro_tools.rational import rational_peak, scs_runoff_depth, manning_full_flow_circular
print(rational_peak(0.7, 4.0, 5.0))  # → 14.0 cfs
print(manning_full_flow_circular(2.0, 0.013, 0.005))  # 0.2: ~15.996 cfs (D=2ft, n=0.013, S=0.005)
"
# CLI also: python -m hydro_tools.cli manning --d 2.0 --n 0.013 --s 0.005
```


```bash
# Python/hydro-tools CLI (enhanced subcmds)
python -m hydro_tools.cli hgl-loss --q 17.656 --n 0.013 --a 3.0 --r 0.62132 --l 100
python -m hydro_tools.cli egl-step --q 17.656 --n 0.013 --a 3.0 --r 0.62132 --l 100 --vhup 0 --vhdown 0
# ~0.500 ft EGL
python -m hydro_tools.cli critical-depth --q 10 --d 2
# ~1.131 ft
python -m hydro_tools.cli normal-depth --d 2 --n 0.013 --s 0.005 --q 8.0
# ~1.000 ft
python -m hydro_tools.cli velocity --n 0.013 --r 0.62132 --s 0.005
python -m hydro_tools.cli network-hgl-profile
# Also python -c "
from hydro_tools.rational import manning_normal_flow_trapezoidal, manning_friction_head_loss, critical_depth_circular, normal_depth_circular, energy_grade_line_step, manning_full_flow_circular
print('trap 17.656:', manning_normal_flow_trapezoidal(2.0,1.0,1.0,0.013,0.005))
print('hglStep0_2 ~0.500:', manning_friction_head_loss(17.656,0.013,3,0.62132,100))
print('crit ~1.131:', critical_depth_circular(10,2))
print('normal ~1.000:', normal_depth_circular(2.0,0.013,0.005,8.0))
print('EGL ~0.500:', energy_grade_line_step(17.656,0.013,3.0,0.62132,100.0))
print('full 15.996:', manning_full_flow_circular(2.0,0.013,0.005))
"  # GREEN match across mirrors + CLI
```


