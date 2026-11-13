from pathlib import Path

from bench import environment


def test_binary_defaults_to_the_build_script_location():
    binary = environment.qucs_binary({})
    assert binary == environment.DEFAULT_BUILD_DIR / "qucs" / "qucs-s"


def test_binary_follows_build_dir_then_explicit_path():
    assert environment.qucs_binary({"QUCS_S_BUILD": "/b"}) == Path("/b/qucs/qucs-s")
    both = {"QUCS_S_BUILD": "/b", "QUCS_S_BIN": "/x/qucs-s"}
    assert environment.qucs_binary(both) == Path("/x/qucs-s")


def test_bench_cpu_reads_the_environment():
    assert environment.bench_cpu({}) == 0
    assert environment.bench_cpu({"BENCH_CPU": "2"}) == 2


def test_isolated_env_redirects_settings_and_goes_offscreen(tmp_path):
    env = environment.isolated_env(tmp_path, base={"PATH": "/usr/bin", "HOME": "/home/me"})
    assert env["HOME"] == str(tmp_path)
    assert env["XDG_CONFIG_HOME"] == str(tmp_path / ".config")
    assert env["QT_QPA_PLATFORM"] == "offscreen"
    assert env["PATH"] == "/usr/bin"


def test_isolated_env_does_not_modify_its_input(tmp_path):
    base = {"HOME": "/home/me"}
    environment.isolated_env(tmp_path, base=base)
    assert base == {"HOME": "/home/me"}


def test_bench_command_pins_and_keeps_the_file_in_one_argument(tmp_path):
    schematic = tmp_path / "grid 1000.sch"
    command = environment.bench_command(Path("/b/qucs-s"), schematic, 20, cpu=2)
    assert command[:3] == ["taskset", "-c", "2"]
    assert command[3] == "/b/qucs-s"
    assert command[4] == f"--perf-bench={schematic.resolve()}"
    assert command[5] == "--perf-bench-repeat=20"
    assert len(command) == 6


def test_bench_command_without_pinning(tmp_path):
    command = environment.bench_command(Path("/b/qucs-s"), tmp_path / "a.sch", 5, cpu=None)
    assert command[0] == "/b/qucs-s"


def test_machine_info_has_the_fields_results_rely_on():
    info = environment.machine_info()
    for key in ("cpu_model", "pinned_cpu", "governor", "max_freq_mhz",
                "turbo_disabled", "kernel", "python", "repo_revision"):
        assert key in info
    assert info["pinned_cpu"] == 0
