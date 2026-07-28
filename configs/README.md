# Policy configurations

A policy JSON object maps directly to `engine.core.policy_inputs.PolicyInputs`.

- `tax_rate`: target theoretical tax revenue as a GDP ratio.
- `total_expenditure_gdp`: total expenditure as a GDP ratio.
- `health_share`, `education_share`, `infrastructure_share`, `social_transfers_share`, `admin_share`, and `military_share`: shares of total expenditure. They must sum to 1.0.
- `inflation_target`: target inflation ratio.
- `trade_policy`: structural trade setting from -1.0 to 1.0.

Values are decimals. `0.20` means 20%.

Included files:

- `baseline_policy.json`: neutral publication example used by the CLI and verification tools.
- `education_infrastructure_reform.json`: illustrative reallocation toward education and infrastructure.

These files are examples, not historical policy reconstructions or recommendations.
