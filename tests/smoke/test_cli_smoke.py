import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_cli_runs_twenty_years():
    completed = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "main.py"),
            "KEN",
            "--start-year",
            "2023",
            "--years",
            "20",
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert "POLITY V1 | KEN" in completed.stdout
    assert "2043" in completed.stdout
