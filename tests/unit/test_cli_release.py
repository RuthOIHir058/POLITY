import csv

import pytest

from engine.cli import load_policy_file, main


def test_cli_main_prints_audit_and_writes_csv(tmp_path, capsys):
    output = tmp_path / "annual.csv"
    status = main(
        [
            "KEN",
            "--start-year",
            "2023",
            "--years",
            "1",
            "--audit",
            "--output",
            str(output),
        ]
    )
    assert status == 0
    captured = capsys.readouterr().out
    assert "POLITY V1 | KEN" in captured
    assert "CSV output:" in captured
    assert output.is_file()
    with output.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert rows[0]["year"] == "2024"
    assert rows[0]["hdi"]


def test_policy_file_reports_read_json_and_shape_errors(tmp_path):
    with pytest.raises(ValueError, match="Cannot read policy file"):
        load_policy_file(tmp_path / "missing.json")

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_policy_file(invalid)

    array = tmp_path / "array.json"
    array.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="one JSON object"):
        load_policy_file(array)


def test_cli_rejects_negative_years():
    with pytest.raises(SystemExit) as exc:
        main(["KEN", "--years", "-1"])
    assert exc.value.code == 2


def test_cli_version_reports_release(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == "POLITY Engine 1.0.0"
