"""Layer 4 real growth, inflation, and labour-market equations."""

from __future__ import annotations

from dataclasses import dataclass

from engine.core.constants import (
    ALPHA,
    BETA,
    CAPACITY_GDP_COEFF,
    DEBT_DRAG_COEFF,
    DEBT_STABILITY_THRESHOLD,
    DEPRECIATION_RATE,
    HC_PIPELINE_LAG,
    HC_TRADE_THRESHOLD,
    INFLATION_MAX,
    INFLATION_MIN,
    INFLATION_PERSISTENCE,
    INFLATION_UNMODELLED_WEIGHT,
    NKPC_KAPPA,
    OKUN_COEFFICIENT,
    OUTPUT_GAP_DENOMINATOR_FLOOR,
    OUTPUT_GAP_MAX,
    OUTPUT_GAP_MIN,
    PASSTHROUGH_RATE,
    TRADE_GDP_COEFF,
    UNEMPLOYMENT_MAX,
)
from engine.core.country_state import CountryState
from engine.core.helpers import clamp_with_adjustment
from engine.core.policy_inputs import PolicyInputs
from engine.global_context.shocks import ExternalShocks
from engine.politics.stability import conflict_gdp_penalty


@dataclass(frozen=True)
class GrowthBreakdown:
    gdp_growth_raw: float
    conflict_adjustment: float
    gdp_growth: float
    capital_accumulation: float
    human_capital_delta: float
    trade_delta: float
    causes: list[tuple[str, float]]


@dataclass(frozen=True)
class OutputGap:
    value: float
    raw_value: float
    causes: list[tuple[str, float]]


@dataclass(frozen=True)
class InflationUpdate:
    inflation: float
    causes: list[tuple[str, float]]


@dataclass(frozen=True)
class UnemploymentUpdate:
    unemployment: float
    delta_u: float
    causes: list[tuple[str, float]]


def compute_gdp_growth(
    state: CountryState,
    human_capital_t: float,
    trade_openness_t: float,
    infra_spend_gdp: float,
) -> GrowthBreakdown:
    capital_accumulation = infra_spend_gdp - DEPRECIATION_RATE
    capital_effect = ALPHA * capital_accumulation

    human_capital_delta = human_capital_t - state.human_capital
    human_capital_effect = (
        (BETA / HC_PIPELINE_LAG) * human_capital_delta * 50.0
    )

    capacity_effect = CAPACITY_GDP_COEFF * (state.legal_capacity - 0.5)

    debt_drag = (
        DEBT_DRAG_COEFF * (state.debt_gdp - DEBT_STABILITY_THRESHOLD)
        if state.debt_gdp > DEBT_STABILITY_THRESHOLD
        else 0.0
    )

    trade_delta = trade_openness_t - state.trade_openness
    trade_effect = (
        TRADE_GDP_COEFF * trade_delta
        if state.human_capital > HC_TRADE_THRESHOLD
        else 0.0
    )

    raw = (
        state.potential_growth
        + capital_effect
        + human_capital_effect
        + capacity_effect
        - debt_drag
        + trade_effect
    )
    conflict_adjustment = conflict_gdp_penalty(state.conflict_risk)
    growth = raw + conflict_adjustment

    return GrowthBreakdown(
        gdp_growth_raw=raw,
        conflict_adjustment=conflict_adjustment,
        gdp_growth=growth,
        capital_accumulation=capital_accumulation,
        human_capital_delta=human_capital_delta,
        trade_delta=trade_delta,
        causes=[
            ("potential_growth", state.potential_growth),
            ("capital_accumulation", capital_effect),
            ("human_capital_change", human_capital_effect),
            ("state_capacity_tfp", capacity_effect),
            ("debt_overhang", -debt_drag),
            ("trade_openness", trade_effect),
            ("conflict_penalty", conflict_adjustment),
        ],
    )


def compute_output_gap(
    gdp_growth: float,
    potential_growth: float,
) -> OutputGap:
    denominator = max(abs(potential_growth), OUTPUT_GAP_DENOMINATOR_FLOOR)
    raw = (gdp_growth - potential_growth) / denominator
    value, boundary_adjustment = clamp_with_adjustment(
        raw, OUTPUT_GAP_MIN, OUTPUT_GAP_MAX
    )
    causes = [("growth_deviation_from_potential", raw)]
    if boundary_adjustment:
        causes.append(("range_clamp", boundary_adjustment))
    return OutputGap(value=value, raw_value=raw, causes=causes)


def update_inflation(
    state: CountryState,
    policy: PolicyInputs,
    output_gap: float,
    external_shocks: ExternalShocks,
) -> InflationUpdate:
    backward = INFLATION_PERSISTENCE * state.inflation
    forward = (
        1.0 - INFLATION_PERSISTENCE - INFLATION_UNMODELLED_WEIGHT
    ) * policy.inflation_target
    demand_push = NKPC_KAPPA * output_gap
    import_push = (
        PASSTHROUGH_RATE
        * external_shocks.import_price_change
        * state.trade_openness
    )

    raw = backward + forward + demand_push + import_push
    inflation_t, boundary_adjustment = clamp_with_adjustment(
        raw, INFLATION_MIN, INFLATION_MAX
    )
    causes = [
        ("inflation_persistence", backward),
        ("target_anchor", forward),
        ("demand_push", demand_push),
        ("import_passthrough", import_push),
    ]
    if boundary_adjustment:
        causes.append(("range_clamp", boundary_adjustment))

    return InflationUpdate(inflation=inflation_t, causes=causes)


def update_unemployment(
    state: CountryState,
    gdp_growth: float,
) -> UnemploymentUpdate:
    delta_u = -OKUN_COEFFICIENT * (
        gdp_growth - state.potential_growth
    )
    raw = state.unemployment + delta_u
    unemployment_t, boundary_adjustment = clamp_with_adjustment(
        raw, state.structural_unemployment, UNEMPLOYMENT_MAX
    )
    causes = [("okun_gdp_effect", delta_u)]
    if boundary_adjustment:
        causes.append(("structural_or_range_floor", boundary_adjustment))
    return UnemploymentUpdate(
        unemployment=unemployment_t,
        delta_u=delta_u,
        causes=causes,
    )
