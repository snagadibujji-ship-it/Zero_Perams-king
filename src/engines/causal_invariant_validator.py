from typing import Dict, List


class CausalInvariantValidator:
    """Transition invariants to guard against non-causal jumps.

    Checks year-over-year deltas, directional responses, and lagged responses
    to major pressure changes.
    """

    DELTA_LIMITS = {
        'civilization_entropy': 0.35,
        'emotional_pressure': 0.40,
        'geopolitical_instability': 0.40,
        'migration_pressure': 0.38,
        'institutional_trust': 0.35,
        'technological_maturity': 0.30,
    }

    def validate_transition(self, prev_state: Dict[str, object], state: Dict[str, object]) -> Dict[str, object]:
        warnings: List[str] = []
        score = 1.0

        for key, limit in self.DELTA_LIMITS.items():
            if key in prev_state and key in state:
                delta = abs(float(state[key]) - float(prev_state[key]))
                if delta > limit:
                    warnings.append(f'delta_too_large:{key}:{round(delta,3)}>{limit}')
                    score -= 0.08

        war_pressure = float(state.get('historical_pressure_vector', {}).get('war_pressure', 0.0))
        if war_pressure >= 0.6:
            if float(state.get('geopolitical_instability', 0.0)) < 0.45:
                warnings.append('high_war_pressure_without_geopolitical_instability_response')
                score -= 0.16
            if float(state.get('migration_pressure', 0.0)) < 0.2:
                warnings.append('high_war_pressure_without_migration_response')
                score -= 0.1

        recovery = float(state.get('historical_pressure_vector', {}).get('recovery_momentum', 0.0))
        if recovery >= 0.5 and float(state.get('civilization_entropy', 1.0)) > float(prev_state.get('civilization_entropy', 1.0)) + 0.2:
            warnings.append('recovery_momentum_with_entropy_spike_conflict')
            score -= 0.1

        self._validate_directional_constraints(prev_state, state, warnings)
        score -= 0.05 * len([w for w in warnings if w.startswith('directional_constraint_failed')])

        lag_violations = self._validate_lag_constraints(prev_state, state, warnings)
        score -= 0.06 * lag_violations

        return {
            'valid': score >= 0.68,
            'causal_transition_score': round(max(0.0, score), 3),
            'warnings': warnings,
        }

    def _validate_directional_constraints(
        self,
        prev_state: Dict[str, object],
        state: Dict[str, object],
        warnings: List[str],
    ) -> None:
        prev_vector = prev_state.get('historical_pressure_vector', {})
        curr_vector = state.get('historical_pressure_vector', {})

        war_delta = float(curr_vector.get('war_pressure', 0.0)) - float(prev_vector.get('war_pressure', 0.0))
        if war_delta >= 0.18:
            geo_delta = float(state.get('geopolitical_instability', 0.0)) - float(prev_state.get('geopolitical_instability', 0.0))
            if geo_delta < -0.04:
                warnings.append('directional_constraint_failed:war_pressure_up_requires_non_decreasing_geopolitical_instability')

        recovery_delta = float(curr_vector.get('recovery_momentum', 0.0)) - float(prev_vector.get('recovery_momentum', 0.0))
        trust_delta = float(state.get('institutional_trust', 0.0)) - float(prev_state.get('institutional_trust', 0.0))
        if recovery_delta >= 0.2 and trust_delta < -0.05:
            warnings.append('directional_constraint_failed:recovery_momentum_up_requires_non_falling_institutional_trust')

        disruption_delta = float(curr_vector.get('technological_disruption', 0.0)) - float(prev_vector.get('technological_disruption', 0.0))
        maturity_delta = float(state.get('technological_maturity', 0.0)) - float(prev_state.get('technological_maturity', 0.0))
        if disruption_delta >= 0.2 and maturity_delta < -0.05:
            warnings.append('directional_constraint_failed:technological_disruption_up_requires_non_falling_technological_maturity')

    def _validate_lag_constraints(
        self,
        prev_state: Dict[str, object],
        state: Dict[str, object],
        warnings: List[str],
    ) -> int:
        lag_violations = 0
        stress_memory = prev_state.get('lag_stress_memory', {})
        if not isinstance(stress_memory, dict):
            stress_memory = {}

        curr_vector = state.get('historical_pressure_vector', {})
        war = float(curr_vector.get('war_pressure', 0.0))
        dislocation = float(curr_vector.get('economic_dislocation', 0.0))

        if war >= 0.7:
            stress_memory['war_spike_window'] = 2
        if dislocation >= 0.65:
            stress_memory['dislocation_window'] = 2

        if int(stress_memory.get('war_spike_window', 0)) > 0:
            if float(state.get('migration_pressure', 0.0)) < 0.24:
                warnings.append('lag_constraint_failed:war_spike_requires_migration_pressure_within_2_ticks')
                lag_violations += 1
            stress_memory['war_spike_window'] = max(0, int(stress_memory['war_spike_window']) - 1)

        if int(stress_memory.get('dislocation_window', 0)) > 0:
            if float(state.get('emotional_pressure', 0.0)) < 0.34:
                warnings.append('lag_constraint_failed:economic_dislocation_requires_emotional_pressure_within_2_ticks')
                lag_violations += 1
            stress_memory['dislocation_window'] = max(0, int(stress_memory['dislocation_window']) - 1)

        state['lag_stress_memory'] = stress_memory
        return lag_violations
