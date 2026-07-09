"""
rational.py
Basic Rational Method peak flow calculator and related open-channel/storm-sewer hydraulics primitives.

Q = C * i * A   (cfs when i in in/hr, A in acres, or scaled)
"""

import math
from typing import Any, Dict, List, Tuple


def _circular_geometry(depth_ft: float, diameter_ft: float) -> Tuple[float, float, float]:
    """Geometry of a partly full circular section: (area, top width, wetted perimeter).

    ``alpha = 2*acos(1 - 2y/D)`` is the full central angle subtending the wetted
    segment, so area = (D^2/8)(alpha - sin alpha), top width = D*sin(alpha/2),
    and wetted perimeter = (D/2)*alpha. All in ft / ft^2.
    """
    arg = max(min(1.0 - 2.0 * (depth_ft / diameter_ft), 1.0), -1.0)
    alpha = 2.0 * math.acos(arg)
    area = (diameter_ft * diameter_ft / 8.0) * (alpha - math.sin(alpha))
    top_width = diameter_ft * math.sin(alpha / 2.0)
    wetted_perimeter = (diameter_ft / 2.0) * alpha
    return area, top_width, wetted_perimeter


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

def scs_runoff_depth(rainfall_in: float, cn: float) -> float:
    """
    Simple SCS runoff depth (inches) using the standard approximation.
    Useful for hydrograph volume calculations and consistent with the existing rational_peak.

    Formula (US customary units):
        S = (1000 / CN) - 10      (potential maximum retention, in)
        Ia = 0.2 * S              (initial abstraction, in)
        Q = (P - Ia)^2 / (P - Ia + S)   for P > Ia, else 0

    Args:
        rainfall_in: rainfall depth P (in)
        cn: SCS curve number CN (0, 100]

    Returns:
        runoff depth Q (in).
    """
    if not (0.0 < cn <= 100.0):
        raise ValueError("Curve number CN must be in (0, 100]")
    if rainfall_in <= 0:
        return 0.0
    s = (1000.0 / cn) - 10.0
    ia = 0.2 * s
    if rainfall_in <= ia:
        return 0.0
    return ((rainfall_in - ia) ** 2) / (rainfall_in - ia + s)


# Manning full-flow capacity for a circular storm sewer / channel. Complements Rational/SCS.
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

    Reference: standard public-domain (Chow, HEC-22).
    """
    if diameter_ft <= 0.0 or n <= 0.0 or slope_ft_per_ft < 0.0:
        raise ValueError("diameter_ft > 0, n > 0, slope_ft_per_ft >= 0 required")
    d = diameter_ft
    a = math.pi * (d / 2.0) ** 2
    r = d / 4.0
    k = 1.486
    return (k / n) * a * (r ** (2.0 / 3.0)) * (slope_ft_per_ft ** 0.5)


# Manning normal (uniform) flow capacity for a trapezoidal channel (rectangular if z=0).
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

    Reference: standard public-domain (Chow, V.T. "Open-Channel Hydraulics"; HEC-22; NRCS NEH).
    """
    if bottom_width_ft < 0.0 or side_slope_z < 0.0 or flow_depth_ft <= 0.0 or n <= 0.0 or slope_ft_per_ft < 0.0:
        raise ValueError("bottom_width_ft >=0, side_slope_z >=0, flow_depth_ft >0, n>0, slope_ft_per_ft >=0 required")
    b = bottom_width_ft
    z = side_slope_z
    y = flow_depth_ft
    a = (b + z * y) * y
    p = b + 2.0 * y * math.sqrt(1.0 + z * z)
    r = a / p if p > 0.0 else 0.0
    k = 1.486
    return (k / n) * a * (r ** (2.0 / 3.0)) * (slope_ft_per_ft ** 0.5)


# Simple one-step linear reservoir routing for channel/reservoir hydrograph attenuation.
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

    Reference: standard public-domain linear reservoir / simple routing model (e.g. "Applied Hydrology", Chow et al.; NRCS intro methods).
    """
    if k_hr <= 0.0 or dt_hr <= 0.0 or inflow_cfs < 0.0 or prev_outflow_cfs < 0.0:
        raise ValueError("k_hr >0, dt_hr >0, flows >=0 required")
    e = math.exp(-dt_hr / k_hr)
    return prev_outflow_cfs * e + inflow_cfs * (1.0 - e)


# Manning friction head loss over a reach (HGL step) via inverted Manning.
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

    Reference: standard public-domain (Chow, HEC-22). Combine with manning_normal_flow_trapezoidal etc.
    to get A/R, then this loss for an HGL profile.
    """
    if q_cfs < 0.0 or n <= 0.0 or area_ft2 <= 0.0 or hyd_radius_ft <= 0.0 or length_ft <= 0.0:
        raise ValueError("q_cfs >=0, n>0, area>0, R>0, L>0 required")
    k = 1.486
    sf = (n * q_cfs / (k * area_ft2 * (hyd_radius_ft ** (2.0 / 3.0)))) ** 2
    return sf * length_ft


# Critical depth for a circular pipe/channel (determines flow regime for network/culvert analysis).
def critical_depth_circular(q_cfs: float, diameter_ft: float) -> float:
    """
    Critical depth for circular pipe/channel (yc where Froude=1; basic auditable primitive for network HGL/culvert analysis).
    Uses binary search on yc in (0,D) to solve Q^2/g = A(yc)^3 / T(yc)  (US ft, cfs, g=32.2).

    Args:
        q_cfs: discharge Q (cfs)
        diameter_ft: pipe/channel diameter D (ft)

    Returns:
        yc critical depth (ft)

    Reference: standard public-domain (Chow, HEC-22).
    """
    if q_cfs < 0.0 or diameter_ft <= 0.0:
        raise ValueError("q_cfs >=0, diameter_ft >0 required")
    g = 32.2
    y_low = 0.001
    y_high = diameter_ft * 0.999
    for _ in range(40):
        y = (y_low + y_high) / 2.0
        a, t, _ = _circular_geometry(y, diameter_ft)
        if t <= 0.0:
            y_high = y
            continue
        lhs = a ** 3 / t
        rhs = (q_cfs * q_cfs / g)
        if lhs > rhs:
            y_high = y
        else:
            y_low = y
    return y_low


# Energy grade line (EGL) step: friction head loss plus change in velocity head over a reach.
def energy_grade_line_step(q_cfs: float, n: float, area_ft2: float, hyd_radius_ft: float, length_ft: float, vel_head_up_ft: float = 0.0, vel_head_down_ft: float = 0.0) -> float:
    """
    Energy grade line (EGL) step: friction head loss (from inverted Manning, same as basic HGL) + delta velocity head for full EGL profile stepping in networks.
    (High-leverage auditable primitive; EGL drop over reach = hf + (Vh_up - Vh_down); for uniform flow delta Vh=0 yields same as HGL friction.)

    Formula (US customary units for storm sewer / channel context):
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

    Reference: standard public-domain (Chow, HEC-22). Combine with manning_normal_flow_trapezoidal etc.
    to get A/R, then this full EGL step (friction + velocity head) for network profiles.
    """
    hf = manning_friction_head_loss(q_cfs, n, area_ft2, hyd_radius_ft, length_ft)
    return hf + (vel_head_up_ft - vel_head_down_ft)


# Normal (uniform) depth for a circular pipe/channel: solve y_n for given Q via Manning + partial geometry.
def normal_depth_circular(diameter_ft: float, n: float, slope_ft_per_ft: float, q_cfs: float) -> float:
    """
    Normal (uniform) depth for circular pipe/channel: solve for flow depth y_n given Q, D, n, S via Manning equation + partial circular geometry (binary search iter on y in (0,D); US ft/cfs, g not needed here).
    Use to find normal depth then compare to critical, or for HGL/EGL stepping.

    Formula (US customary units for storm sewer / channel context):
        For given y: alpha = 2 * acos(1 - 2*(y/D))
        A = (D^2/8) * (alpha - sin(alpha))
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
        y_n normal depth (ft). Raises ValueError if Q exceeds the pipe's maximum
        capacity (Manning discharge is non-monotonic in depth near full).

    Reference: standard public-domain (Chow, HEC-22). Combine with manning_full_flow_circular (capacity
    check), critical_depth_circular, and energy_grade_line_step for full network profiles.
    """
    if diameter_ft <= 0.0 or n <= 0.0 or slope_ft_per_ft < 0.0 or q_cfs < 0.0:
        raise ValueError("diameter_ft >0, n>0, slope>=0, q>=0 required")
    d = diameter_ft
    s = slope_ft_per_ft
    k = 1.486

    def q_at(depth: float) -> float:
        a, _, p = _circular_geometry(depth, d)
        r = a / p if p > 0.0 else 0.0
        return (k / n) * a * (r ** (2.0 / 3.0)) * (s ** 0.5)

    y_low = 0.0001
    y_high = d * 0.9999
    for _ in range(50):
        y = (y_low + y_high) / 2.0
        if q_at(y) > q_cfs:
            y_high = y
        else:
            y_low = y
    # Manning discharge in a circular section is non-monotonic in depth (it peaks
    # near y/D ~ 0.94 at ~1.08x full-flow, then drops to full at y=D). If the
    # bisection never brackets the target, Q exceeds the pipe's maximum capacity
    # and the pipe surcharges — signal that instead of returning a near-full depth.
    if q_cfs > 0.0 and abs(q_at(y_low) - q_cfs) > 1e-3 * q_cfs:
        raise ValueError("Q exceeds pipe capacity at this slope; pipe surcharges")
    return y_low


# Normal (uniform) depth for a trapezoidal channel: solve y_n for given Q using manning_normal_flow_trapezoidal.
def normal_depth_trapezoidal(bottom_width_ft: float, side_slope_z: float, n: float, slope_ft_per_ft: float, q_cfs: float) -> float:
    """
    Normal (uniform) depth for trapezoidal channel (rect if z=0): solve y_n for given Q, b, z, n, S via binary iter on the existing manning_normal_flow_trapezoidal.

    Formula (US customary units for storm sewer / channel context):
        Find y_n s.t. Q = (1.486 / n) * A(y) * R(y)^(2/3) * S^(1/2)   where A=(b + z*y)*y , P=b+2*y*sqrt(1+z^2), R=A/P  (bisection on y).

    Args:
        bottom_width_ft: channel bottom width b (ft)
        side_slope_z: side slope z:1 H:V (0 for rect)
        n: Manning's n
        slope_ft_per_ft: S (ft/ft)
        q_cfs: target Q (cfs)

    Returns:
        y_n normal depth (ft)

    Reference: standard public-domain (Chow, HEC-22). Verify with manning_normal_flow_trapezoidal;
    pair with friction loss for an HGL profile.
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
    y_high = 100.0  # safe upper bound for civil channels
    # Trapezoidal discharge is monotonic in depth, so if the requested Q exceeds
    # the flow at the upper bound the solver would return the arbitrary cap;
    # signal that the depth is outside the searched range instead.
    if manning_normal_flow_trapezoidal(b, z, y_high, nn, ss) < qq:
        raise ValueError("Q exceeds channel flow at 100 ft depth; increase bound or check inputs")
    for _ in range(60):
        y = (y_low + y_high) / 2.0
        q_calc = manning_normal_flow_trapezoidal(b, z, y, nn, ss)
        if q_calc > qq:
            y_high = y
        else:
            y_low = y
    return y_low


def steady_network_hgl_profile(reaches: List[Dict[str, float]], start_hgl_ft: float = 10.0) -> List[Dict[str, Any]]:
    """
    Steady (uniform flow assumption per reach) HGL/EGL profile for simple multi-reach network.
    High-leverage for full steady HGL/EGL in storm sewer networks / dam pilots (uses existing manning_friction_head_loss + energy_grade_line_step for stepping; simple list[dict] reaches -> list[dict] points with cum HGL/EGL).
    Reaches: each {'length_ft':L, 'n':n, 'area_ft2':A, 'hyd_radius_ft':R, 'q_cfs':Q, 'vel_head_up_ft':0, 'vel_head_down_ft':0 (opt)}
    Steps downstream subtracting losses (start_hgl is upstream; profile shows cumulative drop). Assumes uniform flow per reach; not a backwater solver.

    Formula (US, using priors):
        for each reach: hf = manning_friction_head_loss(Q, n, A, R, L)
        delta_egl = energy_grade_line_step(Q, n, A, R, L, vh_up, vh_down)
        hgl_i = hgl_{i-1} - hf ; egl_i = egl_{i-1} - delta_egl

    Args:
        reaches: list of reach dicts (required keys: length_ft, n, area_ft2, hyd_radius_ft, q_cfs)
        start_hgl_ft: starting (upstream) HGL (ft); EGL starts same for simplicity (vh=0 uniform start)

    Returns:
        list of {'reach_idx':, 'cum_length_ft':, 'hgl_ft':, 'egl_ft':, 'hf_ft':, 'delta_egl_ft': }

    Reference: standard public-domain (Chow, HEC-22). Pair with normal/critical depths for regime,
    losses for the profile.
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


# Manning mean flow velocity; discharge_to_velocity helper follows.
def manning_velocity(n: float, hyd_radius_ft: float, slope_ft_per_ft: float) -> float:
    """
    Manning mean velocity for a reach (V in ft/s).

    Formula (US customary units): V = (1.486 / n) * R^(2/3) * S^(1/2)

    Args:
        n: Manning's roughness coefficient
        hyd_radius_ft: hydraulic radius R (ft; A/P)
        slope_ft_per_ft: friction slope S (ft/ft)

    Returns:
        V mean velocity (ft/s).

    Reference: public-domain (Chow, HEC-22).
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

