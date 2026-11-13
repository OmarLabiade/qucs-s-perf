"""Everything a measurement needs to know about where it runs.

Timings are only comparable when they come from the same binary, on the
same CPU, with the same frequency settings. This module builds the command
line and environment used for every run, and records the machine state so
that each result file says under which conditions it was produced.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BUILD_DIR = REPO_ROOT / ".cache" / "build-relwithdebinfo"
DEFAULT_CPU = 0


def qucs_binary(environ: dict[str, str] | None = None) -> Path:
    """Path of the instrumented qucs-s binary.

    `QUCS_S_BIN` wins, then `QUCS_S_BUILD`, then the default build directory
    used by scripts/build_qucs.sh.
    """
    environ = os.environ if environ is None else environ
    if "QUCS_S_BIN" in environ:
        return Path(environ["QUCS_S_BIN"])
    build_dir = Path(environ.get("QUCS_S_BUILD", DEFAULT_BUILD_DIR))
    return build_dir / "qucs" / "qucs-s"


def bench_cpu(environ: dict[str, str] | None = None) -> int:
    """CPU the benchmark process is pinned to (`BENCH_CPU`, default 0)."""
    environ = os.environ if environ is None else environ
    return int(environ.get("BENCH_CPU", DEFAULT_CPU))


def isolated_env(home: Path, base: dict[str, str] | None = None) -> dict[str, str]:
    """Environment for a benchmark process.

    A private HOME keeps the user's Qucs-S settings out of the measurement
    (and keeps the measurement from rewriting them). The offscreen platform
    renders with the same raster engine as a desktop session, without a
    window system in the loop.
    """
    env = dict(os.environ if base is None else base)
    env["HOME"] = str(home)
    env["XDG_CONFIG_HOME"] = str(home / ".config")
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["LC_ALL"] = "C"
    return env


def bench_command(binary: Path, schematic: Path, samples: int,
                  cpu: int | None = DEFAULT_CPU) -> list[str]:
    """Command line for one run of the timing hooks.

    `--perf-bench=FILE` is passed as a single argument on purpose: Qucs-S
    opens every argument that does not start with a dash as a document.
    Pass `cpu=None` to leave the process unpinned.
    """
    command = [str(binary), f"--perf-bench={Path(schematic).resolve()}",
               f"--perf-bench-repeat={samples}"]
    if cpu is not None:
        command = ["taskset", "-c", str(cpu), *command]
    return command


def _read(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _cpu_model() -> str | None:
    cpuinfo = _read("/proc/cpuinfo") or ""
    for line in cpuinfo.splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip()
    return None


def _git_revision(directory: Path) -> str | None:
    if shutil.which("git") is None or not directory.exists():
        return None
    result = subprocess.run(["git", "-C", str(directory), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def machine_info(cpu: int = DEFAULT_CPU, qucs_source: Path | None = None) -> dict:
    """State of the machine that affects timings.

    Missing files (other kernels, containers, CI runners) give `None`
    rather than an error: a result recorded with unknown conditions is
    still better than no result, as long as it says so.
    """
    cpufreq = f"/sys/devices/system/cpu/cpu{cpu}/cpufreq"
    max_khz = _read(f"{cpufreq}/scaling_max_freq")
    no_turbo = _read("/sys/devices/system/cpu/intel_pstate/no_turbo")
    return {
        "cpu_model": _cpu_model(),
        "pinned_cpu": cpu,
        "performance_cores": _read("/sys/devices/cpu_core/cpus"),
        "efficiency_cores": _read("/sys/devices/cpu_atom/cpus"),
        "governor": _read(f"{cpufreq}/scaling_governor"),
        "max_freq_mhz": int(max_khz) // 1000 if max_khz else None,
        "turbo_disabled": None if no_turbo is None else no_turbo == "1",
        "on_ac_power": _on_ac_power(),
        "kernel": platform.release(),
        "os": _os_name(),
        "python": platform.python_version(),
        "repo_revision": _git_revision(REPO_ROOT),
        "qucs_revision": _git_revision(qucs_source) if qucs_source else None,
    }


def _on_ac_power() -> bool | None:
    supplies = Path("/sys/class/power_supply")
    if not supplies.exists():
        return None
    for supply in supplies.iterdir():
        if _read(str(supply / "type")) == "Mains":
            return _read(str(supply / "online")) == "1"
    return None


def _os_name() -> str | None:
    release = _read("/etc/os-release") or ""
    for line in release.splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.split("=", 1)[1].strip('"')
    return None


def main() -> int:
    source = os.environ.get("QUCS_S_SRC")
    info = machine_info(bench_cpu(), Path(source) if source else None)
    info["qucs_binary"] = str(qucs_binary())
    json.dump(info, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
