"""Deterministic 24-step POLITY V1 annual simulation orchestrator."""

from __future__ import annotations

from dataclasses import dataclass

from engine.core.audit_entry import AuditEntry
from engine.core.constants import classify_severity
from engine.core.country_state import CountryState
from engine.core.policy_inputs import PolicyInputs
from engine.core.step_result import StepResult
from engine.economy.fiscal import (
    DebtUpdate,
    FiscalFlows,
    RiskPremiumUpdate,
    compute_fiscal_flows,
    update_debt,
    update_risk_premium,
)
from engine.economy.macro import (
    GrowthBreakdown,
    InflationUpdate,
    OutputGap,
    UnemploymentUpdate,
    compute_gdp_growth,
    compute_output_gap,
    update_inflation,
    update_unemployment,
)
from engine.global_context.shocks import (
    ExternalShocks,
    normalize_external_shocks,
)
from engine.governance.capacity import (
    CapacityUpdate,
    CorruptionUpdate,
    update_corruption,
    update_state_capacity,
)
from engine.policy.stabilizers import (
    StabilizerResult,
    apply_automatic_stabilizers,
)
from engine.policy.validation import expenditure_breakdown, validate_policy
from engine.politics.stability import ConflictRiskUpdate, evaluate_conflict_risk
from engine.society.demographics import DemographicsUpdate, update_demographics
from engine.society.health import (
    LifeExpectancyUpdate,
    SchoolLifeExpectancy,
    compute_school_life_expectancy,
    update_life_expectancy,
)
from engine.society.human_capital import HumanCapitalUpdate, step_human_capital
from engine.society.inequality import GiniUpdate, update_gini
from engine.society.reference_metrics import (
    ReferenceMetrics,
    compute_reference_metrics,
)
from engine.society.urbanization import UrbanizationUpdate, update_urbanization
from engine.trade.openness import TradeUpdate, update_trade_openness


@dataclass(frozen=True)
class _Candidate:
    state: CountryState
    derived: dict[str, float]
    reference: dict[str, float]
    audit_log: list[AuditEntry]


def _entry(
    *,
    year: int,
    variable: str,
    value: float,
    previous: float,
    causes: list[tuple[str, float]],
    note: str,
) -> AuditEntry:
    delta = float(value) - float(previous)
    return AuditEntry(
        year=year,
        variable=variable,
        value=float(value),
        delta=delta,
        causes=[(str(label), float(magnitude)) for label, magnitude in causes],
        severity=classify_severity(variable, abs(delta)),
        note=note,
    )


def _build_audit_log(
    prior: CountryState,
    new_state: CountryState,
    policy: PolicyInputs,
    demographics: DemographicsUpdate,
    urbanization: UrbanizationUpdate,
    human_capital: HumanCapitalUpdate,
    growth: GrowthBreakdown,
    output_gap: OutputGap,
    inflation: InflationUpdate,
    unemployment: UnemploymentUpdate,
    fiscal: FiscalFlows,
    debt: DebtUpdate,
    risk: RiskPremiumUpdate,
    gini: GiniUpdate,
    life_expectancy: LifeExpectancyUpdate,
    conflict: ConflictRiskUpdate,
    capacity: CapacityUpdate,
    corruption: CorruptionUpdate,
    trade: TradeUpdate,
    school_life: SchoolLifeExpectancy,
    reference: ReferenceMetrics,
) -> list[AuditEntry]:
    year = prior.year
    prior_gdp_per_capita = prior.gdp / prior.population
    new_gdp_per_capita = new_state.gdp / new_state.population
    prior_output_gap = compute_output_gap(
        prior.previous_gdp_growth
        if prior.previous_gdp_growth is not None
        else prior.potential_growth,
        prior.potential_growth,
    ).value
    prior_school_life = compute_school_life_expectancy(
        prior.human_capital, fiscal.education_spend
    )
    prior_reference = compute_reference_metrics(
        prior_gdp_per_capita,
        prior.life_expectancy,
        prior.human_capital,
        prior_school_life.value,
    )

    gdp_pc_gdp_effect = (
        new_state.gdp - prior.gdp
    ) / new_state.population
    gdp_pc_population_effect = prior.gdp * (
        1.0 / new_state.population - 1.0 / prior.population
    )

    tax_capacity_adjustment = (
        fiscal.tax_revenue_gdp - policy.tax_rate
    )
    prior_tax_under_current_policy = policy.tax_rate * prior.fiscal_capacity
    prior_primary_under_current_policy = (
        prior_tax_under_current_policy - policy.total_expenditure_gdp
    )

    entries = [
        _entry(
            year=year,
            variable="youth_share",
            value=new_state.youth_share,
            previous=prior.youth_share,
            causes=demographics.youth_causes,
            note="Youth cohort share updated from longevity and education fertility effects.",
        ),
        _entry(
            year=year,
            variable="elderly_share",
            value=new_state.elderly_share,
            previous=prior.elderly_share,
            causes=demographics.elderly_causes,
            note="Elderly cohort share updated from life expectancy.",
        ),
        _entry(
            year=year,
            variable="working_age_share",
            value=new_state.working_age_share,
            previous=prior.working_age_share,
            causes=demographics.working_causes,
            note="Working-age share is the residual cohort share.",
        ),
        _entry(
            year=year,
            variable="population",
            value=new_state.population,
            previous=prior.population,
            causes=demographics.population_causes,
            note=f"Population changed {demographics.population_growth:.2%}.",
        ),
        _entry(
            year=year,
            variable="urban_pop_pct",
            value=new_state.urban_pop_pct,
            previous=prior.urban_pop_pct,
            causes=urbanization.causes,
            note="Urbanization follows the calibrated logistic migration curve.",
        ),
        _entry(
            year=year,
            variable="human_capital",
            value=new_state.human_capital,
            previous=prior.human_capital,
            causes=human_capital.causes,
            note=(
                "Human capital reflects the matured 15-year education investment "
                "and workforce depreciation."
            ),
        ),
        _entry(
            year=year,
            variable="gdp_growth",
            value=growth.gdp_growth,
            previous=(
                prior.previous_gdp_growth
                if prior.previous_gdp_growth is not None
                else prior.potential_growth
            ),
            causes=growth.causes,
            note=(
                f"GDP grew {growth.gdp_growth:.1%} versus potential "
                f"{prior.potential_growth:.1%}."
            ),
        ),
        _entry(
            year=year,
            variable="gdp",
            value=new_state.gdp,
            previous=prior.gdp,
            causes=[("real_gdp_growth", prior.gdp * growth.gdp_growth)],
            note="Absolute GDP updated from real annual growth.",
        ),
        _entry(
            year=year,
            variable="gdp_per_capita",
            value=new_gdp_per_capita,
            previous=prior_gdp_per_capita,
            causes=[
                ("gdp_level_change", gdp_pc_gdp_effect),
                ("population_denominator", gdp_pc_population_effect),
            ],
            note="GDP per capita combines the new GDP level and population.",
        ),
        _entry(
            year=year,
            variable="output_gap",
            value=output_gap.value,
            previous=prior_output_gap,
            causes=output_gap.causes,
            note="Output gap is growth deviation normalized by potential growth.",
        ),
        _entry(
            year=year,
            variable="inflation",
            value=new_state.inflation,
            previous=prior.inflation,
            causes=inflation.causes,
            note="Inflation updated by the hybrid NKPC.",
        ),
        _entry(
            year=year,
            variable="unemployment",
            value=new_state.unemployment,
            previous=prior.unemployment,
            causes=unemployment.causes,
            note="Unemployment updated by Okun's Law and the structural floor.",
        ),
        _entry(
            year=year,
            variable="tax_revenue_gdp",
            value=fiscal.tax_revenue_gdp,
            previous=prior_tax_under_current_policy,
            causes=[
                ("tax_rate_target", policy.tax_rate),
                ("fiscal_capacity_collection_gap", tax_capacity_adjustment),
            ],
            note="Actual tax collection is capped by prior-year fiscal capacity.",
        ),
        _entry(
            year=year,
            variable="primary_balance_gdp",
            value=fiscal.primary_balance_gdp,
            previous=prior_primary_under_current_policy,
            causes=[
                ("tax_revenue", fiscal.tax_revenue_gdp),
                ("total_expenditure", -fiscal.total_expenditure_gdp),
            ],
            note="Primary balance is tax revenue minus total expenditure.",
        ),
        _entry(
            year=year,
            variable="debt_gdp",
            value=new_state.debt_gdp,
            previous=prior.debt_gdp,
            causes=debt.causes,
            note="Debt follows the intertemporal budget constraint.",
        ),
        _entry(
            year=year,
            variable="risk_premium",
            value=new_state.risk_premium,
            previous=prior.risk_premium,
            causes=risk.causes,
            note="Sovereign risk combines persistence and nonlinear debt repricing.",
        ),
        _entry(
            year=year,
            variable="gini",
            value=new_state.gini,
            previous=prior.gini,
            causes=gini.causes,
            note="Inequality changed through persistent structural drivers.",
        ),
        _entry(
            year=year,
            variable="life_expectancy",
            value=new_state.life_expectancy,
            previous=prior.life_expectancy,
            causes=life_expectancy.causes,
            note="Life expectancy moves toward the Preston-curve target.",
        ),
        _entry(
            year=year,
            variable="conflict_risk",
            value=new_state.conflict_risk,
            previous=prior.conflict_risk,
            causes=list(conflict.components.items()),
            note=f"Conflict risk is {conflict.band} (logistic eta={conflict.eta:.3f}).",
        ),
        _entry(
            year=year,
            variable="political_stability_score",
            value=conflict.political_stability_score,
            previous=2.5 - 5.0 * prior.conflict_risk,
            causes=[
                (
                    "conflict_risk_mapping",
                    -5.0 * (new_state.conflict_risk - prior.conflict_risk),
                )
            ],
            note="Conflict risk mapped to the WGI-compatible stability scale.",
        ),
        _entry(
            year=year,
            variable="fiscal_capacity",
            value=new_state.fiscal_capacity,
            previous=prior.fiscal_capacity,
            causes=capacity.fiscal_causes,
            note=(
                "Fiscal capacity reflects admin investment, corruption, decay, "
                "and prior conflict conditions."
            ),
        ),
        _entry(
            year=year,
            variable="legal_capacity",
            value=new_state.legal_capacity,
            previous=prior.legal_capacity,
            causes=capacity.legal_causes,
            note=(
                "Legal capacity reflects slower investment and stronger conflict/"
                "corruption exposure."
            ),
        ),
        _entry(
            year=year,
            variable="corruption",
            value=new_state.corruption,
            previous=prior.corruption,
            causes=corruption.causes,
            note="Corruption balances legal suppression against conflict and poverty.",
        ),
        _entry(
            year=year,
            variable="trade_openness",
            value=new_state.trade_openness,
            previous=prior.trade_openness,
            causes=trade.causes,
            note="Trade openness converges 20% toward the policy target.",
        ),
        _entry(
            year=year,
            variable="school_life_expectancy",
            value=school_life.value,
            previous=prior_school_life.value,
            causes=school_life.causes,
            note="School life expectancy is informational Tier 2 output.",
        ),
        _entry(
            year=year,
            variable="hdi",
            value=reference.hdi,
            previous=prior_reference.hdi,
            causes=[
                ("life_expectancy_index", reference.life_expectancy_index),
                ("education_index", reference.education_index),
                ("income_index", reference.income_index),
            ],
            note="HDI is the geometric composite of health, education, and income.",
        ),
        _entry(
            year=year,
            variable="mean_years_schooling",
            value=reference.mean_years_schooling,
            previous=prior_reference.mean_years_schooling,
            causes=[
                (
                    "human_capital_mapping",
                    reference.mean_years_schooling
                    - prior_reference.mean_years_schooling,
                )
            ],
            note="Mean years of schooling is human capital multiplied by 15.",
        ),
        _entry(
            year=year,
            variable="expected_years_schooling",
            value=reference.expected_years_schooling,
            previous=prior_reference.expected_years_schooling,
            causes=[
                (
                    "school_life_expectancy_mapping",
                    reference.expected_years_schooling
                    - prior_reference.expected_years_schooling,
                )
            ],
            note="Expected years of schooling equals school life expectancy.",
        ),
    ]
    return entries


def _compute_candidate(
    prior: CountryState,
    policy: PolicyInputs,
    shocks: ExternalShocks,
) -> _Candidate:
    # Step 2. Update demographics.
    demographics = update_demographics(prior)

    # Step 3. Update urbanization from previous-year growth.
    urbanization = update_urbanization(prior)

    # Expenditure values are pure policy arithmetic and are needed by Steps 4-5.
    prospective_spends = expenditure_breakdown(policy)

    # Step 4. Advance the human-capital pipeline.
    human_capital = step_human_capital(
        prior, prospective_spends["education_spend"]
    )

    # Sequencing reconciliation: calculate the Step-19 value without committing it.
    prospective_trade = update_trade_openness(prior, policy)

    # Steps 5-6. MRW-delta growth and the prior conflict-risk penalty.
    growth = compute_gdp_growth(
        prior,
        human_capital.human_capital,
        prospective_trade.trade_openness,
        prospective_spends["infra_spend"],
    )

    # Step 7. Update absolute GDP.
    gdp_t = prior.gdp * (1.0 + growth.gdp_growth)
    if gdp_t <= 0.0:
        raise ValueError("GDP growth produced a non-positive GDP level")
    gdp_per_capita_t = gdp_t / demographics.population

    # Step 8. Compute the normalized output gap.
    output_gap = compute_output_gap(
        growth.gdp_growth, prior.potential_growth
    )

    # Step 9. Hybrid NKPC inflation.
    inflation = update_inflation(prior, policy, output_gap.value, shocks)

    # Step 10. Okun unemployment.
    unemployment = update_unemployment(prior, growth.gdp_growth)

    # Step 11. Fiscal flows.
    fiscal = compute_fiscal_flows(prior, policy)

    # Step 12. Debt dynamics.
    debt = update_debt(
        prior,
        growth.gdp_growth,
        inflation.inflation,
        fiscal.primary_balance_gdp,
    )

    # Step 13. Sovereign risk premium.
    risk = update_risk_premium(prior, debt.debt_gdp)

    # Step 14. Gini coefficient.
    gini = update_gini(
        prior,
        inflation.inflation,
        unemployment.unemployment,
        fiscal.transfers_spend,
    )

    # Step 15. Preston-curve life expectancy.
    life_expectancy = update_life_expectancy(
        prior, fiscal.health_spend, gdp_per_capita_t
    )

    # Step 16. Current conflict risk; it affects GDP/capacity in the next step.
    conflict = evaluate_conflict_risk(
        prior,
        unemployment.unemployment,
        growth.gdp_growth,
        gini.gini,
        inflation.inflation,
        fiscal.military_spend,
    )

    # Step 17. State capacity uses the prior persisted conflict-risk band.
    capacity = update_state_capacity(prior, fiscal.admin_spend)

    # Step 18. Corruption also uses prior conflict/legal capacity per the equation.
    corruption = update_corruption(prior, gdp_per_capita_t)

    # Step 19. Commit the previously calculated trade value.
    trade = prospective_trade

    # Step 20. Tier-2 school life expectancy.
    school_life = compute_school_life_expectancy(
        human_capital.human_capital, fiscal.education_spend
    )

    # Step 21. Tier-3 display-only reference metrics.
    reference_metrics = compute_reference_metrics(
        gdp_per_capita_t,
        life_expectancy.life_expectancy,
        human_capital.human_capital,
        school_life.value,
    )

    # Step 24 state assembly is delayed until every equation has used the prior state.
    new_state = CountryState(
        country_code=prior.country_code,
        year=prior.year + 1,
        gdp=gdp_t,
        inflation=inflation.inflation,
        unemployment=unemployment.unemployment,
        debt_gdp=debt.debt_gdp,
        risk_premium=risk.risk_premium,
        fiscal_capacity=capacity.fiscal_capacity,
        legal_capacity=capacity.legal_capacity,
        corruption=corruption.corruption,
        population=demographics.population,
        youth_share=demographics.youth_share,
        working_age_share=demographics.working_age_share,
        elderly_share=demographics.elderly_share,
        urban_pop_pct=urbanization.urban_pop_pct,
        human_capital=human_capital.human_capital,
        life_expectancy=life_expectancy.life_expectancy,
        gini=gini.gini,
        trade_openness=trade.trade_openness,
        conflict_risk=conflict.conflict_risk,
        hc_pipeline=human_capital.pipeline,
        potential_growth=prior.potential_growth,
        structural_unemployment=prior.structural_unemployment,
        urbanization_capacity=prior.urbanization_capacity,
        conflict_intercept=prior.conflict_intercept,
        previous_gdp_growth=growth.gdp_growth,
    )

    derived = {
        "gdp_growth": growth.gdp_growth,
        "gdp_per_capita": gdp_per_capita_t,
        "output_gap": output_gap.value,
        "tax_revenue_gdp": fiscal.tax_revenue_gdp,
        "primary_balance_gdp": fiscal.primary_balance_gdp,
        "conflict_risk": conflict.conflict_risk,
        "political_stability_score": conflict.political_stability_score,
        "school_life_expectancy": school_life.value,
        # Additional transparent flow diagnostics.
        "population_growth": demographics.population_growth,
        "total_expenditure_gdp": fiscal.total_expenditure_gdp,
        "health_spend_gdp": fiscal.health_spend,
        "education_spend_gdp": fiscal.education_spend,
        "infrastructure_spend_gdp": fiscal.infra_spend,
        "social_transfers_spend_gdp": fiscal.transfers_spend,
        "admin_spend_gdp": fiscal.admin_spend,
        "military_spend_gdp": fiscal.military_spend,
        "nominal_interest": debt.nominal_interest,
        "nominal_gdp_growth": debt.nominal_gdp_growth,
        "conflict_eta": conflict.eta,
        "capacity_investment_factor": capacity.investment_factor,
        "new_hc_investment": human_capital.new_investment,
        "matured_hc_investment": human_capital.matured_investment,
    }
    reference = {
        "hdi": reference_metrics.hdi,
        "mean_years_schooling": reference_metrics.mean_years_schooling,
        "expected_years_schooling": reference_metrics.expected_years_schooling,
    }

    # Step 22. Generate the complete explainability record.
    audit_log = _build_audit_log(
        prior,
        new_state,
        policy,
        demographics,
        urbanization,
        human_capital,
        growth,
        output_gap,
        inflation,
        unemployment,
        fiscal,
        debt,
        risk,
        gini,
        life_expectancy,
        conflict,
        capacity,
        corruption,
        trade,
        school_life,
        reference_metrics,
    )

    return _Candidate(
        state=new_state,
        derived=derived,
        reference=reference,
        audit_log=audit_log,
    )


def _append_stabilizer_audit(
    audit_log: list[AuditEntry],
    prior: CountryState,
    original_policy: PolicyInputs,
    stabilizer: StabilizerResult,
) -> None:
    effective = stabilizer.policy

    if stabilizer.sovereign_triggered:
        audit_log.append(
            _entry(
                year=prior.year,
                variable="effective_expenditure_gdp",
                value=effective.total_expenditure_gdp,
                previous=original_policy.total_expenditure_gdp,
                causes=[
                    (
                        "sovereign_pressure_constraint",
                        -stabilizer.sovereign_consolidation,
                    )
                ],
                note=(
                    "Debt above 90% triggered the Step-23 sovereign spending "
                    "constraint."
                ),
            )
        )

    if stabilizer.safety_net_triggered:
        old_transfer = (
            original_policy.social_transfers_share
            * original_policy.total_expenditure_gdp
        )
        new_transfer = (
            effective.social_transfers_share
            * effective.total_expenditure_gdp
        )
        consolidation_effect = original_policy.social_transfers_share * (
            effective.total_expenditure_gdp
            - original_policy.total_expenditure_gdp
        )
        audit_log.append(
            _entry(
                year=prior.year,
                variable="effective_social_transfers_gdp",
                value=new_transfer,
                previous=old_transfer,
                causes=[
                    ("sovereign_pressure_constraint", consolidation_effect),
                    (
                        "unemployment_safety_net",
                        stabilizer.safety_net_reallocation,
                    ),
                ],
                note=(
                    "Unemployment above 20% imposed the minimum 1% GDP social "
                    "transfer floor."
                ),
            )
        )

        for source, moved in stabilizer.reallocation_sources:
            original_share = getattr(original_policy, source)
            effective_share = getattr(effective, source)
            old_spend = original_share * original_policy.total_expenditure_gdp
            new_spend = effective_share * effective.total_expenditure_gdp
            audit_log.append(
                _entry(
                    year=prior.year,
                    variable=f"effective_{source.removesuffix('_share')}_spend_gdp",
                    value=new_spend,
                    previous=old_spend,
                    causes=[
                        (
                            "sovereign_pressure_constraint",
                            original_share
                            * (
                                effective.total_expenditure_gdp
                                - original_policy.total_expenditure_gdp
                            ),
                        ),
                        ("unemployment_safety_net_reallocation", -moved),
                    ],
                    note="Non-essential spending was reallocated to the safety net.",
                )
            )


class SimulationEngine:
    """Execute the guidebook's deterministic annual update contract."""

    PHASES = (
        "validate_policy_inputs",
        "update_demographics",
        "update_urbanization",
        "advance_human_capital_pipeline",
        "compute_gdp_growth",
        "apply_conflict_penalty",
        "update_gdp_level",
        "compute_output_gap",
        "update_inflation",
        "update_unemployment",
        "compute_fiscal_flows",
        "update_debt",
        "update_risk_premium",
        "update_gini",
        "update_life_expectancy",
        "evaluate_conflict_risk",
        "update_state_capacity",
        "update_corruption",
        "update_trade_openness",
        "compute_school_life_expectancy",
        "compute_reference_metrics",
        "generate_audit_log",
        "apply_automatic_stabilizers",
        "increment_year_and_return",
    )

    @staticmethod
    def step(
        state: CountryState,
        policy_inputs: PolicyInputs,
        external_shocks: ExternalShocks | dict[str, float] | None = None,
    ) -> StepResult:
        # Step 1. Validate the player's requested policy.
        validate_policy(policy_inputs)
        shocks = normalize_external_shocks(external_shocks)

        # Deep prior-year snapshot: no domain equation mutates caller-owned state.
        prior = state.clone()
        ordinary = _compute_candidate(prior, policy_inputs, shocks)

        # Step 23. Evaluate candidate end-state constraints.
        stabilizer = apply_automatic_stabilizers(
            policy_inputs,
            ordinary.state.debt_gdp,
            ordinary.state.unemployment,
        )

        policy_changed = stabilizer.policy != policy_inputs
        if policy_changed:
            validate_policy(stabilizer.policy)
            final = _compute_candidate(prior, stabilizer.policy, shocks)
        else:
            final = ordinary

        derived = dict(final.derived)
        derived.update(
            {
                "effective_total_expenditure_gdp": (
                    stabilizer.policy.total_expenditure_gdp
                ),
                "effective_social_transfers_spend_gdp": (
                    stabilizer.policy.social_transfers_share
                    * stabilizer.policy.total_expenditure_gdp
                ),
                "sovereign_consolidation": stabilizer.sovereign_consolidation,
                "safety_net_reallocation": stabilizer.safety_net_reallocation,
                "stabilizer_recomputed": 1.0 if policy_changed else 0.0,
            }
        )

        audit_log = list(final.audit_log)
        _append_stabilizer_audit(
            audit_log, prior, policy_inputs, stabilizer
        )

        return StepResult(
            state=final.state,
            derived=derived,
            reference=dict(final.reference),
            audit_log=audit_log,
        )

    @staticmethod
    def simulate(
        state: CountryState,
        policy_inputs: PolicyInputs,
        years: int,
        external_shocks: ExternalShocks | dict[str, float] | None = None,
    ) -> list[StepResult]:
        if years < 0:
            raise ValueError("years must be non-negative")
        results: list[StepResult] = []
        current = state.clone()
        for _ in range(years):
            result = SimulationEngine.step(
                current, policy_inputs, external_shocks
            )
            results.append(result)
            current = result.state
        return results
