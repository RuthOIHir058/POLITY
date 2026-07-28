"""Backward-compatible facade for the canonical SimulationEngine."""

from engine.core.country_state import CountryState
from engine.core.policy_inputs import PolicyInputs
from engine.core.simulation_engine import SimulationEngine
from engine.core.step_result import StepResult
from engine.global_context.shocks import ExternalShocks


class SimulationStep:
    @staticmethod
    def step(
        state: CountryState,
        policy_inputs: PolicyInputs,
        external_shocks: ExternalShocks | dict[str, float] | None = None,
    ) -> StepResult:
        return SimulationEngine.step(state, policy_inputs, external_shocks)

    @staticmethod
    def run(
        state: CountryState,
        policy_inputs: PolicyInputs,
        external_shocks: ExternalShocks | dict[str, float] | None = None,
    ) -> StepResult:
        return SimulationStep.step(state, policy_inputs, external_shocks)
