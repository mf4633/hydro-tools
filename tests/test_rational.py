"""
Tests for the open hydraulic primitives in ``hydro_tools.rational``.

The expected values pin the cross-verification numbers that previously lived
only in source comments, so any change to a formula is caught here.
"""
import math

import pytest

from hydro_tools import rational as r


# --- Rational method -------------------------------------------------------

def test_rational_peak_basic():
    assert r.rational_peak(0.5, 4.0, 2.0) == pytest.approx(4.0)


@pytest.mark.parametrize(
    "c, i, a",
    [
        (0.0, 4.0, 2.0),    # C must be > 0
        (1.5, 4.0, 2.0),    # C must be <= 1
        (0.5, 0.0, 2.0),    # intensity must be > 0
        (0.5, 4.0, 0.0),    # area must be > 0
    ],
)
def test_rational_peak_validation(c, i, a):
    with pytest.raises(ValueError):
        r.rational_peak(c, i, a)


def test_batch_rational():
    out = r.batch_rational({"A": 1.0, "B": 2.0}, c=0.5, i=4.0)
    assert out == {"A": pytest.approx(2.0), "B": pytest.approx(4.0)}


# --- SCS runoff depth ------------------------------------------------------

def test_scs_runoff_depth_value():
    assert r.scs_runoff_depth(3.0, 75.0) == pytest.approx(0.9607843137254899)


def test_scs_runoff_depth_below_initial_abstraction():
    # rainfall below Ia (=0.2*S) yields zero runoff
    assert r.scs_runoff_depth(0.1, 75.0) == 0.0


def test_scs_runoff_depth_nonpositive_rain():
    assert r.scs_runoff_depth(0.0, 75.0) == 0.0


def test_scs_runoff_depth_cn_at_100_is_all_runoff():
    # CN = 100 -> S = 0 -> Ia = 0 -> all rainfall becomes runoff
    assert r.scs_runoff_depth(3.0, 100.0) == pytest.approx(3.0)


@pytest.mark.parametrize("cn", [0.0, -5.0, 100.1, 150.0])
def test_scs_runoff_depth_invalid_cn(cn):
    with pytest.raises(ValueError):
        r.scs_runoff_depth(3.0, cn)


# --- Manning capacity ------------------------------------------------------

def test_manning_full_flow_circular():
    assert r.manning_full_flow_circular(2.0, 0.013, 0.005) == pytest.approx(
        15.996452037889803
    )


def test_manning_normal_flow_trapezoidal():
    assert r.manning_normal_flow_trapezoidal(2.0, 1.0, 1.0, 0.013, 0.005) == pytest.approx(
        17.655990906836966
    )


def test_manning_normal_flow_rectangular_zero_z():
    # z = 0 -> rectangular section. Expected value pinned independently
    # (A=0.5, P=2.0, R=0.25): Q = (1.486/0.025)*0.5*0.25**(2/3)*0.01**0.5.
    assert r.manning_normal_flow_trapezoidal(1.0, 0.0, 0.5, 0.025, 0.01) == pytest.approx(
        1.1794, abs=1e-3
    )


@pytest.mark.parametrize(
    "d, n, s",
    [
        (0.0, 0.013, 0.005),   # diameter must be > 0
        (2.0, 0.0, 0.005),     # n must be > 0
        (2.0, 0.013, -0.001),  # slope must be >= 0
    ],
)
def test_manning_full_flow_circular_validation(d, n, s):
    with pytest.raises(ValueError):
        r.manning_full_flow_circular(d, n, s)


# --- Velocity helpers ------------------------------------------------------

def test_manning_velocity():
    assert r.manning_velocity(0.013, 0.62132, 0.005) == pytest.approx(5.885328132746334)


def test_discharge_to_velocity():
    assert r.discharge_to_velocity(17.656, 3.0) == pytest.approx(17.656 / 3.0)


def test_discharge_to_velocity_zero_area():
    with pytest.raises(ValueError):
        r.discharge_to_velocity(10.0, 0.0)


# --- Routing ---------------------------------------------------------------

def test_linear_reservoir_routing_value():
    assert r.simple_linear_reservoir_routing(10.0, 0.0, 1.0, 1.0) == pytest.approx(
        6.321205588285577
    )


def test_linear_reservoir_routing_steady_state():
    # inflow == prev outflow -> output unchanged (steady state preserved)
    assert r.simple_linear_reservoir_routing(5.0, 5.0, 2.0, 0.5) == pytest.approx(5.0)


def test_linear_reservoir_routing_validation():
    with pytest.raises(ValueError):
        r.simple_linear_reservoir_routing(10.0, 0.0, 0.0, 1.0)  # K must be > 0


# --- HGL / EGL steps -------------------------------------------------------

def test_manning_friction_head_loss():
    assert r.manning_friction_head_loss(17.656, 0.013, 3.0, 0.62132, 100.0) == pytest.approx(
        0.500000883653244
    )


def test_energy_grade_line_step_equals_hf_when_velocity_head_constant():
    hf = r.manning_friction_head_loss(17.656, 0.013, 3.0, 0.62132, 100.0)
    egl = r.energy_grade_line_step(17.656, 0.013, 3.0, 0.62132, 100.0, 0.0, 0.0)
    assert egl == pytest.approx(hf)


def test_energy_grade_line_step_adds_velocity_head_delta():
    egl = r.energy_grade_line_step(17.656, 0.013, 3.0, 0.62132, 100.0, 0.7, 0.2)
    hf = r.manning_friction_head_loss(17.656, 0.013, 3.0, 0.62132, 100.0)
    assert egl == pytest.approx(hf + 0.5)


# --- Depth solvers ---------------------------------------------------------

def test_critical_depth_circular():
    # Q^2/g = A^3/T with the correct circular-segment area (D^2/8)(theta - sin theta)
    assert r.critical_depth_circular(10.0, 2.0) == pytest.approx(1.131, abs=1e-3)


def test_normal_depth_circular_inverts_capacity():
    # ~8.0 cfs is the half-full (y=D/2) discharge for this 2 ft pipe, so the
    # solver must recover y ~ 1.0 ft. (The pipe's true max capacity is ~17.2 cfs.)
    assert r.normal_depth_circular(2.0, 0.013, 0.005, 8.0) == pytest.approx(1.0, abs=1e-3)


def test_normal_depth_circular_raises_over_capacity():
    # 25.393 cfs far exceeds the ~17.2 cfs max capacity of a 2 ft pipe at S=0.005
    with pytest.raises(ValueError):
        r.normal_depth_circular(2.0, 0.013, 0.005, 25.393)


def test_normal_depth_trapezoidal_inverts_flow():
    # inverse of manning_normal_flow_trapezoidal(2,1,1,...) == 17.656 -> y ~ 1.0
    yn = r.normal_depth_trapezoidal(2.0, 1.0, 0.013, 0.005, 17.656)
    assert yn == pytest.approx(1.0, abs=1e-3)
    # round-trips back through the forward flow function
    assert r.manning_normal_flow_trapezoidal(2.0, 1.0, yn, 0.013, 0.005) == pytest.approx(
        17.656, abs=1e-2
    )


def test_normal_depth_trapezoidal_raises_when_beyond_bound():
    # A discharge requiring depth > 100 ft is outside the searched range
    with pytest.raises(ValueError):
        r.normal_depth_trapezoidal(2.0, 1.0, 0.013, 0.005, 1.0e9)


# --- Network profile -------------------------------------------------------

def test_steady_network_hgl_profile_single_reach():
    reaches = [
        {"length_ft": 100.0, "n": 0.013, "area_ft2": 3.0, "hyd_radius_ft": 0.62132, "q_cfs": 17.656}
    ]
    prof = r.steady_network_hgl_profile(reaches, start_hgl_ft=10.0)
    assert len(prof) == 1
    last = prof[-1]
    assert last["hf_ft"] == pytest.approx(0.5, abs=1e-3)
    assert last["hgl_ft"] == pytest.approx(9.5, abs=1e-3)
    assert last["reach_idx"] == 0
    assert last["cum_length_ft"] == pytest.approx(100.0)


def test_steady_network_hgl_profile_empty():
    assert r.steady_network_hgl_profile([]) == []


def test_steady_network_hgl_profile_accepts_short_key_aliases():
    # the function accepts L/A/R/Q aliases in addition to the long keys
    reaches = [{"L": 100.0, "n": 0.013, "A": 3.0, "R": 0.62132, "Q": 17.656}]
    prof = r.steady_network_hgl_profile(reaches, start_hgl_ft=10.0)
    assert prof[-1]["hf_ft"] == pytest.approx(0.5, abs=1e-3)


def test_steady_network_hgl_profile_multi_reach_accumulates():
    reach = {"n": 0.013, "area_ft2": 3.0, "hyd_radius_ft": 0.62132, "q_cfs": 17.656}
    reaches = [
        {**reach, "length_ft": 100.0},
        {**reach, "length_ft": 50.0},
        {**reach, "length_ft": 200.0},
    ]
    prof = r.steady_network_hgl_profile(reaches, start_hgl_ft=10.0)
    assert [p["reach_idx"] for p in prof] == [0, 1, 2]
    assert [p["cum_length_ft"] for p in prof] == [100.0, 150.0, 350.0]
    # hf scales with reach length (same section/flow)
    assert prof[0]["hf_ft"] == pytest.approx(0.5, abs=1e-3)
    assert prof[1]["hf_ft"] == pytest.approx(0.25, abs=1e-3)
    assert prof[2]["hf_ft"] == pytest.approx(1.0, abs=1e-3)
    # HGL drops monotonically by the cumulative friction loss
    assert prof[-1]["hgl_ft"] == pytest.approx(10.0 - (0.5 + 0.25 + 1.0), abs=1e-3)


# --- Validation guards (parametrized) --------------------------------------

@pytest.mark.parametrize(
    "func, args",
    [
        (r.manning_normal_flow_trapezoidal, (2.0, 1.0, 0.0, 0.013, 0.005)),   # depth must be > 0
        (r.manning_normal_flow_trapezoidal, (2.0, 1.0, 1.0, 0.0, 0.005)),     # n must be > 0
        (r.manning_friction_head_loss, (10.0, 0.0, 2.0, 0.5, 100.0)),         # n must be > 0
        (r.manning_friction_head_loss, (10.0, 0.013, 0.0, 0.5, 100.0)),       # area must be > 0
        (r.manning_friction_head_loss, (10.0, 0.013, 2.0, 0.5, 0.0)),         # length must be > 0
        (r.critical_depth_circular, (10.0, 0.0)),                            # diameter must be > 0
        (r.energy_grade_line_step, (10.0, 0.0, 2.0, 0.5, 100.0)),            # n must be > 0
        (r.normal_depth_circular, (0.0, 0.013, 0.005, 8.0)),                # diameter must be > 0
        (r.normal_depth_trapezoidal, (2.0, 1.0, 0.0, 0.005, 10.0)),         # n must be > 0
        (r.manning_velocity, (0.0, 0.5, 0.005)),                            # n must be > 0
        (r.manning_velocity, (0.013, 0.0, 0.005)),                          # R must be > 0
        (r.simple_linear_reservoir_routing, (10.0, 0.0, 0.0, 1.0)),         # K must be > 0
        (r.simple_linear_reservoir_routing, (10.0, 0.0, 1.0, 0.0)),         # dt must be > 0
        (r.simple_linear_reservoir_routing, (-1.0, 0.0, 1.0, 1.0)),         # flow must be >= 0
        (r.manning_full_flow_circular, (2.0, 0.013, -0.001)),               # slope must be >= 0
    ],
)
def test_validation_guards_raise(func, args):
    with pytest.raises(ValueError):
        func(*args)


# --- Property / round-trip -------------------------------------------------

@pytest.mark.parametrize("depth", [0.4, 0.7, 1.0, 1.3, 1.6])
def test_normal_depth_circular_round_trips(depth):
    # forward: discharge at a known depth; inverse: recover that depth
    d, n, s = 2.0, 0.013, 0.005
    a, _, p = r._circular_geometry(depth, d)
    q = (1.486 / n) * a * ((a / p) ** (2.0 / 3.0)) * (s ** 0.5)
    assert r.normal_depth_circular(d, n, s, q) == pytest.approx(depth, abs=2e-3)


@pytest.mark.parametrize("depth", [0.25, 0.5, 1.0, 2.0, 4.0])
def test_normal_depth_trapezoidal_round_trips(depth):
    b, z, n, s = 4.0, 2.0, 0.013, 0.005
    q = r.manning_normal_flow_trapezoidal(b, z, depth, n, s)
    assert r.normal_depth_trapezoidal(b, z, n, s, q) == pytest.approx(depth, abs=2e-3)


def test_critical_depth_below_diameter():
    # critical depth is physically bounded by the pipe diameter
    for q in (2.0, 5.0, 10.0, 15.0):
        yc = r.critical_depth_circular(q, 2.0)
        assert 0.0 < yc < 2.0
