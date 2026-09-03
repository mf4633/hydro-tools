# hydro-tools

Open, auditable Python primitives for stormwater and open-channel hydraulics —
the Rational Method, SCS curve-number runoff, Manning capacity and depth
solvers, HGL/EGL steps, and simple reservoir routing — plus a small pure-Python
`.dbf` reader. US customary units (feet, cfs, in/hr) throughout.

Every method is a plain, dependency-free function you can read, test, and cite
against public-domain references (Chow, *Open-Channel Hydraulics*; FHWA HEC-22;
NRCS NEH).

## Install

```bash
pip install hydro-tools            # from PyPI (once published)
pip install -e ".[dev]"            # from a checkout, with test deps
```

Requires Python 3.9+. No runtime dependencies.

## Quick start

```python
from hydro_tools import (
    rational_peak, scs_runoff_depth,
    manning_full_flow_circular, critical_depth_circular, normal_depth_circular,
)

rational_peak(0.7, 4.0, 5.0)            # Q = C·i·A -> 14.0 cfs
scs_runoff_depth(3.0, 75)               # SCS runoff depth -> 0.961 in
manning_full_flow_circular(2.0, 0.013, 0.005)   # full-flow capacity -> 15.996 cfs
critical_depth_circular(10.0, 2.0)      # critical depth -> 1.131 ft
normal_depth_circular(2.0, 0.013, 0.005, 8.0)   # normal depth -> 1.000 ft
```

Or from the command line:

```bash
hydro-tools rational --c 0.7 --i 4.0 --a 5.0
hydro-tools manning --d 2.0 --n 0.013 --s 0.005
hydro-tools critical-depth --q 10 --d 2
hydro-tools dbf-dump path/to/some.dbf -n 3
```

(`python -m hydro_tools.cli ...` works identically if the console script isn't
on your `PATH`.)

## API reference

All discharges are in cfs, lengths/depths in feet, slopes in ft/ft, Manning's
`n` dimensionless, intensity in in/hr, area in acres (Rational) or ft² (velocity).

### Rational Method & runoff
| Function | Returns |
| --- | --- |
| `rational_peak(c, intensity_in_per_hr, area_acres)` | peak discharge Q = C·i·A (cfs) |
| `batch_rational(areas: dict[str, float], c, i)` | `{name: Q}` for several sub-areas |
| `scs_runoff_depth(rainfall_in, cn)` | SCS runoff depth (in); `cn` in (0, 100] |

### Manning capacity & velocity
| Function | Returns |
| --- | --- |
| `manning_full_flow_circular(diameter_ft, n, slope)` | full-flow capacity of a circular pipe (cfs) |
| `manning_normal_flow_trapezoidal(bottom_width_ft, side_slope_z, flow_depth_ft, n, slope)` | discharge of a trapezoidal (or rectangular, `z=0`) channel at a given depth (cfs) |
| `manning_velocity(n, hyd_radius_ft, slope)` | mean velocity V = (1.486/n)·R^(2/3)·S^(1/2) (ft/s) |
| `discharge_to_velocity(q_cfs, area_ft2)` | V = Q/A (ft/s) |

### Depth solvers
| Function | Returns |
| --- | --- |
| `critical_depth_circular(q_cfs, diameter_ft)` | critical depth (ft), from Q²/g = A³/T |
| `normal_depth_circular(diameter_ft, n, slope, q_cfs)` | normal depth (ft); raises `ValueError` if Q exceeds the pipe's capacity |
| `normal_depth_trapezoidal(bottom_width_ft, side_slope_z, n, slope, q_cfs)` | normal depth (ft) |

### Energy / hydraulic grade line & routing
| Function | Returns |
| --- | --- |
| `manning_friction_head_loss(q_cfs, n, area_ft2, hyd_radius_ft, length_ft)` | friction head loss hf = S_f·L (ft) |
| `energy_grade_line_step(q_cfs, n, area_ft2, hyd_radius_ft, length_ft, vel_head_up_ft=0, vel_head_down_ft=0)` | friction loss plus the change in velocity head (ft); equals hf for uniform flow |
| `simple_linear_reservoir_routing(inflow_cfs, prev_outflow_cfs, k_hr, dt_hr)` | routed outflow for one timestep (cfs) |
| `steady_network_hgl_profile(reaches, start_hgl_ft=10.0)` | list of per-reach `{reach_idx, cum_length_ft, hgl_ft, egl_ft, hf_ft, delta_egl_ft}` |

### .dbf reader
| Function | Returns |
| --- | --- |
| `read_dbf(path)` | iterator of records as dicts (streams, skips deleted rows, coerces numeric fields) |
| `dbf_to_list(path)` | all records as a list of dicts |

## CLI

`hydro-tools <command> [options]`. Calculation commands:

| Command (aliases) | Example |
| --- | --- |
| `rational` | `hydro-tools rational --c 0.7 --i 4 --a 5` |
| `scs` | `hydro-tools scs --rain 3 --cn 75` |
| `manning` | `hydro-tools manning --d 2 --n 0.013 --s 0.005` |
| `manning-trap` (`trapezoidal`) | `hydro-tools manning-trap --b 2 --z 1 --y 1 --n 0.013 --s 0.005` |
| `critical-depth` (`yc-circular`) | `hydro-tools critical-depth --q 10 --d 2` |
| `normal-depth` (`normal-depth-circular`) | `hydro-tools normal-depth --d 2 --n 0.013 --s 0.005 --q 8` |
| `normal-depth-trap` | `hydro-tools normal-depth-trap --b 2 --z 1 --n 0.013 --s 0.005 --q 17.656` |
| `hgl-loss` (`hgl-step`, `friction-head-loss`) | `hydro-tools hgl-loss --q 17.656 --n 0.013 --a 3 --r 0.62132 --l 100` |
| `egl-step` (`energy-grade-line`) | `hydro-tools egl-step --q 17.656 --n 0.013 --a 3 --r 0.62132 --l 100` |
| `routing` (`linear-reservoir`) | `hydro-tools routing --i 10 --qp 0 --k 1 --dt 1` |
| `velocity` (`manning-velocity`) | `hydro-tools velocity --n 0.013 --r 0.62132 --s 0.005` |
| `network-hgl-profile` | `hydro-tools network-hgl-profile` |
| `dbf-dump` | `hydro-tools dbf-dump some.dbf -n 3` |

Run `hydro-tools --help` for the full list.

## Development

```bash
pip install -e ".[dev]"
python -m pytest tests
```

CI runs the test suite on Python 3.9–3.12 and smoke-tests the built wheel on
every push and pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) for the
build/release workflow.

## License

MIT — see [LICENSE](LICENSE).

## See also

Browser versions of these primitives, with worked notes: [Rational method](https://pe-calc.com/tools/rational-method.html), [SCS curve number runoff](https://pe-calc.com/tools/scs-runoff.html), and [Manning's equation](https://pe-calc.com/tools/mannings.html) on pe-calc.com.
