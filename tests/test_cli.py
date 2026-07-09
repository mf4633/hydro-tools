"""
Tests for the ``hydro_tools.cli`` entry point.

These guard the regressions that previously made the CLI unusable: the
UnboundLocalError from a shadowed ``argparse`` import, the ``args[1:]``
Namespace subscripting, and subcommands that were never registered.
"""
import pytest

from hydro_tools import cli


def run(monkeypatch, argv):
    monkeypatch.setattr("sys.argv", ["hydro-tools"] + argv)
    cli.main()


def test_hello(monkeypatch, capsys):
    run(monkeypatch, ["hello"])
    assert "Hello, world from hydro-tools!" in capsys.readouterr().out


def test_version(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["hydro-tools", "--version"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == "0.2.0"


def test_no_command_prints_help_and_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["hydro-tools"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    assert "usage:" in capsys.readouterr().out


def test_rational(monkeypatch, capsys):
    run(monkeypatch, ["rational", "--c", "0.5", "--i", "4", "--a", "2"])
    assert capsys.readouterr().out.strip() == "4.0"


def test_manning(monkeypatch, capsys):
    run(monkeypatch, ["manning", "--d", "2", "--n", "0.013", "--s", "0.005"])
    assert "Q=15.996 cfs" in capsys.readouterr().out


@pytest.mark.parametrize("name", ["manning-trap", "trapezoidal"])
def test_trapezoidal_and_alias(monkeypatch, capsys, name):
    run(monkeypatch, [name, "--b", "2", "--z", "1", "--y", "1", "--n", "0.013", "--s", "0.005"])
    assert "Q=17.656 cfs" in capsys.readouterr().out


@pytest.mark.parametrize("name", ["hgl-loss", "hgl-step", "friction-head-loss"])
def test_hgl_loss_and_aliases(monkeypatch, capsys, name):
    run(monkeypatch, [name, "--q", "17.656", "--n", "0.013", "--a", "3", "--r", "0.62132", "--l", "100"])
    assert "hf=0.500 ft" in capsys.readouterr().out


def test_critical_depth(monkeypatch, capsys):
    run(monkeypatch, ["critical-depth", "--q", "10", "--d", "2"])
    assert "yc=1.131 ft" in capsys.readouterr().out


def test_normal_depth(monkeypatch, capsys):
    run(monkeypatch, ["normal-depth", "--d", "2", "--n", "0.013", "--s", "0.005", "--q", "8.0"])
    assert "yn=1.000 ft" in capsys.readouterr().out


def test_velocity(monkeypatch, capsys):
    run(monkeypatch, ["velocity", "--n", "0.013", "--r", "0.62132", "--s", "0.005"])
    assert "V=5.885 ft/s" in capsys.readouterr().out


def test_network_hgl_profile(monkeypatch, capsys):
    run(monkeypatch, ["network-hgl-profile"])
    out = capsys.readouterr().out
    assert "hgl=9.500 ft" in out and "hf=0.500" in out


def test_scs(monkeypatch, capsys):
    run(monkeypatch, ["scs", "--rain", "3", "--cn", "75"])
    assert "0.960" in capsys.readouterr().out


def test_routing(monkeypatch, capsys):
    run(monkeypatch, ["routing", "--i", "10", "--qp", "0", "--k", "1", "--dt", "1"])
    assert "Qout=6.321 cfs" in capsys.readouterr().out


def test_egl_step(monkeypatch, capsys):
    run(monkeypatch, ["egl-step", "--q", "17.656", "--n", "0.013", "--a", "3", "--r", "0.62132", "--l", "100"])
    assert "delta=0.500 ft" in capsys.readouterr().out


def test_normal_depth_trap(monkeypatch, capsys):
    run(monkeypatch, ["normal-depth-trap", "--b", "2", "--z", "1", "--n", "0.013", "--s", "0.005", "--q", "17.656"])
    assert "yn=1.000 ft" in capsys.readouterr().out


def test_manning_full_flow(monkeypatch, capsys):
    run(monkeypatch, ["manning", "--d", "2", "--n", "0.013", "--s", "0.005"])
    assert "Q=15.996 cfs" in capsys.readouterr().out


def test_consumption(monkeypatch, capsys):
    run(monkeypatch, ["consumption"])
    out = capsys.readouterr().out
    # the cross-verify block prints each primitive with its corrected value
    assert "crit 1.131" in out
    assert "full 15.996" in out


def test_unknown_command_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["hydro-tools", "definitely-not-a-command"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code != 0


def test_dbf_dump_honors_limit(monkeypatch, capsys, tmp_path):
    # build a tiny DBF with 3 records and check --limit truncates output
    import struct

    def field(name, ftype, length):
        d = bytearray(32)
        d[0:len(name)] = name.encode("ascii")
        d[11] = ord(ftype)
        d[16] = length
        return bytes(d)

    fields = [("NAME", "C", 6)]
    header = bytearray(32)
    header[0] = 0x03
    struct.pack_into("<I", header, 4, 3)
    fdescs = b"".join(field(n, t, ln) for n, t, ln in fields)
    header_len = 32 + len(fdescs) + 1
    rec_len = 1 + 6
    struct.pack_into("<H", header, 8, header_len)
    struct.pack_into("<H", header, 10, rec_len)
    blob = bytes(header) + fdescs + b"\x0d"
    for nm in ("AAA", "BBB", "CCC"):
        blob += b"\x20" + nm.ljust(6).encode("ascii")
    path = tmp_path / "x.dbf"
    path.write_bytes(blob)

    run(monkeypatch, ["dbf-dump", str(path), "-n", "2"])
    out = capsys.readouterr().out
    assert out.count("NAME") == 2   # only 2 of the 3 records printed
