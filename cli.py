"""
Entry point for hydro-tools CLI.

Usage examples (future):
  python -m hydro_tools.cli analyze --model BC-local.inp --rp 25
  hydro-tools dbf-dump some.dbf

p3-friday-hydro-tools-final-04 usage example (one more 0.2 hgl-step subcmd + exact numeric test 17.656 trap -> 0.500 HGL):
  python -m hydro_tools.cli hgl-step --q 17.656 --n 0.013 --a 3 --r 0.62132 --l 100
  # -> Manning friction head loss hf=0.500 ft ... [0.2 ... hgl-step alias]
"""
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(prog="hydro-tools")
    parser.add_argument("--version", action="version", version="0.1.0")
    sub = parser.add_subparsers(dest="cmd")

    # Placeholder for now — will be filled as we port real scripts
    p = sub.add_parser("hello", help="Sanity check")
    p.add_argument("name", nargs="?", default="world")

    p2 = sub.add_parser("dbf-dump", help="Dump first N records of a .dbf")
    p2.add_argument("dbf_path")
    p2.add_argument("-n", "--limit", type=int, default=5)

    p_hgl = sub.add_parser("hgl-loss", help="0.2: Manning friction head loss (HGL step; hglStep0_2 ~0.500 ft from 17.656 trap ex)")
    p_hgl.add_argument("--q", type=float, required=True, help="Q cfs")
    p_hgl.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
    p_hgl.add_argument("--a", type=float, required=True, help="area ft2")
    p_hgl.add_argument("--r", type=float, required=True, help="hyd radius R ft")
    p_hgl.add_argument("--l", type=float, required=True, help="length ft")
    p_hglstep = sub.add_parser("hgl-step", help="0.2: HGL step (manning_friction_head_loss; exact 17.656 trap -> 0.500 HGL hglStep0_2)")
    p_hglstep.add_argument("--q", type=float, required=True, help="Q cfs")
    p_hglstep.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
    p_hglstep.add_argument("--a", type=float, required=True, help="area ft2")
    p_hglstep.add_argument("--r", type=float, required=True, help="hyd radius R ft")
    p_hglstep.add_argument("--l", type=float, required=True, help="length ft")
    p_egl = sub.add_parser("egl-step", help="0.2: full energy grade line step (EGL; friction + delta Vh; ~0.500 ft)")
    p_egl.add_argument("--q", type=float, required=True, help="Q cfs")
    p_egl.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
    p_egl.add_argument("--a", type=float, required=True, help="area ft2")
    p_egl.add_argument("--r", type=float, required=True, help="hyd radius R ft")
    p_egl.add_argument("--l", type=float, required=True, help="length ft")
    p_egl.add_argument("--vhup", type=float, default=0.0, help="vel head up ft (default 0)")
    p_egl.add_argument("--vhdown", type=float, default=0.0, help="vel head down ft (default 0)")
    p_crit = sub.add_parser("critical-depth", help="0.2: critical depth circular (yc; network/culvert; ~0.658 ft)")
    p_crit.add_argument("--q", type=float, required=True, help="Q cfs")
    p_crit.add_argument("--d", type=float, required=True, help="diameter ft")
    p_norm = sub.add_parser("normal-depth", help="0.2: normal depth circular (yn; ~1.000 ft test)")
    p_norm.add_argument("--d", type=float, required=True, help="diameter ft")
    p_norm.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
    p_norm.add_argument("--s", type=float, required=True, help="slope ft/ft")
    p_norm.add_argument("--q", type=float, required=True, help="Q cfs")
    p_hglprof = sub.add_parser("network-hgl-profile", help="0.2: steady network HGL profile (multi-reach; 0.500 hf match)")
    p_vel = sub.add_parser("velocity", help="0.2: manning_velocity + discharge ex (V from n,R,S)")

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
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument("--c", type=float, required=True)
        p.add_argument("--i", type=float, required=True, help="intensity in/hr")
        p.add_argument("--a", type=float, required=True, help="area acres")
        ns = p.parse_args(args[1:] if args else [])
        print(rational_peak(ns.c, ns.i, ns.a))
    elif args.cmd == "stormsewer":
        print("stormsewer bridge stub — build with `cargo build --target wasm32-unknown-unknown` in crates/stormsewer (inside OpenCADStudio) then use via WASM (shared engine for marketable apps + OpenCAD). See stormsewer WASM target added per review.")
    elif args.cmd == "scs":
        from .rational import scs_runoff_depth
        print("SCS runoff depth (in):", scs_runoff_depth(args.rain or 3.0, args.cn or 75))
    elif args.cmd == "manning":
        # 0.2 spike: open core Manning full flow primitive (circular pipe capacity).
        from .rational import manning_full_flow_circular
        import argparse as _a
        p = _a.ArgumentParser()
        p.add_argument("--d", type=float, required=True, help="diameter ft")
        p.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
        p.add_argument("--s", type=float, required=True, help="slope ft/ft")
        ns = p.parse_args(args[1:] if args else [])
        q = manning_full_flow_circular(ns.d, ns.n, ns.s)
        print(f"Manning full flow Q={q:.3f} cfs (D={ns.d}, n={ns.n}, S={ns.s})")
    elif args.cmd == "manning-trap" or args.cmd == "trapezoidal":
        # 0.2 additional spike: open core Manning normal flow for trapezoidal channel (complements circular; network hydraulics primitive).
        # Exact append style as manning cmd (read-first, no new files, cross-verif).
        from .rational import manning_normal_flow_trapezoidal
        import argparse as _a
        p = _a.ArgumentParser()
        p.add_argument("--b", type=float, required=True, help="bottom width ft")
        p.add_argument("--z", type=float, required=True, help="side slope z:1 (H:V; 0=rect)")
        p.add_argument("--y", type=float, required=True, help="flow depth ft")
        p.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
        p.add_argument("--s", type=float, required=True, help="slope ft/ft")
        ns = p.parse_args(args[1:] if args else [])
        q = manning_normal_flow_trapezoidal(ns.b, ns.z, ns.y, ns.n, ns.s)
        print(f"Manning trap/rect normal Q={q:.3f} cfs (b={ns.b}, z={ns.z}, y={ns.y}, n={ns.n}, S={ns.s}) [0.2 additional]")
    elif args.cmd == "routing" or args.cmd == "linear-reservoir":
        # 0.2 additional spike: open core simple linear reservoir routing step (basic network/channel hydrograph routing primitive; complements Manning capacity).
        # Builds on Manning 0.2 + trap. Exact append style as manning cmd (read-first, no new files, cross-verif).
        from .rational import simple_linear_reservoir_routing
        import argparse as _a
        p = _a.ArgumentParser()
        p.add_argument("--i", type=float, required=True, help="inflow cfs for timestep")
        p.add_argument("--qp", type=float, required=True, help="prev outflow cfs")
        p.add_argument("--k", type=float, required=True, help="K storage coeff (hr)")
        p.add_argument("--dt", type=float, required=True, help="dt (hr)")
        ns = p.parse_args(args[1:] if args else [])
        q = simple_linear_reservoir_routing(ns.i, ns.qp, ns.k, ns.dt)
        print(f"Linear reservoir Qout={q:.3f} cfs (I={ns.i}, Qp={ns.qp}, K={ns.k}, dt={ns.dt}) [0.2 additional routing]")
    elif args.cmd == "hgl-loss" or args.cmd == "friction-head-loss" or args.cmd == "hgl-step":
        # 0.2 additional spike: open core manning_friction_head_loss (basic HGL/energy step for network using inverted Manning; high-leverage for steady network HGL profiles).
        from .rational import manning_friction_head_loss
        import argparse as _a
        p = _a.ArgumentParser()
        p.add_argument("--q", type=float, required=True, help="Q cfs")
        p.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
        p.add_argument("--a", type=float, required=True, help="area ft2")
        p.add_argument("--r", type=float, required=True, help="hyd radius R ft")
        p.add_argument("--l", type=float, required=True, help="length ft")
        ns = p.parse_args(args[1:] if args else [])
        hf = manning_friction_head_loss(ns.q, ns.n, ns.a, ns.r, ns.l)
        print(f"Manning friction head loss hf={hf:.3f} ft (Q={ns.q}, n={ns.n}, A={ns.a}, R={ns.r}, L={ns.l}) [0.2 additional HGL/energy step for network; hgl-step alias]")
    elif args.cmd == "critical-depth" or args.cmd == "yc-circular":
        from .rational import critical_depth_circular
        import argparse as _a
        p = _a.ArgumentParser()
        p.add_argument("--q", type=float, required=True, help="Q cfs")
        p.add_argument("--d", type=float, required=True, help="diameter ft")
        ns = p.parse_args(args[1:] if args else [])
        yc = critical_depth_circular(ns.q, ns.d)
        print(f"Critical depth yc={yc:.3f} ft (Q={ns.q}, D={ns.d}) [0.2 additional critical_depth_circular for network/culvert]")
    elif args.cmd == "egl-step" or args.cmd == "energy-grade-line":
        from .rational import energy_grade_line_step
        import argparse as _a
        p = _a.ArgumentParser()
        p.add_argument("--q", type=float, required=True, help="Q cfs")
        p.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
        p.add_argument("--a", type=float, required=True, help="area ft2")
        p.add_argument("--r", type=float, required=True, help="hyd radius R ft")
        p.add_argument("--l", type=float, required=True, help="length ft")
        p.add_argument("--vhup", type=float, default=0.0, help="vel head up ft (default 0)")
        p.add_argument("--vhdown", type=float, default=0.0, help="vel head down ft (default 0)")
        ns = p.parse_args(args[1:] if args else [])
        de = energy_grade_line_step(ns.q, ns.n, ns.a, ns.r, ns.l, ns.vhup, ns.vhdown)
        print(f"EGL step delta={de:.3f} ft (Q={ns.q}, n={ns.n}, A={ns.a}, R={ns.r}, L={ns.l}, Vh_up={ns.vhup}, Vh_down={ns.vhdown}) [0.2 more energy_grade_line_step full EGL step for network; ~0.500 ft test; same in WASM/JS]")
    elif args.cmd == "normal-depth" or args.cmd == "normal-depth-circular":
        # 0.2 concrete additional primitive spike (Phase 3 / STRATEGY; complements the two general "more 0.2" spikes 019eb308-6b3c-7d61-b141-11bd97b22946 (cancelled) + 019eb30a-97de-7081-9de3-aaf6d5c8e55b (EGL completed); focus normal_depth_circular high-leverage next or culvert-related).
        from .rational import normal_depth_circular
        import argparse as _a
        p = _a.ArgumentParser()
        p.add_argument("--d", type=float, required=True, help="diameter ft")
        p.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
        p.add_argument("--s", type=float, required=True, help="slope ft/ft")
        p.add_argument("--q", type=float, required=True, help="Q cfs")
        ns = p.parse_args(args[1:] if args else [])
        yn = normal_depth_circular(ns.d, ns.n, ns.s, ns.q)
        print(f"Normal depth yn={yn:.3f} ft (D={ns.d}, n={ns.n}, S={ns.s}, Q={ns.q}) [0.2 additional normal_depth_circular; test ~1.000 for Q~25.393 at D=2; mirrors py/js/rust; no break priors]")
    elif args.cmd == "analyze-connectivity":
        # Demo: shows how an old root script pattern can move here
        print("analyze-connectivity stub — porting logic from analyze_network_connectivity.py next")
    elif args.cmd == "normal-depth-trap" or args.cmd == "normal-depth-trapezoidal":
        from .rational import normal_depth_trapezoidal
        import argparse as _a
        p = _a.ArgumentParser()
        p.add_argument("--b", type=float, required=True, help="bottom width ft")
        p.add_argument("--z", type=float, required=True, help="side slope z:1")
        p.add_argument("--n", type=float, required=True, help="Manning n (0.013 concrete)")
        p.add_argument("--s", type=float, required=True, help="slope ft/ft")
        p.add_argument("--q", type=float, required=True, help="Q cfs")
        ns = p.parse_args(args[1:] if args else [])
        yn = normal_depth_trapezoidal(ns.b, ns.z, ns.n, ns.s, ns.q)
        print(f"Normal depth trap yn={yn:.3f} ft (b={ns.b}, z={ns.z}, n={ns.n}, S={ns.s}, Q={ns.q}) [0.2 additional normal_depth_trapezoidal trap variant; ~1.000 test; mirrors py/js/rust; no break priors]")
    elif args.cmd == "network-hgl-profile" or args.cmd == "hgl-profile":
        # 0.2 additional (this task): steady_network_hgl_profile (multi-reach using existing friction+egl step fns for full steady profile). 2 new 0.2 delivered (profile + trap normal). Full phrases as above.
        from .rational import steady_network_hgl_profile
        reaches = [{'length_ft':100.0, 'n':0.013, 'area_ft2':3.0, 'hyd_radius_ft':0.62132, 'q_cfs':17.656}]
        prof = steady_network_hgl_profile(reaches, start_hgl_ft=10.0)
        last = prof[-1] if prof else {}
        print(f"Network HGL profile demo: last hgl={last.get('hgl_ft',0):.3f} ft hf={last.get('hf_ft',0):.3f} (0.500 match prior HGL hglStep0_2; 2 new 0.2; mirrors; no break)")
    elif args.cmd == "velocity" or args.cmd == "manning-velocity":
        from .rational import manning_velocity, discharge_to_velocity, manning_normal_flow_trapezoidal
        import argparse as _a
        p = _a.ArgumentParser()
        p.add_argument("--n", type=float, required=True, help="Manning n")
        p.add_argument("--r", type=float, required=True, help="hyd radius R ft")
        p.add_argument("--s", type=float, required=True, help="slope ft/ft")
        ns = p.parse_args(args[1:] if args else [])
        v = manning_velocity(ns.n, ns.r, ns.s)
        qex = manning_normal_flow_trapezoidal(2.0,1.0,1.0,ns.n,ns.s) if ns.n>0 else 0
        va = discharge_to_velocity(qex, 3.0) if qex>0 else 0
        print(f"Manning velocity V={v:.3f} ft/s (n={ns.n}, R={ns.r}, S={ns.s}) [0.2 velocity fn; ~5.88 from trap ex; mirrors py/js/rs; + Q/A ex V={va:.3f}]")
    elif args.cmd == "consumption" or args.cmd == "verif-0.2":
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
        print('=== p3-16-spawn-06 CONSUMPTION SCRIPT (cli enhanced; or python -c full) ===')
        print('trap', manning_normal_flow_trapezoidal(2,1,1,0.013,0.005))
        print('hgl', manning_friction_head_loss(17.656,0.013,3,0.62132,100))  # correct R from trap geo for exact 0.500 HGL hglStep0_2
        print('full', manning_full_flow_circular(2.0, 0.013, 0.005))
        print('routing', simple_linear_reservoir_routing(10.0, 0.0, 1.0, 1.0))
        print('crit', critical_depth_circular(10.0, 2.0))
        print('egl', energy_grade_line_step(17.656, 0.013, 3.0, 0.62132, 100.0))  # correct R
        print('normal_circ', normal_depth_circular(2.0, 0.013, 0.005, 25.393))
        print('normal_trap', normal_depth_trapezoidal(2.0, 1.0, 0.013, 0.005, 17.656))
        print('vel_manning', manning_velocity(0.013, 0.62132, 0.005))
        print('vel_discharge', discharge_to_velocity(17.656, 3.0))
        reaches = [{'length_ft':100.0, 'n':0.013, 'area_ft2':3.0, 'hyd_radius_ft':0.62132, 'q_cfs':17.656}]  # p3-friday-rational-05: ROBUST good positive dicts for steady_network_hgl_profile (positive L/n/A/R/Q >0; avoids prior ValueError in loss fns; R exact from trap geo for 0.500 hf hglStep0_2)
        prof = steady_network_hgl_profile(reaches, start_hgl_ft=10.0)
        print('profile_last_hgl', prof[-1]['hgl_ft'] if prof else None)
        print('profile_last_hf', prof[-1]['hf_ft'] if prof else None)
    else:
        parser.print_help()
        sys.exit(1)


# Subcmd added: hgl-step (one more 0.2 e.g. hgl-step; augments hgl-loss for the exact numeric test)
# Usage example: python -m hydro_tools.cli hgl-step --q 17.656 --n 0.013 --a 3 --r 0.62132 --l 100

if __name__ == "__main__":
    main()


