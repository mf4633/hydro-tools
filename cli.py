"""
Entry point for hydro-tools CLI.

Usage examples (future):
  python -m hydro_tools.cli analyze --model BC-local.inp --rp 25
  hydro-tools dbf-dump some.dbf

  python -m hydro_tools.cli hgl-step --q 17.656 --n 0.013 --a 3 --r 0.62132 --l 100
"""
import argparse
import sys

def main():
    from . import __version__
    parser = argparse.ArgumentParser(prog="hydro-tools")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd")

    # Placeholder for now — will be filled as we port real scripts
    p = sub.add_parser("hello", help="Sanity check")
    p.add_argument("name", nargs="?", default="world")

    p2 = sub.add_parser("dbf-dump", help="Dump first N records of a .dbf")
    p2.add_argument("dbf_path")
    p2.add_argument("-n", "--limit", type=int, default=5)

    p_rat = sub.add_parser("rational", help="Rational method peak flow Q = C*i*A (cfs)")
    p_rat.add_argument("--c", type=float, required=True, help="runoff coefficient (0-1)")
    p_rat.add_argument("--i", type=float, required=True, help="intensity in/hr")
    p_rat.add_argument("--a", type=float, required=True, help="area acres")

    p_scs = sub.add_parser("scs", help="SCS runoff depth (in) from rainfall + CN")
    p_scs.add_argument("--rain", type=float, default=3.0, help="rainfall in (default 3.0)")
    p_scs.add_argument("--cn", type=float, default=75, help="curve number (default 75)")

    p_man = sub.add_parser("manning", help="Manning full-flow circular pipe capacity (cfs)")
    p_man.add_argument("--d", type=float, required=True, help="diameter ft")
    p_man.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
    p_man.add_argument("--s", type=float, required=True, help="slope ft/ft")

    p_trap = sub.add_parser("manning-trap", aliases=["trapezoidal"], help="Manning normal flow, trapezoidal channel (cfs)")
    p_trap.add_argument("--b", type=float, required=True, help="bottom width ft")
    p_trap.add_argument("--z", type=float, required=True, help="side slope z:1 (H:V; 0=rect)")
    p_trap.add_argument("--y", type=float, required=True, help="flow depth ft")
    p_trap.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
    p_trap.add_argument("--s", type=float, required=True, help="slope ft/ft")

    p_route = sub.add_parser("routing", aliases=["linear-reservoir"], help="simple linear reservoir routing step (cfs)")
    p_route.add_argument("--i", type=float, required=True, help="inflow cfs for timestep")
    p_route.add_argument("--qp", type=float, required=True, help="prev outflow cfs")
    p_route.add_argument("--k", type=float, required=True, help="K storage coeff (hr)")
    p_route.add_argument("--dt", type=float, required=True, help="dt (hr)")

    p_hgl = sub.add_parser("hgl-loss", aliases=["hgl-step", "friction-head-loss"], help="Manning friction head loss / HGL step (ft)")
    p_hgl.add_argument("--q", type=float, required=True, help="Q cfs")
    p_hgl.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
    p_hgl.add_argument("--a", type=float, required=True, help="area ft2")
    p_hgl.add_argument("--r", type=float, required=True, help="hyd radius R ft")
    p_hgl.add_argument("--l", type=float, required=True, help="length ft")

    p_egl = sub.add_parser("egl-step", aliases=["energy-grade-line"], help="energy grade line step: friction loss + change in velocity head (ft)")
    p_egl.add_argument("--q", type=float, required=True, help="Q cfs")
    p_egl.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
    p_egl.add_argument("--a", type=float, required=True, help="area ft2")
    p_egl.add_argument("--r", type=float, required=True, help="hyd radius R ft")
    p_egl.add_argument("--l", type=float, required=True, help="length ft")
    p_egl.add_argument("--vhup", type=float, default=0.0, help="vel head up ft (default 0)")
    p_egl.add_argument("--vhdown", type=float, default=0.0, help="vel head down ft (default 0)")

    p_crit = sub.add_parser("critical-depth", aliases=["yc-circular"], help="critical depth of a circular pipe (ft)")
    p_crit.add_argument("--q", type=float, required=True, help="Q cfs")
    p_crit.add_argument("--d", type=float, required=True, help="diameter ft")

    p_norm = sub.add_parser("normal-depth", aliases=["normal-depth-circular"], help="normal depth of a circular pipe (ft)")
    p_norm.add_argument("--d", type=float, required=True, help="diameter ft")
    p_norm.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
    p_norm.add_argument("--s", type=float, required=True, help="slope ft/ft")
    p_norm.add_argument("--q", type=float, required=True, help="Q cfs")

    p_ntrap = sub.add_parser("normal-depth-trap", aliases=["normal-depth-trapezoidal"], help="normal depth of a trapezoidal channel (ft)")
    p_ntrap.add_argument("--b", type=float, required=True, help="bottom width ft")
    p_ntrap.add_argument("--z", type=float, required=True, help="side slope z:1")
    p_ntrap.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
    p_ntrap.add_argument("--s", type=float, required=True, help="slope ft/ft")
    p_ntrap.add_argument("--q", type=float, required=True, help="Q cfs")

    p_vel = sub.add_parser("velocity", aliases=["manning-velocity"], help="Manning mean velocity from n, R, S (ft/s)")
    p_vel.add_argument("--n", type=float, required=True, help="Manning n")
    p_vel.add_argument("--r", type=float, required=True, help="hyd radius R ft")
    p_vel.add_argument("--s", type=float, required=True, help="slope ft/ft")

    sub.add_parser("network-hgl-profile", aliases=["hgl-profile"], help="steady multi-reach network HGL profile (demo)")
    sub.add_parser("stormsewer", help="stub (not yet implemented)")
    sub.add_parser("analyze-connectivity", help="network connectivity port stub")
    sub.add_parser("consumption", aliases=["verif-0.2"], help="print all primitives with reference values")

    args = parser.parse_args()

    if args.cmd == "hello":
        print(f"Hello, {args.name} from hydro-tools!")
    elif args.cmd == "dbf-dump":
        from .dbf import read_dbf
        for i, row in enumerate(read_dbf(args.dbf_path)):
            if i >= args.limit:
                break
            print(row)
    elif args.cmd == "rational":
        from .rational import rational_peak
        print(rational_peak(args.c, args.i, args.a))
    elif args.cmd == "stormsewer":
        print("stormsewer subcommand is a stub — not yet implemented.")
    elif args.cmd == "scs":
        from .rational import scs_runoff_depth
        print("SCS runoff depth (in):", scs_runoff_depth(args.rain, args.cn))
    elif args.cmd == "manning":
        # Manning full flow (circular pipe capacity).
        from .rational import manning_full_flow_circular
        q = manning_full_flow_circular(args.d, args.n, args.s)
        print(f"Manning full flow Q={q:.3f} cfs (D={args.d}, n={args.n}, S={args.s})")
    elif args.cmd in ("manning-trap", "trapezoidal"):
        # Manning normal flow for a trapezoidal channel.
        from .rational import manning_normal_flow_trapezoidal
        q = manning_normal_flow_trapezoidal(args.b, args.z, args.y, args.n, args.s)
        print(f"Manning trap/rect normal Q={q:.3f} cfs (b={args.b}, z={args.z}, y={args.y}, n={args.n}, S={args.s})")
    elif args.cmd in ("routing", "linear-reservoir"):
        # Simple linear reservoir routing step.
        from .rational import simple_linear_reservoir_routing
        q = simple_linear_reservoir_routing(args.i, args.qp, args.k, args.dt)
        print(f"Linear reservoir Qout={q:.3f} cfs (I={args.i}, Qp={args.qp}, K={args.k}, dt={args.dt})")
    elif args.cmd in ("hgl-loss", "friction-head-loss", "hgl-step"):
        # Manning friction head loss (HGL step).
        from .rational import manning_friction_head_loss
        hf = manning_friction_head_loss(args.q, args.n, args.a, args.r, args.l)
        print(f"Manning friction head loss hf={hf:.3f} ft (Q={args.q}, n={args.n}, A={args.a}, R={args.r}, L={args.l})")
    elif args.cmd in ("critical-depth", "yc-circular"):
        from .rational import critical_depth_circular
        yc = critical_depth_circular(args.q, args.d)
        print(f"Critical depth yc={yc:.3f} ft (Q={args.q}, D={args.d})")
    elif args.cmd in ("egl-step", "energy-grade-line"):
        from .rational import energy_grade_line_step
        de = energy_grade_line_step(args.q, args.n, args.a, args.r, args.l, args.vhup, args.vhdown)
        print(f"EGL step delta={de:.3f} ft (Q={args.q}, n={args.n}, A={args.a}, R={args.r}, L={args.l}, Vh_up={args.vhup}, Vh_down={args.vhdown})")
    elif args.cmd in ("normal-depth", "normal-depth-circular"):
        from .rational import normal_depth_circular
        yn = normal_depth_circular(args.d, args.n, args.s, args.q)
        print(f"Normal depth yn={yn:.3f} ft (D={args.d}, n={args.n}, S={args.s}, Q={args.q})")
    elif args.cmd == "analyze-connectivity":
        print("analyze-connectivity subcommand is a stub — not yet implemented.")
    elif args.cmd in ("normal-depth-trap", "normal-depth-trapezoidal"):
        from .rational import normal_depth_trapezoidal
        yn = normal_depth_trapezoidal(args.b, args.z, args.n, args.s, args.q)
        print(f"Normal depth trap yn={yn:.3f} ft (b={args.b}, z={args.z}, n={args.n}, S={args.s}, Q={args.q})")
    elif args.cmd in ("network-hgl-profile", "hgl-profile"):
        # Steady network HGL profile (multi-reach demo using friction + EGL step fns).
        from .rational import steady_network_hgl_profile
        reaches = [{'length_ft':100.0, 'n':0.013, 'area_ft2':3.0, 'hyd_radius_ft':0.62132, 'q_cfs':17.656}]
        prof = steady_network_hgl_profile(reaches, start_hgl_ft=10.0)
        last = prof[-1] if prof else {}
        print(f"Network HGL profile demo: last hgl={last.get('hgl_ft',0):.3f} ft hf={last.get('hf_ft',0):.3f}")
    elif args.cmd in ("velocity", "manning-velocity"):
        from .rational import manning_velocity, discharge_to_velocity, manning_normal_flow_trapezoidal
        v = manning_velocity(args.n, args.r, args.s)
        qex = manning_normal_flow_trapezoidal(2.0, 1.0, 1.0, args.n, args.s) if args.n > 0 else 0
        va = discharge_to_velocity(qex, 3.0) if qex > 0 else 0
        print(f"Manning velocity V={v:.3f} ft/s (n={args.n}, R={args.r}, S={args.s}) [+ Q/A ex V={va:.3f}]")
    elif args.cmd in ("consumption", "verif-0.2"):
        from .rational import (
            manning_normal_flow_trapezoidal,
            manning_friction_head_loss,
            manning_full_flow_circular,
            simple_linear_reservoir_routing,
            critical_depth_circular,
            energy_grade_line_step,
            normal_depth_circular,
            normal_depth_trapezoidal,
            manning_velocity,
            discharge_to_velocity,
            steady_network_hgl_profile,
        )
        print('trap', manning_normal_flow_trapezoidal(2,1,1,0.013,0.005))
        print('hgl', manning_friction_head_loss(17.656,0.013,3,0.62132,100))
        print('full', manning_full_flow_circular(2.0, 0.013, 0.005))
        print('routing', simple_linear_reservoir_routing(10.0, 0.0, 1.0, 1.0))
        print('crit', critical_depth_circular(10.0, 2.0))
        print('egl', energy_grade_line_step(17.656, 0.013, 3.0, 0.62132, 100.0))
        print('normal_circ', normal_depth_circular(2.0, 0.013, 0.005, 8.0))
        print('normal_trap', normal_depth_trapezoidal(2.0, 1.0, 0.013, 0.005, 17.656))
        print('vel_manning', manning_velocity(0.013, 0.62132, 0.005))
        print('vel_discharge', discharge_to_velocity(17.656, 3.0))
        reaches = [{'length_ft':100.0, 'n':0.013, 'area_ft2':3.0, 'hyd_radius_ft':0.62132, 'q_cfs':17.656}]
        prof = steady_network_hgl_profile(reaches, start_hgl_ft=10.0)
        print('profile_last_hgl', prof[-1]['hgl_ft'] if prof else None)
        print('profile_last_hf', prof[-1]['hf_ft'] if prof else None)
    else:
        parser.print_help()
        sys.exit(1)


# Usage example: python -m hydro_tools.cli hgl-step --q 17.656 --n 0.013 --a 3 --r 0.62132 --l 100

if __name__ == "__main__":
    main()


