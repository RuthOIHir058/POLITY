# Examples

Run examples from the repository root after installing POLITY in an active virtual environment.

## Minimal programmatic simulation

```bash
python examples/basic_simulation.py
```

`basic_simulation.py` initializes Kenya at 2015, runs the public default policy for ten years, and prints final GDP per capita, inflation, conflict risk, and audit-entry count.

## Run a JSON policy and write CSV

```bash
python examples/run_custom_policy.py \
  --country KEN \
  --start-year 2015 \
  --years 20 \
  --policy configs/baseline_policy.json \
  --output results/custom_policy.csv
```

The policy file must contain valid `PolicyInputs` fields. The example writes one annual row per step.

## Compare two policy files

```bash
python examples/compare_policies.py \
  --country KEN \
  --start-year 2015 \
  --years 20 \
  --baseline configs/baseline_policy.json \
  --alternative configs/education_infrastructure_reform.json
```

Both paths start from the same immutable initial state. Output differences therefore arise from the supplied policies, not random noise.

All example results are model scenarios, not forecasts or policy recommendations.
