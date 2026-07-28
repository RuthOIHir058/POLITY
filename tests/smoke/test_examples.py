import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run(module_name: str):
    return subprocess.run(
        [sys.executable, "-m", module_name],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_basic_example_runs():
    completed = _run("examples.basic_simulation")
    assert completed.returncode == 0, completed.stderr
    assert "End year: 2025" in completed.stdout
    assert "Audit entries" in completed.stdout

