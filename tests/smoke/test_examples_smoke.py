import csv
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_custom_policy_example_writes_csv(tmp_path):
    output = tmp_path / "example.csv"
    completed = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "examples" / "run_custom_policy.py"),
            "--country",
            "KEN",
            "--start-year",
            "2023",
            "--years",
            "2",
            "--output",
            str(output),
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.exists()
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [int(row["year"]) for row in rows] == [2024, 2025]


def test_policy_comparison_example_runs():
    completed = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "examples" / "compare_policies.py"),
            "--country",
            "KEN",
            "--start-year",
            "2023",
            "--years",
            "2",
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert "baseline" in completed.stdout
    assert "alternative" in completed.stdout
