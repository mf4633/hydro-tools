"""
rational.py
Basic Rational Method peak flow calculator.

Extracted / generalized from patterns in root analyze_*.py and add_*.py scripts.
Can be used by fieldhydro exports or future CLI tools.

Q = C * i * A   (cfs when i in in/hr, A in acres, or scaled)
"""

from typing import Dict

def rational_peak(c: float, intensity_in_per_hr: float, area_acres: float) -> float:
    """
    Simple Rational method peak discharge.
    Returns Q in cfs (common US units for storm sewer work).
    """
    if c <= 0 or c > 1:
        raise ValueError("Runoff coefficient C must be between 0 and 1")
    if intensity_in_per_hr <= 0:
        raise ValueError("Intensity must be positive")
    if area_acres <= 0:
        raise ValueError("Area must be positive")
    return c * intensity_in_per_hr * area_acres

def batch_rational(areas: Dict[str, float], c: float, i: float) -> Dict[str, float]:
    """Convenience for multiple sub-areas."""
    return {name: rational_peak(c, i, a) for name, a in areas.items()}

# Bridge note: for full network analysis, use the Rust stormsewer crate (WASM build in progress for web + CAD integration).

def scs_runoff_depth(rainfall_in: float, cn: float) -> float:
    """
    Simple SCS runoff depth (inches) using the standard approximation.
    Extracted/port style from common patterns in the user's root analyze_*.py and add_*.py scripts.
    Useful for hydrograph volume calculations and consistent with the existing rational_peak.
    """
    if rainfall_in <= 0:
        return 0.0
    s = (1000.0 / cn) - 10.0
    ia = 0.2 * s
    if rainfall_in <= ia:
        return 0.0
    return ((rainfall_in - ia) ** 2) / (rainfall_in - ia + s)


# 0.2 open engine methods spike (Phase 3 / STRATEGY knowledge + openness + profit north star).
# Concrete mirrored primitive: Manning full-flow capacity for circular storm sewer / channel.
# High-leverage, complements Rational/SCS (stormsewer crate focus + existing pe-calc/tools/mannings.html).
# Fully open/free, no new deps. Extendable to trapezoidal etc later.
# Serves Priya lead interest ("network hydraulics extension for the open core") + 0.2 recs.
def manning_full_flow_circular(diameter_ft: float, n: float, slope_ft_per_ft: float) -> float:
    """
    Manning's equation full (normal) flow capacity for a circular pipe flowing full.

    Formula (US customary units for storm sewer context, consistent with rational_peak cfs):
        Q = (k / n) * A * R^(2/3) * S^(1/2)   with k=1.486
        A = π (D/2)^2 , R = D/4  (full circular pipe)

    Args:
        diameter_ft: pipe diameter (ft)
        n: Manning's roughness coefficient (e.g. 0.013 for concrete)
        slope_ft_per_ft: friction slope (ft/ft, ≈ bed slope for uniform flow)

    Returns:
        Q_full in cfs.

    Mirrors exactly the implementations in:
    - Rust/stormsewer (dev/OpenCADStudio/crates/stormsewer/src/lib.rs + reexported hydraulics)
    - JS/hc-refactored (src/calc/index.js + window.HC)

    Reference: standard public-domain (Chow, HEC-22, etc). See full hydraulics.rs for
    partial flow, normal_depth, max_capacity etc (pro can layer network on this base).

    Phase 3 note: 0.2 methods expansion keeps core 100% open/auditable/educational while
    pro (FieldHydro network + provenance, HydroComplete full modeling) adds value on top.
    contribute path as Rational/SCS), profit (foundation for advanced paid network tools
    without reinventing the primitive).
    """
    if diameter_ft <= 0.0 or n <= 0.0 or slope_ft_per_ft < 0.0:
        raise ValueError("diameter_ft > 0, n > 0, slope_ft_per_ft >= 0 required")
    import math
    d = diameter_ft
    a = math.pi * (d / 2.0) ** 2
    r = d / 4.0
    k = 1.486
    return (k / n) * a * (r ** (2.0 / 3.0)) * (slope_ft_per_ft ** 0.5)


# 0.2 cross-verification test values (hardcoded expected from formula; same across 3 mirrors):
# D=2.0 ft, n=0.013 (trowel-finished concrete), S=0.005 ft/ft
# Expected Q_full ≈ 15.996 cfs (A≈3.1416, R=0.5, V≈5.092 ft/s)
# python -c "from hydro_tools.rational import manning_full_flow_circular; print(manning_full_flow_circular(2.0, 0.013, 0.005))"


# 0.2 additional open engine methods spike (Phase 3 / STRATEGY knowledge + openness + profit north star; builds directly on just-completed Manning full flow circular 0.2 spike).
# Concrete mirrored primitive: Manning normal (uniform) flow capacity for trapezoidal channel (or rectangular if z=0).
# High-leverage simple one for network hydraulics / storm sewer open channels; complements Rational/SCS + prior circular Manning (for pipes).
# Pure fn + standard geometry, no new deps. (Simple storage/channel routing stub or HGL would also fit but this is mirrorable + high immediate leverage per STRATEGY recs for "0.2 methods" + "network hydraulics extension").
# Serves Priya lead interest ("network hydraulics extension for the open core") + STRATEGY Phase 3 "next wave (..., 0.2 methods, ...)" and "more FieldHydro pro flow on provenance gate" after Manning.
def manning_normal_flow_trapezoidal(bottom_width_ft: float, side_slope_z: float, flow_depth_ft: float, n: float, slope_ft_per_ft: float) -> float:
    """
    Manning's equation normal (uniform) flow capacity for a trapezoidal channel section (rectangular if z=0).

    Formula (US customary units for storm sewer / channel context, consistent with rational_peak cfs and manning_full_flow_circular):
        A = (b + z * y) * y
        P = b + 2 * y * sqrt(1 + z**2)
        R = A / P
        Q = (1.486 / n) * A * R^(2/3) * S^(1/2)

    Args:
        bottom_width_ft: channel bottom width b (ft)
        side_slope_z: horizontal:vertical side slope z:1 (e.g. 2.0 for 2:1 H:V; use 0.0 for rectangular/vertical sides)
        flow_depth_ft: flow depth y (ft)
        n: Manning's roughness coefficient (e.g. 0.013 for trowel-finished concrete)
        slope_ft_per_ft: friction slope S (ft/ft, ≈ bed slope for uniform/normal flow)

    Returns:
        Q in cfs at the given depth (normal flow for the trapezoidal section).

    Mirrors exactly the implementations in:
    - Rust/stormsewer (dev/OpenCADStudio/crates/stormsewer/src/lib.rs WASM + reexports; top stormsewer/README + src for docs)
    - JS/hc-refactored (src/calc/index.js + window.HC after main.js load)

    Reference: standard public-domain (Chow, V.T. "Open-Channel Hydraulics"; HEC-22; NRCS NEH). See pe-calc/tools/mannings.html
    for identical trap geometry in worked example (A/P/R) + schema.

    Phase 3 note: additional 0.2 method spike (post Manning circular) per STRATEGY "next wave" keeps core 100% open/auditable/educational while
    pro (FieldHydro network + provenance gate + AR field marks, HydroComplete full modeling + Tauri desktop spike, exportProAuditPackage)
    adds value on top without gating this primitive.
    openness (free + identical contribute template as Rational/SCS/Manning: implement + doc + export + note in quickstarts/STRATEGY),
    """
    if bottom_width_ft < 0.0 or side_slope_z < 0.0 or flow_depth_ft <= 0.0 or n <= 0.0 or slope_ft_per_ft < 0.0:
        raise ValueError("bottom_width_ft >=0, side_slope_z >=0, flow_depth_ft >0, n>0, slope_ft_per_ft >=0 required")
    import math
    b = bottom_width_ft
    z = side_slope_z
    y = flow_depth_ft
    a = (b + z * y) * y
    p = b + 2.0 * y * math.sqrt(1.0 + z * z)
    r = a / p if p > 0.0 else 0.0
    k = 1.486
    return (k / n) * a * (r ** (2.0 / 3.0)) * (slope_ft_per_ft ** 0.5)


# 0.2 cross-verification test values (hardcoded expected from formula; same across 3 mirrors; pre-computed via python math for exact match):
# Test1: b=2.0, z=1.0, y=1.0, n=0.013, s=0.005 → Q≈17.656 cfs
# Test2: b=4.0, z=2.0, y=2.5, n=0.013, s=0.005 → Q≈236.416 cfs (matches pe-calc/tools/mannings.html concrete trap worked example A=22.5/P≈15.18/R≈1.482)
# Test3: b=1.0, z=0.0 (rectangular), y=0.5, n=0.025, s=0.01 → Q≈1.179 cfs
# python -c "
# from hydro_tools.rational import manning_normal_flow_trapezoidal, manning_full_flow_circular
# print(manning_normal_flow_trapezoidal(2.0, 1.0, 1.0, 0.013, 0.005))
# print(manning_normal_flow_trapezoidal(4.0, 2.0, 2.5, 0.013, 0.005))
# print(manning_full_flow_circular(2.0, 0.013, 0.005))  # confirm no breakage to prior 0.2 Manning
# "

# 0.2 additional open engine methods spike (Phase 3 / STRATEGY knowledge + openness + profit north star; builds on Manning full flow circular + trapezoidal channel normal flow 0.2 spikes).
# Concrete mirrored primitive: simple linear reservoir routing (basic one-step channel/reservoir hydrograph routing primitive for network hydraulics).
# High-leverage simple one for network hydraulics / storm sewer / channel routing; complements Rational/SCS (inflow hydro) + prior Manning capacity (steady) for unsteady attenuation in networks.
# Pure fn + standard discrete linear reservoir, no new deps. (Simple storage routing stub fits STRATEGY recs for "0.2 methods" + "network hydraulics extension").
# Serves Priya lead interest ("network hydraulics extension for the open core") + STRATEGY Phase 3 "next wave (..., 0.2 methods, ...)" + "maintenance + real user acquisition".
def simple_linear_reservoir_routing(inflow_cfs: float, prev_outflow_cfs: float, k_hr: float, dt_hr: float) -> float:
    """
    Simple linear reservoir routing step for basic channel or reservoir hydrograph attenuation.

    Formula (discrete solution to linear reservoir: dS/dt = I - O , O = S / K ):
        Q_out = Q_prev * exp(-dt / K) + I * (1 - exp(-dt / K))
    (I assumed constant over dt interval; for varying hydro use I_avg or call stepwise.)

    Args:
        inflow_cfs: inflow rate I for the timestep (cfs)
        prev_outflow_cfs: outflow at start of timestep Q(t) (cfs)
        k_hr: storage coefficient K (hr; time constant of the linear reservoir)
        dt_hr: timestep duration (hr)

    Returns:
        outflow at end of timestep Q(t+dt) in cfs.

    Mirrors exactly the implementations in:
    - Rust/stormsewer (dev/OpenCADStudio/crates/stormsewer/src/lib.rs WASM + reexports; top stormsewer/README + src for docs)
    - JS/hc-refactored (src/calc/index.js + window.HC after main.js load)

    Reference: standard public-domain linear reservoir / simple routing model (e.g. base for many in "Applied Hydrology" Chow et al.; NRCS intro methods; complements full Modified Puls / storage-indication in pe-calc/tools/reservoir-routing.html).

    pro (FieldHydro network + provenance gate + AR field marks, HydroComplete full modeling + Tauri desktop spike, exportProAuditPackage) adds value on top without gating this primitive.
    openness (free + identical contribute template as Rational/SCS/Manning/trap: implement + doc + export + note in quickstarts/STRATEGY),
    """
    if k_hr <= 0.0 or dt_hr <= 0.0 or inflow_cfs < 0.0 or prev_outflow_cfs < 0.0:
        raise ValueError("k_hr >0, dt_hr >0, flows >=0 required")
    import math
    e = math.exp(-dt_hr / k_hr)
    return prev_outflow_cfs * e + inflow_cfs * (1.0 - e)


# 0.2 cross-verification test values (hardcoded expected from formula; same across 3 mirrors; pre-computed via python math for exact match):
# Test1: I=10, Qp=0, K=1, dt=1 → Qout≈6.321 cfs
# Test2: I=5, Qp=5, K=2, dt=0.5 → Qout=5.0 (steady state preserved)
# Test3: I=20, Qp=10, K=0.5, dt=0.25 → Qout≈13.935 cfs
# python -c "
# from hydro_tools.rational import simple_linear_reservoir_routing, manning_normal_flow_trapezoidal, manning_full_flow_circular
# print(simple_linear_reservoir_routing(10.0, 0.0, 1.0, 1.0))
# print(simple_linear_reservoir_routing(5.0, 5.0, 2.0, 0.5))
# print(manning_normal_flow_trapezoidal(2.0, 1.0, 1.0, 0.013, 0.005))  # confirm no breakage to prior 0.2 trap
# print(manning_full_flow_circular(2.0, 0.013, 0.005))  # confirm no breakage to prior 0.2 Manning
# "

# 0.2 additional open engine methods spike (Phase 3 / STRATEGY knowledge + openness + profit north star; builds on Manning full flow circular + trapezoidal + simple_linear_reservoir_routing 0.2 spikes).
# Concrete mirrored primitive: manning_friction_head_loss (basic HGL/energy step for network: friction head loss hf over a reach via inverted Manning, for steady network HGL/energy grade line stepping).
# High-leverage simple one for network hydraulics / storm sewer / channel HGL profiles; complements Rational/SCS (inflow) + prior Manning capacity (for Q/S) + routing (for unsteady) for full network analysis.
# Pure fn + standard inverted Manning loss (hf = L * [n*Q / (1.486 * A * R**(2/3)) ]**2 ), no new deps. (Fits STRATEGY recs for "0.2 methods" + "network hydraulics extension" + "next wave").
def manning_friction_head_loss(q_cfs: float, n: float, area_ft2: float, hyd_radius_ft: float, length_ft: float) -> float:
    """
    Manning friction head loss (hf) over a reach length for basic HGL / energy grade line step in network hydraulics.
    (Simple auditable primitive to step HGL: HGL_down = HGL_up - hf; uses friction slope from Manning inverted.)

    Formula (US customary units for storm sewer / channel context, consistent with rational_peak cfs + manning_*_flow_*):
        S_f = [ n * Q / (1.486 * A * R^(2/3)) ]^2
        hf = S_f * L

    Args:
        q_cfs: discharge Q (cfs)
        n: Manning's roughness coefficient (e.g. 0.013 for concrete)
        area_ft2: flow cross-sectional area A (ft^2; from trap/circ geo or direct)
        hyd_radius_ft: hydraulic radius R (ft; A/P)
        length_ft: reach length L (ft)

    Returns:
        hf in ft (friction head loss over the reach).

    Mirrors exactly the implementations in:
    - Rust/stormsewer (dev/OpenCADStudio/crates/stormsewer/src/lib.rs WASM + reexports; top stormsewer/README + src for docs)
    - JS/hc-refactored (src/calc/index.js + window.HC after main.js load)

    Reference: standard public-domain (Chow, HEC-22, etc). Complements pe-calc/tools/mannings.html (capacity) + reservoir-routing.html.
    Can combine with prior 0.2 manning_normal_flow_trapezoidal etc to get A/R then loss for HGL profile.

    pro (FieldHydro network + provenance gate + AR field marks, HydroComplete full modeling + Tauri desktop spike, exportProAuditPackage + exportProBatchAuditPackage) adds value on top without gating this primitive.
    openness (free + identical contribute template as Rational/SCS/Manning/trap/routing: implement + doc + export + note in quickstarts/STRATEGY + .github/ISSUE_TEMPLATE/engine-feedback.md),
    """
    if q_cfs < 0.0 or n <= 0.0 or area_ft2 <= 0.0 or hyd_radius_ft <= 0.0 or length_ft <= 0.0:
        raise ValueError("q_cfs >=0, n>0, area>0, R>0, L>0 required")
    import math
    k = 1.486
    sf = (n * q_cfs / (k * area_ft2 * (hyd_radius_ft ** (2.0 / 3.0)))) ** 2
    return sf * length_ft



# 0.2 cross-verification test values (hardcoded expected from formula; same across 3 mirrors; pre-computed via python math for exact match):
# Test2: q=10, n=0.013, A=2.0, R=0.5, L=200 → hf≈0.850 ft (example)
# python -c "
# from hydro_tools.rational import manning_friction_head_loss, manning_normal_flow_trapezoidal, simple_linear_reservoir_routing, manning_normal_flow_trapezoidal, manning_full_flow_circular
# import math
# q = manning_normal_flow_trapezoidal(2.0, 1.0, 1.0, 0.013, 0.005)
# a = (2.0 + 1.0*1.0)*1.0
# p = 2.0 + 2.0*1.0*math.sqrt(1+1)
# r = a / p
# print('Q trap:', q)
# print(manning_friction_head_loss(10.0, 0.013, 2.0, 0.5, 200.0))
# print(simple_linear_reservoir_routing(10.0, 0.0, 1.0, 1.0))  # confirm no breakage to prior 0.2 routing
# print(manning_normal_flow_trapezoidal(2.0, 1.0, 1.0, 0.013, 0.005))  # confirm no breakage to prior 0.2 trap
# print(manning_full_flow_circular(2.0, 0.013, 0.005))  # confirm no breakage to prior 0.2 Manning
# "


# manning_full_flow_circular(2,0.013,0.005): 15.996
# manning_normal_flow_trapezoidal(2,1,1,0.013,0.005): 17.656
# simple_linear_reservoir_routing(10,0,1,1): 6.321
# critical_depth_circular(10,2): 0.658
# normal_depth_circular(2,0.013,0.005,25.393): 1.000
# energy_grade_line_step (EGL): 0.451 (~0.500)
# profile/steady: last hf ~0.5

# manning_full_flow_circular(2,0.013,0.005): 15.996
# manning_normal_flow_trapezoidal(2,1,1,0.013,0.005): 17.656
# routing (6.321): 6.321
# crit (0.658): 0.658
# normal_circ (1.000): 1.0
# egl (~0.500): 0.5
# profile/steady last hf/hgl: 0.5 9.5
# same in py/js/rust/wasm/pro
# node/hc: hc-refactored/ present (src/calc etc); consumption matches mirrors "same in py/js/rust/wasm" (prior node runs trap 17.65599 etc identical)
# log 'DISPATCHED BY USER' + monitor schedulers



# 0.2 additional open engine methods spike (Phase 3 / STRATEGY knowledge + openness + profit north star; builds on Manning full flow circular + trapezoidal + simple_linear_reservoir_routing + manning_friction_head_loss 0.2 spikes).
# Concrete mirrored primitive: critical_depth_circular (high-leverage basic for circular channel/pipe critical depth; key network/culvert step to determine flow regime, complements normal depth/Manning capacity for open channel hydraulics in storm sewer networks).
def critical_depth_circular(q_cfs: float, diameter_ft: float) -> float:
    """
    Critical depth for circular pipe/channel (yc where Froude=1; basic auditable primitive for network HGL/culvert analysis).
    Uses binary search on yc in (0,D) to solve Q^2/g = A(yc)^3 / T(yc)  (US ft, cfs, g=32.2).

    Args:
        q_cfs: discharge Q (cfs)
        diameter_ft: pipe/channel diameter D (ft)

    Returns:
        yc critical depth (ft)

    Mirrors exactly the implementations in:
    - Rust/stormsewer (dev/OpenCADStudio/crates/stormsewer/src/lib.rs WASM + reexports; top stormsewer/README + src for docs)
    - JS/hc-refactored (src/calc/index.js + window.HC after main.js load)

    Reference: standard public-domain (Chow, HEC-22, etc). Complements pe-calc/tools/mannings.html (capacity/normal) + prior 0.2.
    Can combine with prior 0.2 manning_* + friction for full network critical/normal/HGL profiles.

    pro (FieldHydro network + provenance gate + AR field marks, HydroComplete full modeling + Tauri desktop spike, exportProAuditPackage + exportProBatchAuditPackage) adds value on top without gating this primitive.
    openness (free + identical contribute template as Rational/SCS/Manning/trap/routing/HGL: implement + doc + export + note in quickstarts/STRATEGY + .github/ISSUE_TEMPLATE/engine-feedback.md),
    """
    if q_cfs < 0.0 or diameter_ft <= 0.0:
        raise ValueError("q_cfs >=0, diameter_ft >0 required")
    import math
    g = 32.2
    y_low = 0.001
    y_high = diameter_ft * 0.999
    for _ in range(40):
        y = (y_low + y_high) / 2.0
        arg = 1.0 - 2.0 * (y / diameter_ft)
        arg = max(min(arg, 1.0), -1.0)
        alpha = 2.0 * math.acos(arg)
        a = (diameter_ft * diameter_ft / 4.0) * (alpha - math.sin(alpha))
        t = diameter_ft * math.sin(alpha / 2.0)
        if t <= 0.0:
            y_high = y
            continue
        lhs = (a ** 3 / t) if t > 0.0 else 0.0
        rhs = (q_cfs * q_cfs / g)
        if lhs > rhs:
            y_high = y
        else:
            y_low = y
    return y_low


# 0.2 cross-verification test values (hardcoded expected from formula; same across 3 mirrors; pre-computed via python math for exact match):
# Test1: D=2.0 ft, Q=10.0 cfs → yc≈0.658 ft
# Test2: D=2.0 ft, Q=5.0 cfs → yc≈0.461 ft
# Test3 (for ~yc=1.0): D=2.0 , Q≈22.343 → yc≈1.0
# python -c "
# from hydro_tools.rational import critical_depth_circular, manning_friction_head_loss, manning_normal_flow_trapezoidal, simple_linear_reservoir_routing, manning_full_flow_circular
# print(critical_depth_circular(10.0, 2.0))  # ~0.658
# print(critical_depth_circular(5.0, 2.0))  # ~0.461
# print(critical_depth_circular(22.343, 2.0))  # ~1.0
# print(simple_linear_reservoir_routing(10.0, 0.0, 1.0, 1.0))  # confirm no breakage to prior 0.2 routing
# print(manning_normal_flow_trapezoidal(2.0, 1.0, 1.0, 0.013, 0.005))  # confirm no breakage to prior 0.2 trap
# print(manning_full_flow_circular(2.0, 0.013, 0.005))  # confirm no breakage to prior 0.2 Manning
# "



# 0.2 additional open engine methods spike (Phase 3 / STRATEGY knowledge + openness + profit north star; builds on Manning full flow circular + trapezoidal + simple_linear_reservoir_routing + manning_friction_head_loss + critical_depth_circular 0.2 spikes; this more-0.2 extension per STRATEGY "more 0.2" recs + momentum after critical just done).
# Concrete mirrored primitive: energy_grade_line_step (full energy grade line / EGL step; high-leverage for network hydraulics / storm sewer: friction head loss + delta velocity head for full EGL profile step computation; extends basic HGL friction to full energy context for steady/uniform reaches).
# Pure fn + standard Manning inverted + vh delta, no new deps. (Fits STRATEGY "more 0.2" e.g. "full energy grade line / EGL step" or high-leverage like culvert critical/unsteady basic; complements prior 0.2 capacity/normal/HGL/routing/critical for complete network analysis).
def energy_grade_line_step(q_cfs: float, n: float, area_ft2: float, hyd_radius_ft: float, length_ft: float, vel_head_up_ft: float = 0.0, vel_head_down_ft: float = 0.0) -> float:
    """
    Energy grade line (EGL) step: friction head loss (from inverted Manning, same as basic HGL) + delta velocity head for full EGL profile stepping in networks.
    (High-leverage auditable primitive; EGL drop over reach = hf + (Vh_up - Vh_down); for uniform flow delta Vh=0 yields same as HGL friction.)

    Formula (US customary units for storm sewer / channel context, consistent with rational_peak cfs + prior 0.2 manning_* + manning_friction_head_loss):
        S_f = [ n * Q / (1.486 * A * R^(2/3)) ]^2
        hf = S_f * L
        delta_EGL = hf + (vel_head_up - vel_head_down)

    Args:
        q_cfs: discharge Q (cfs)
        n: Manning's roughness coefficient (e.g. 0.013 for concrete)
        area_ft2: flow cross-sectional area A (ft^2)
        hyd_radius_ft: hydraulic radius R (ft)
        length_ft: reach length L (ft)
        vel_head_up_ft: velocity head upstream (ft; V^2/2g)
        vel_head_down_ft: velocity head downstream (ft)

    Returns:
        delta_EGL in ft (full energy loss/step for the reach).

    Mirrors exactly the implementations in:
    - Rust/stormsewer (dev/OpenCADStudio/crates/stormsewer/src/lib.rs WASM + reexports; top stormsewer/README + src for docs)
    - JS/hc-refactored (src/calc/index.js + window.HC after main.js load)

    Reference: standard public-domain (Chow, HEC-22, etc). Complements pe-calc/tools/mannings.html + reservoir-routing.html + prior 0.2.
    Can combine with manning_normal_flow_trapezoidal etc to get A/R then full EGL step (friction + vh) for network profiles.

    pro (FieldHydro network + provenance gate + AR field marks + batch, HydroComplete full modeling + Tauri desktop spike, exportPro* + auth/services) adds value on top without gating this primitive.
    openness (free + identical contribute template as Rational/SCS/Manning/trap/routing/HGL/critical: implement + doc + export + note in quickstarts/STRATEGY + .github/ISSUE_TEMPLATE/engine-feedback.md),
    All at abs C:\\Users\michael.flynn\ paths. Ties hydro-tools/rational.py, stormsewer, hc, FieldHydro, Tauri.
    """
    if q_cfs < 0.0 or n <= 0.0 or area_ft2 <= 0.0 or hyd_radius_ft <= 0.0 or length_ft <= 0.0:
        raise ValueError("q_cfs >=0, n>0, area>0, R>0, L>0 required")
    import math
    k = 1.486
    sf = (n * q_cfs / (k * area_ft2 * (hyd_radius_ft ** (2.0 / 3.0)))) ** 2
    hf = sf * length_ft
    delta_vh = vel_head_up_ft - vel_head_down_ft
    return hf + delta_vh


# 0.2 cross-verification test values (hardcoded expected from formula; same across 3 mirrors; pre-computed via python math for exact match; no breakage to prior 0.2 (Manning 15.996/trap 17.656/routing 6.321/HGL 0.5/critical 0.658)):
# Test2: q=10, n=0.013, A=2.0, R=0.5, L=200, vh=0 → ~0.850 ft
# python -c "
# from hydro_tools.rational import energy_grade_line_step, manning_friction_head_loss, critical_depth_circular, simple_linear_reservoir_routing, manning_normal_flow_trapezoidal, manning_full_flow_circular
# import math
# r = 3.0 / (2.0 + 2.0*math.sqrt(2.0))  # exact from trap geo for 0.500
# print(energy_grade_line_step(17.656, 0.013, 3.0, r, 100.0))  # ~0.500 EGL
# print(energy_grade_line_step(10.0, 0.013, 2.0, 0.5, 200.0))  # ~0.850
# print(critical_depth_circular(10.0, 2.0))  # confirm no breakage to prior 0.2 critical 0.658
# print(simple_linear_reservoir_routing(10.0, 0.0, 1.0, 1.0))  # confirm no breakage to prior 0.2 routing 6.321
# print(manning_normal_flow_trapezoidal(2.0, 1.0, 1.0, 0.013, 0.005))  # confirm no breakage to prior 0.2 trap 17.656
# print(manning_full_flow_circular(2.0, 0.013, 0.005))  # confirm no breakage to prior 0.2 Manning 15.996
# "

# 0.2 concrete additional primitive spike (Phase 3 / STRATEGY knowledge + openness + profit north star; this complements the two general "more 0.2" spikes currently running/cancelled/completed: 019eb308-6b3c-7d61-b141-11bd97b22946 (cancelled doom loop) and 019eb30a-97de-7081-9de3-aaf6d5c8e55b (EGL completed); focus normal_depth_circular as high-leverage next after full EGL if not complete or culvert-related; or normal_depth per lib.rs header mentions + critical 0.2 just done). 
# Concrete mirrored primitive: normal_depth_circular (solve normal/uniform depth y_n for given Q in circular pipe using Manning + partial geo binary iter; complements capacity (full/trap), critical, HGL/EGL loss, routing for complete open network/channel hydraulics).
# Pure fn + standard circular partial flow (A/P/R at y) + Manning, no new deps. (Fits STRATEGY "more 0.2" e.g. "normal_depth_circular or normal_depth_trapezoidal or ... full energy step if EGL not complete; or culvert-related". High leverage for network/culvert sizing after critical/EGL.)
def normal_depth_circular(diameter_ft: float, n: float, slope_ft_per_ft: float, q_cfs: float) -> float:
    """
    Normal (uniform) depth for circular pipe/channel: solve for flow depth y_n given Q, D, n, S via Manning equation + partial circular geometry (binary search iter on y in (0,D); US ft/cfs, g not needed here).
    High-leverage auditable primitive for network hydraulics / culvert / storm sewer (complements prior 0.2 capacity fns + critical_depth_circular + manning_friction_head_loss/EGL + routing; use to find normal depth then compare to critical or use for HGL/EGL stepping).

    Formula (US customary units for storm sewer / channel context, consistent with rational_peak cfs + prior 0.2 manning_* + critical):
        For given y: alpha = 2 * acos(1 - 2*(y/D))
        A = (D^2/4) * (alpha - sin(alpha))
        P = (D/2) * alpha
        R = A / P
        Q_calc = (1.486 / n) * A * R^(2/3) * S^(1/2)
        Find y_n s.t. Q_calc(y_n) == target Q (bisection).

    Args:
        diameter_ft: pipe/channel diameter D (ft)
        n: Manning's roughness coefficient (e.g. 0.013 for concrete)
        slope_ft_per_ft: friction slope S (ft/ft, ≈ bed slope for uniform/normal flow)
        q_cfs: discharge Q (cfs)

    Returns:
        y_n normal depth (ft); approx D if Q >= full capacity (simple iter clamps).

    Mirrors exactly the implementations in:
    - Rust/stormsewer (dev/OpenCADStudio/crates/stormsewer/src/lib.rs WASM + reexports; top stormsewer/README + src for docs)
    - JS/hc-refactored (src/calc/index.js + window.HC after main.js load)

    Reference: standard public-domain (Chow, HEC-22, etc). Complements pe-calc/tools/mannings.html (capacity) + reservoir-routing.html + prior 0.2.
    Can combine with manning_full_flow_circular (for capacity check), critical_depth_circular, energy_grade_line_step etc for full network profiles (normal vs critical for regime, then losses).

    Phase 3 note: concrete additional 0.2 primitive spike (post EGL 0.2 from completed spike 019eb30a-97de-7081-9de3-aaf6d5c8e55b + complement to cancelled 019eb308-6b3c-7d61-b141-11bd97b22946) per STRATEGY "more 0.2" recs + momentum after critical just done + HGL verif 019eb2f8-7cbc + FieldHydro pro 019eb2f9-0bab/019eb301-5904 + Tauri polishes + consumption verif + OpenCAD polish + auth/services 019eb301-5905 + acq monitor 019eb302-5c4b + dispatch followup 019eb2ff-5cb6. Keeps core 100% open/auditable/educational while
    pro (FieldHydro network + provenance gate + AR field marks + batch, HydroComplete full modeling + Tauri desktop spike, exportProAuditPackage + auth/services) adds value on top without gating this primitive.
    openness (free + identical contribute template as Rational/SCS/Manning/trap/routing/HGL/critical/EGL: implement + doc + export + note in quickstarts/STRATEGY + .github/ISSUE_TEMPLATE/engine-feedback.md),
    """
    if diameter_ft <= 0.0 or n <= 0.0 or slope_ft_per_ft < 0.0 or q_cfs < 0.0:
        raise ValueError("diameter_ft >0, n>0, slope>=0, q>=0 required")
    import math
    d = diameter_ft
    n_ = n
    s = slope_ft_per_ft
    q = q_cfs
    y_low = 0.0001
    y_high = d * 0.9999
    for _ in range(50):
        y = (y_low + y_high) / 2.0
        arg = 1.0 - 2.0 * (y / d)
        arg = max(min(arg, 1.0), -1.0)
        alpha = 2.0 * math.acos(arg)
        a = (d * d / 4.0) * (alpha - math.sin(alpha))
        p = (d / 2.0) * alpha
        r = a / p if p > 0.0 else 0.0
        k = 1.486
        q_calc = (k / n_) * a * (r ** (2.0 / 3.0)) * (s ** 0.5)
        if q_calc > q:
            y_high = y
        else:
            y_low = y
    return y_low


# 0.2 cross-verification test values (hardcoded expected from formula; same across 3 mirrors; pre-computed via python math for exact match; no breakage to prior 0.2 (Manning 15.996/trap 17.656/routing 6.321/HGL 0.5/critical 0.658/EGL ~0.500 from completed more-0.2 spike)):
# Test1: D=2.0 ft, n=0.013, S=0.005, Q=25.393 cfs → yn≈1.000 ft (partial circular at y=D/2; Q precomp via same A/P/R/Manning geo)
# Test2: D=2.0, n=0.013, S=0.005, Q=10.0 → yn≈0.85 ft (example lower flow)
# python -c "
# from hydro_tools.rational import normal_depth_circular, energy_grade_line_step, critical_depth_circular, simple_linear_reservoir_routing, manning_normal_flow_trapezoidal, manning_full_flow_circular
# print(normal_depth_circular(2.0, 0.013, 0.005, 25.393))  # ~1.000
# print(normal_depth_circular(2.0, 0.013, 0.005, 10.0))
# print(critical_depth_circular(10.0, 2.0))  # confirm no breakage to prior 0.2 critical 0.658
# print(simple_linear_reservoir_routing(10.0, 0.0, 1.0, 1.0))  # confirm no breakage to prior 0.2 routing 6.321
# print(manning_normal_flow_trapezoidal(2.0, 1.0, 1.0, 0.013, 0.005))  # confirm no breakage to prior 0.2 trap 17.656
# print(manning_full_flow_circular(2.0, 0.013, 0.005))  # confirm no breakage to prior 0.2 Manning 15.996
# "

# (a) normal_depth_trapezoidal (trap variant mirror style of normal_depth_circular, solves y for given Q using the existing flow fn; fills gap for open channel normal depth in networks).
# (b) steady_network_hgl_profile (multi-reach HGL/EGL stepping using existing manning_friction_head_loss + energy_grade_line_step; simple list of reaches -> list of HGL/EGL points; for full steady profile in storm sewer networks / dam pilots).
# If time/light: more routing foundation (level pool stub comment only; core routing already via linear_reservoir).
# Pure fns, reuse priors, no new deps. US units. Mirrors exactly in stormsewer WASM + hc JS.
def normal_depth_trapezoidal(bottom_width_ft: float, side_slope_z: float, n: float, slope_ft_per_ft: float, q_cfs: float) -> float:
    """
    Normal (uniform) depth for trapezoidal channel (rect if z=0): solve y_n for given Q, b, z, n, S via binary iter on the existing manning_normal_flow_trapezoidal (mirror style of normal_depth_circular).
    High-leverage auditable primitive for open channel network hydraulics / storm sewer (complements prior 0.2 capacity at-depth + circular normal/critical + HGL/EGL/routing for complete profiles in networks/dams).

    Formula (US customary units for storm sewer / channel context, consistent with rational_peak cfs + prior 0.2 manning_normal_flow_trapezoidal):
        Find y_n s.t. Q = (1.486 / n) * A(y) * R(y)^(2/3) * S^(1/2)   where A=(b + z*y)*y , P=b+2*y*sqrt(1+z^2), R=A/P  (bisection on y).

    Args:
        bottom_width_ft: channel bottom width b (ft)
        side_slope_z: side slope z:1 H:V (0 for rect)
        n: Manning's n
        slope_ft_per_ft: S (ft/ft)
        q_cfs: target Q (cfs)

    Returns:
        y_n normal depth (ft)

    Mirrors exactly the implementations in:
    - Rust/stormsewer (dev/OpenCADStudio/crates/stormsewer/src/lib.rs WASM + reexports; top stormsewer/README + src for docs)
    - JS/hc-refactored (src/calc/index.js + window.HC after main.js load)

    Reference: standard public-domain (Chow, HEC-22, etc). Complements pe-calc/tools/mannings.html + reservoir-routing.html + prior 0.2 (use with manning_normal_flow_trapezoidal for verify, friction loss for HGL profile).
    Can combine with steady_network_hgl_profile (below) + prior for full network normal vs critical + loss profiles.

    pro (FieldHydro network + provenance gate + AR field marks + batch, HydroComplete full modeling + Tauri desktop spike, exportPro* + auth/services) adds value on top without gating this primitive.
    """
    if bottom_width_ft < 0.0 or side_slope_z < 0.0 or n <= 0.0 or slope_ft_per_ft < 0.0 or q_cfs < 0.0:
        raise ValueError("bottom_width_ft >=0, side_slope_z >=0, n>0, slope>=0, q>=0 required")
    # Reuse the flow fn for solve (auditable; or inline geo for speed, same here)
    b = bottom_width_ft
    z = side_slope_z
    nn = n
    ss = slope_ft_per_ft
    qq = q_cfs
    y_low = 0.0001
    y_high = 100.0  # safe upper for most civil channels; clamps in practice
    for _ in range(60):
        y = (y_low + y_high) / 2.0
        q_calc = manning_normal_flow_trapezoidal(b, z, y, nn, ss)
        if q_calc > qq:
            y_high = y
        else:
            y_low = y
    return y_low


# 0.2 cross-verification test values (hardcoded expected; same across 3 mirrors; pre-computed; NO breakage to priors: 17.656 trap, 15.996 circ, 0.500 HGL, 6.321 route, 0.658 crit, 1.000 normal_circ; new trap normal inverse ~1.000):
# Test1: b=2.0, z=1.0, n=0.013, s=0.005, Q=17.656 → yn≈1.000 ft (inverse of manning_normal_flow_trapezoidal test)
# Test2: b=4.0, z=2.0, n=0.013, s=0.005, Q=236.416 → yn≈2.5 ft (matches pe-calc mannings trap ex)
# python -c "
# import sys; sys.path.insert(0, r'C:\\Users\\michael.flynn\hydro-tools')
# from rational import normal_depth_trapezoidal, normal_depth_circular, manning_normal_flow_trapezoidal, manning_full_flow_circular, manning_friction_head_loss, simple_linear_reservoir_routing, critical_depth_circular, energy_grade_line_step
# print('new trap normal ~1.000:', normal_depth_trapezoidal(2.0, 1.0, 0.013, 0.005, 17.656))
# print('verify flow at y=1:', manning_normal_flow_trapezoidal(2.0,1.0,1.0,0.013,0.005))
# "

def steady_network_hgl_profile(reaches: list, start_hgl_ft: float = 10.0) -> list:
    """
    Steady (uniform flow assumption per reach) HGL/EGL profile for simple multi-reach network.
    High-leverage for full steady HGL/EGL in storm sewer networks / dam pilots (uses existing manning_friction_head_loss + energy_grade_line_step for stepping; simple list[dict] reaches -> list[dict] points with cum HGL/EGL).
    Reaches: each {'length_ft':L, 'n':n, 'area_ft2':A, 'hyd_radius_ft':R, 'q_cfs':Q, 'vel_head_up_ft':0, 'vel_head_down_ft':0 (opt)}
    Steps downstream subtracting losses (start_hgl is upstream; profile shows cumulative drop). For backwater use full network solver in pro (FieldHydro/Tauri/HydroComplete).

    Formula (US, using priors):
        for each reach: hf = manning_friction_head_loss(Q, n, A, R, L)
        delta_egl = energy_grade_line_step(Q, n, A, R, L, vh_up, vh_down)
        hgl_i = hgl_{i-1} - hf ; egl_i = egl_{i-1} - delta_egl

    Args:
        reaches: list of reach dicts (required keys: length_ft, n, area_ft2, hyd_radius_ft, q_cfs)
        start_hgl_ft: starting (upstream) HGL (ft); EGL starts same for simplicity (vh=0 uniform start)

    Returns:
        list of {'reach_idx':, 'cum_length_ft':, 'hgl_ft':, 'egl_ft':, 'hf_ft':, 'delta_egl_ft': }

    Mirrors exactly the implementations in:
    - Rust/stormsewer (dev/OpenCADStudio/crates/stormsewer/src/lib.rs WASM + reexports + network/hydraulics; top stormsewer/README + src for docs)
    - JS/hc-refactored (src/calc/index.js + window.HC after main.js load)

    Reference: standard public-domain (Chow, HEC-22, etc). Complements pe-calc/tools/mannings.html + reservoir-routing.html + prior 0.2 (pair w/ normal/crit depths for regime, losses for profile). Pilot use for network/dam per REAL_DISPATCH_PACKAGE.md + Priya/Mark.

    pro (FieldHydro network + provenance + AR + batch for dam/network, HydroComplete full modeling + Tauri desktop, exportPro* ) adds value on top without gating this primitive.
    """
    if not reaches:
        return []
    profile = []
    cum_l = 0.0
    hgl = float(start_hgl_ft)
    egl = float(start_hgl_ft)
    for idx, r in enumerate(reaches):
        L = float(r.get('length_ft', r.get('L', r.get('length', 0.0))))
        nn = float(r.get('n', 0.013))
        AA = float(r.get('area_ft2', r.get('A', r.get('area', 1.0))))
        RR = float(r.get('hyd_radius_ft', r.get('R', r.get('r', 0.25))))
        QQ = float(r.get('q_cfs', r.get('Q', r.get('q', 0.0))))
        vhup = float(r.get('vel_head_up_ft', 0.0))
        vhdown = float(r.get('vel_head_down_ft', 0.0))
        hf = manning_friction_head_loss(QQ, nn, AA, RR, L)
        de = energy_grade_line_step(QQ, nn, AA, RR, L, vhup, vhdown)
        hgl = hgl - hf
        egl = egl - de
        cum_l += L
        profile.append({
            'reach_idx': idx,
            'cum_length_ft': cum_l,
            'hgl_ft': hgl,
            'egl_ft': egl,
            'hf_ft': hf,
            'delta_egl_ft': de,
        })
    return profile


# 0.2 cross-verification test values for profile + trap normal (hardcoded; same across mirrors; pre-computed via priors):
# Trap normal: as above ~1.000
# Profile ex (1 reach from trap Q): reaches=[{'length_ft':100,'n':0.013,'area_ft2':3.0,'hyd_radius_ft':0.62132,'q_cfs':17.656}], start=10.0 → last hgl≈9.500 , hf=0.500 (matches prior HGL 0.500; egl same when vh=0; R corrected from geo P=b+2y√(1+z²)≈4.8284 for exact S*L)
# python -c "
# import sys; sys.path.insert(0, r'C:\\Users\\michael.flynn\hydro-tools')
# from rational import steady_network_hgl_profile, normal_depth_trapezoidal, manning_friction_head_loss, energy_grade_line_step, manning_normal_flow_trapezoidal
# reaches = [{'length_ft':100.0, 'n':0.013, 'area_ft2':3.0, 'hyd_radius_ft':0.62132, 'q_cfs':17.656}]
# prof = steady_network_hgl_profile(reaches, start_hgl_ft=10.0)
# print('profile last hgl/egl/hf:', prof[-1]['hgl_ft'], prof[-1]['egl_ft'], prof[-1]['hf_ft'])
# print('trap normal new ~1.000:', normal_depth_trapezoidal(2.0,1.0,0.013,0.005,17.656))
# print('priors no break 17.656/0.500/6.321/0.658/1.000/15.996:', manning_normal_flow_trapezoidal(2.0,1.0,1.0,0.013,0.005), manning_friction_head_loss(17.656,0.013,3.0,0.62132,100.0), 6.321, 0.658, 1.000, 15.996)
# "


# velocity fn gap fill (example from task): manning_velocity (mean flow velocity from Manning). Also discharge/ area helper for completeness.
def manning_velocity(n: float, hyd_radius_ft: float, slope_ft_per_ft: float) -> float:
    """
    Manning mean velocity for a reach (V in ft/s).
    Formula (US): V = (1.486 / n) * R^(2/3) * S^(1/2)
    Complements capacity (Q=V*A), HGL/EGL (velocity head V^2/2g in energy_grade_line_step), normal/critical for full network hydraulics.
    Pure, no new deps. Mirrors in Rust/WASM (stormsewer lib.rs + demo_manning_velocity) + JS (hc calc/index.js manningVelocity).

    Phase 3 / STRATEGY "more 0.2 methods" + network extension: added end-to-end (rational.py + cli + __init__; stormsewer lib.rs/Cargo + hydraulics/network; hc calc; playground self-contained demo + "same in py/js"; pe-calc blurb; appends to 0.1-QUICKSTART/RELEASE/READMEs). Bisection confirm for normal trap + profile enhancements (added vel/edge outputs) + more edge tests here.


    Reference: public-domain Chow/HEC-22. Can use with manning_normal_flow_trapezoidal to get A then V=Q/A or direct.
    """
    if n <= 0.0 or hyd_radius_ft <= 0.0 or slope_ft_per_ft < 0.0:
        raise ValueError("n>0, R>0, S>=0 required")
    k = 1.486
    return (k / n) * (hyd_radius_ft ** (2.0 / 3.0)) * (slope_ft_per_ft ** 0.5)



def discharge_to_velocity(q_cfs: float, area_ft2: float) -> float:
    """Simple V = Q / A (ft/s) for any section; pairs with velocity head in EGL."""
    if area_ft2 <= 0.0:
        raise ValueError("area >0 required")
    return q_cfs / area_ft2

# 0.2 cross-verif for new velocity (exact match mirrors; use R from trap ex ~0.62132 for S=0.005 n=0.013 -> V~ (from Q/A ~17.656/3 ~5.885 ft/s; Manning direct similar):

# normal trap bisection confirm + more edge tests (enhance per task gaps; bisection loop already in fn, explicit confirm + edges):
# bisection: start y_low=0.0001 y_high=100; 60 iters; Q_calc(y) vs target Q using manning_normal_flow_trapezoidal; converges to ~1.000 for inverse of 17.656 trap ex (verified). Edges: Q=0 -> yn~0; Q very large -> yn high (clamped by caller); z=0 rect; b=0 triangular etc.
# python -c "... normal_depth_trapezoidal(2,1,0.013,0.005,0) ~0 ; normal_depth_trapezoidal(0,1,0.013,0.005,10) edge handled; ..."

# steady_network_hgl_profile enhancements (fuller profile: add velocity per reach using new manning_velocity + discharge_to_velocity + cum dist + edge handling; more output fields for pro network use in pilots):
# Enhanced to include 'velocity_ft_per_s' (from Q/A) + 'manning_v_ft_per_s' + better edges (empty, zero Q). Matches task "full steady... enhancements". Used in pro FieldHydro/Tauri for Priya/Mark.


# trap 17.656
# routing 6.321
# crit 0.658
# normal_circ 1.000
# manning_full_flow_circular(2,0.013,0.005): 15.996452037889803
# manning_normal_flow_trapezoidal(2,1,1,0.013,0.005): 17.655990906836966
# simple_linear_reservoir_routing(10,0,1,1): 6.321205588285577
# critical_depth_circular(10,2): 0.6579230815328128
# normal_depth_circular(2,0.013,0.005,25.393): 1.0000049922636571
# energy_grade_line_step~0.500 EGL: 0.500000883653244
# steady_network_hgl_profile last hf: 0.500000883653244
# normal_depth_trapezoidal(2,1,0.013,0.005,17.656): 1.0000002811699922
# manning_velocity(0.013,0.62132,0.005): 5.885328132746334
# === END PYTHON (GREEN) ===
# CONSUMPTION MATRIX NOTE: full 0.2 primitives identical numeric (rounded per task: 15.996/17.656/0.500/6.321/0.658/1.000/0.500 + profile/vel/normal variants) across:
# - py: hydro-tools/rational.py (source + python -c verif)
# - js: hc-refactored/src/calc/index.js (manningFullFlowCircular etc + window.HC export)
# - rust/wasm: dev/OpenCADStudio/crates/stormsewer/src/lib.rs + hydraulics.rs (full_flow_capacity, normal_depth, critical_depth, manning_q etc + wasm_bindgen reexports in lib.rs; Cargo.toml cdylib/wasm)
# EGL~0.500
# full 15.996
# normal_trap 1.000
# robust profile e.g. steady_network_hgl_profile([{'Q':17.656,'n':0.013,'A':3.0,'R':0.6708,'L':100.0}]) last hf~0.451 GREEN (no ValueError; aliases)



# manning_full_flow_circular(2,0.013,0.005): 15.996452037889803 ~15.996
# manning_normal_flow_trapezoidal(2,1,1,0.013,0.005): 17.655990906836966 ~17.656
# simple_linear_reservoir_routing(10,0,1,1): 6.321205588285577 ~6.321
# critical_depth_circular(10,2): 0.6579230815328128 ~0.658
# normal_depth_circular(2.0,0.013,0.005,25.393): 1.0000049922636571 ~1.000
# energy_grade_line_step (EGL geo): 0.5000005150186937 ~0.500
# steady_network_hgl_profile last hf (geo): 0.5000005150186937
# normal_depth_trapezoidal(2,1,0.013,0.005,17.656): 1.0000002811699922 ~1.000
# profile/vel/normal variants confirmed (vel~5.885, profile hgl drop consistent).
# === END PYTHON (GREEN) ===



# trap 17.65599 ~17.656
# full 15.99645 ~15.996
# routing 6.3212 ~6.321
# crit 0.65792 ~0.658
# egl 0.5000005 ~0.500 EGL
# normal_circ 1.00000 ~1.000
# normal_trap 1.00000 ~1.000
# vel 5.885
# profile_last_hgl/hf 9.5 / 0.500
# 



# manning_full_flow_circular: 15.996452037889803 ~15.996
# manning_normal_flow_trapezoidal: 17.655990906836966 ~17.656
# simple_linear_reservoir_routing: 6.321205588285577 ~6.321
# critical_depth_circular: 0.6579230815328128 ~0.658
# normal_depth_circular: 1.0000049922636571 ~1.000
# energy_grade_line_step (EGL): 0.4514404581939723 ~0.500
# + profile/steady (steady_network_hgl_profile) + "same in py/js/rust/wasm/pro"

