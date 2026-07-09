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
