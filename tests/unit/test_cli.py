import json

import pytest

from engine.cli import DEFAULT_POLICY, build_parser, load_policy_file, policy_from_args


def test_policy_file_merges_with_public_defaults(tmp_path):
    path = tmp_path / "policy.json"
    path.write_text(json.dumps({"trade_policy": 0.5, "tax_rate": 0.33}))
    policy = load_policy_file(path)
    assert policy.trade_policy == pytest.approx(0.5)
    assert policy.tax_rate == pytest.approx(0.33)
    assert policy.education_share == DEFAULT_POLICY.education_share


def test_policy_file_rejects_unknown_and_non_numeric_values(tmp_path):
    unknown = tmp_path / "unknown.json"
    unknown.write_text('{"secret_switch": 1}')
    with pytest.raises(ValueError, match="Unknown policy fields"):
        load_policy_file(unknown)

    non_numeric = tmp_path / "text.json"
    non_numeric.write_text('{"tax_rate": "high"}')
    with pytest.raises(ValueError, match="must be numeric"):
        load_policy_file(non_numeric)


def test_cli_overrides_win_over_policy_file(tmp_path):
    path = tmp_path / "policy.json"
    path.write_text('{"tax_rate": 0.30}')
    args = build_parser().parse_args(
        ["KEN", "--policy-file", str(path), "--tax-rate", "0.35"]
    )
    policy = policy_from_args(args)
    assert policy.tax_rate == pytest.approx(0.35)


def test_default_cli_policy_is_stable():
    args = build_parser().parse_args(["KEN"])
    assert policy_from_args(args) == DEFAULT_POLICY
