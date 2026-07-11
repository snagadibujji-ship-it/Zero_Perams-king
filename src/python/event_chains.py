"""
GHIA-CHRONOS — HELIX (Engine 6)
DAG Event Chains — Temporal Markov Dependencies

Generates realistic multi-stage event sequences where each event's
probability depends on what happened before.

Example: failed_login -> brute_force_detected -> account_lockout -> incident_declared
         sensor_drift -> threshold_breach -> alarm -> shutdown -> maintenance

Usage:
    from ghia.event_chains import generate_event_chain, DAG_TEMPLATES
    chain = generate_event_chain(world='cybersecurity', seed=42)
"""

import random
import json
import time
from typing import Dict, List, Any


# Directed Acyclic Graph templates: each node triggers the next with probability
# Format: {trigger_event: [(next_event, probability, delay_seconds, severity_escalation)]}

DAG_TEMPLATES = {
    'cybersecurity': {
        'failed_login': [('brute_force_detected', 0.7, 30, 1), ('access_violation', 0.3, 10, 1)],
        'brute_force_detected': [('account_lockout', 0.8, 5, 0), ('incident_declared', 0.5, 60, 2)],
        'account_lockout': [('password_reset_request', 0.6, 300, -1), ('incident_declared', 0.3, 120, 1)],
        'incident_declared': [('containment_started', 0.9, 60, 0), ('escalation_to_management', 0.5, 180, 1)],
        'containment_started': [('forensics_initiated', 0.8, 600, 0), ('system_isolated', 0.7, 30, 0)],
        'threat_detected': [('scan_initiated', 0.9, 10, 0), ('alert_triggered', 0.95, 5, 1)],
        'vulnerability_found': [('patch_scheduled', 0.7, 3600, 0), ('exploit_attempted', 0.1, 7200, 2)],
        'malware_detected': [('quarantine_initiated', 0.95, 5, 1), ('lateral_movement_check', 0.6, 30, 1)],
    },
    'healthcare': {
        'patient_admit': [('triage_assessment', 0.99, 60, 0), ('bed_assignment', 0.9, 300, 0)],
        'vital_sign_abnormal': [('nurse_notified', 0.95, 30, 1), ('rapid_response_called', 0.3, 60, 2)],
        'rapid_response_called': [('physician_arrived', 0.95, 180, 0), ('intervention_started', 0.8, 300, 1)],
        'intervention_started': [('vitals_stabilized', 0.7, 1800, -1), ('icu_transfer', 0.3, 600, 2)],
        'lab_result_critical': [('physician_notified', 0.99, 60, 1), ('treatment_modified', 0.7, 300, 0)],
        'medication_error': [('event_reported', 0.9, 60, 1), ('patient_assessed', 0.99, 30, 1), ('root_cause_analysis', 0.6, 86400, 0)],
        'patient_fall': [('injury_assessment', 0.99, 30, 1), ('incident_report', 0.95, 300, 0), ('fall_prevention_review', 0.7, 3600, 0)],
    },
    'manufacturing': {
        'spc_alarm': [('operator_investigation', 0.9, 60, 0), ('production_hold', 0.4, 120, 1)],
        'production_hold': [('quality_review', 0.95, 300, 0), ('rework_initiated', 0.5, 600, 0)],
        'equipment_vibration_high': [('bearing_inspection', 0.8, 3600, 0), ('predictive_alert', 0.6, 60, 1)],
        'predictive_alert': [('maintenance_scheduled', 0.7, 7200, 0), ('emergency_shutdown', 0.1, 30, 2)],
        'emergency_shutdown': [('lockout_tagout', 0.95, 60, 0), ('repair_started', 0.8, 1800, 0)],
        'repair_started': [('repair_complete', 0.85, 7200, -1), ('parts_ordered', 0.3, 600, 0)],
        'quality_escape': [('customer_notification', 0.6, 3600, 1), ('containment_action', 0.9, 300, 1), ('capa_opened', 0.8, 86400, 0)],
    },
    'mining': {
        'slope_movement_detected': [('monitoring_increased', 0.9, 300, 0), ('evacuation_warning', 0.3, 60, 2)],
        'evacuation_warning': [('personnel_cleared', 0.95, 600, 0), ('slope_failure', 0.1, 1800, 3)],
        'blast_fired': [('dust_monitoring', 0.9, 30, 0), ('fragmentation_check', 0.8, 300, 0), ('vibration_recorded', 0.95, 5, 0)],
        'equipment_fault': [('operator_stop', 0.7, 30, 0), ('maintenance_dispatched', 0.8, 300, 0)],
        'grade_below_cutoff': [('resampling_ordered', 0.6, 3600, 0), ('blast_pattern_adjusted', 0.4, 7200, 0)],
    },
    'aviation': {
        'engine_indication_abnormal': [('pilot_monitoring', 0.9, 10, 0), ('checklist_initiated', 0.7, 30, 1)],
        'checklist_initiated': [('engine_shutdown_inflight', 0.2, 120, 2), ('diversion_considered', 0.4, 60, 1)],
        'diversion_considered': [('diversion_initiated', 0.5, 300, 1), ('continued_to_destination', 0.5, 0, 0)],
        'bird_strike': [('damage_assessment', 0.9, 60, 1), ('return_to_field', 0.3, 120, 2)],
        'weather_deterioration': [('alternate_planning', 0.8, 300, 0), ('holding_pattern', 0.5, 60, 0), ('diversion_initiated', 0.2, 600, 1)],
    },
    'energy': {
        'frequency_deviation': [('governor_response', 0.95, 2, 0), ('load_shedding_armed', 0.3, 10, 1)],
        'transformer_overtemp': [('cooling_fans_max', 0.9, 5, 0), ('load_reduction', 0.5, 60, 1), ('trip_imminent', 0.1, 300, 2)],
        'solar_output_drop': [('cloud_cover_detected', 0.8, 10, 0), ('reserve_activated', 0.4, 30, 0)],
        'outage_detected': [('fault_located', 0.8, 300, 0), ('crew_dispatched', 0.9, 60, 0), ('customers_notified', 0.7, 120, 0)],
        'crew_dispatched': [('arrived_on_site', 0.95, 1800, 0), ('repair_started', 0.9, 2400, 0)],
    },
}

SEVERITY_LEVELS = ['info', 'warning', 'error', 'critical']

# EC-7: All 30 worlds — generic DAG patterns for worlds without specific templates
_GENERIC_DAG_PATTERNS = {
    'alert_triggered': [('investigation_started', 0.9, 60, 0), ('escalated', 0.3, 120, 1)],
    'investigation_started': [('root_cause_found', 0.7, 1800, 0), ('additional_symptoms', 0.4, 600, 1)],
    'root_cause_found': [('fix_applied', 0.8, 3600, -1), ('workaround_deployed', 0.3, 600, 0)],
    'fix_applied': [('verification_passed', 0.85, 1800, -1), ('fix_failed', 0.15, 600, 1)],
    'escalated': [('senior_engaged', 0.9, 300, 0), ('vendor_contacted', 0.5, 600, 0)],
    'senior_engaged': [('resolution_planned', 0.8, 1200, 0), ('further_escalation', 0.2, 1800, 1)],
    'anomaly_detected': [('alert_triggered', 0.9, 10, 1), ('self_resolved', 0.2, 300, -1)],
    'threshold_breach': [('alert_triggered', 0.95, 5, 1), ('system_degraded', 0.4, 60, 1)],
    'system_degraded': [('failover_activated', 0.5, 30, 0), ('outage_declared', 0.2, 300, 2)],
    'outage_declared': [('incident_response', 0.95, 60, 0), ('stakeholders_notified', 0.9, 120, 0)],
    'incident_response': [('containment_achieved', 0.8, 1800, 0), ('escalated', 0.3, 600, 1)],
    'containment_achieved': [('recovery_started', 0.9, 600, -1), ('post_mortem_scheduled', 0.7, 86400, 0)],
    'maintenance_scheduled': [('maintenance_started', 0.95, 7200, 0)],
    'maintenance_started': [('maintenance_complete', 0.85, 14400, -1), ('parts_needed', 0.2, 3600, 0)],
}

# Fill in worlds that don't have specific DAGs
_ALL_WORLDS = [
    'agriculture', 'aviation', 'biotech', 'coding', 'construction', 'cybersecurity',
    'defense', 'ecommerce', 'education', 'energy', 'finance', 'gaming', 'government',
    'healthcare', 'hospitality', 'industries', 'insurance', 'legal', 'manufacturing',
    'maritime', 'media', 'mining', 'pharma', 'realestate', 'robotics', 'science',
    'space', 'supplychain', 'telecom', 'transport',
]

for _w in _ALL_WORLDS:
    if _w not in DAG_TEMPLATES:
        DAG_TEMPLATES[_w] = dict(_GENERIC_DAG_PATTERNS)


def _lognormal_delay(base_delay: float, rng: random.Random) -> float:
    """EC-8: Log-normal delay distribution (realistic: most events fast, some very slow)."""
    import math
    # Log-normal: median ≈ base_delay, with fat right tail
    mu = math.log(max(base_delay, 1))
    sigma = 0.8  # moderate spread
    return max(1, rng.lognormvariate(mu, sigma))


def generate_event_chain(world: str, trigger: str = None, seed: int = 42,
                          max_depth: int = 12, inter_entity: bool = False,
                          base_timestamp: str = None) -> Dict:
    """Generate a realistic event chain starting from a trigger event.
    
    Args:
        world: Domain world.
        trigger: Starting event (None = random from world's DAG).
        seed: RNG seed.
        max_depth: Maximum chain length (EC-3: default 12, supports 15+).
        inter_entity: EC-5 — if True, events can jump to related entities.
        base_timestamp: EC-9 — ISO timestamp for chain start (None = offset-only).
    
    Returns:
        Dict with events list, edges, root_event, chain_id, etc.
    """
    import math
    rng = random.Random(seed)
    dag = DAG_TEMPLATES.get(world, _GENERIC_DAG_PATTERNS)
    
    if trigger is None:
        trigger = rng.choice(list(dag.keys()))
    
    chain = []
    current_time = 0.0
    current_severity = 1  # start at warning
    entity_id = f"E-{rng.randint(1000,9999)}"
    chain_id = f"CHAIN-{seed:06d}"
    
    # EC-9: Absolute timestamp support
    if base_timestamp is None:
        # Generate a realistic base timestamp
        year = 2024
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        hour = rng.randint(0, 23)
        minute = rng.randint(0, 59)
        base_ts_epoch = 1704067200 + (month-1)*2592000 + (day-1)*86400 + hour*3600 + minute*60
    else:
        # Parse ISO timestamp
        import datetime
        base_ts_epoch = 1704067200  # fallback
    
    def _epoch_to_iso(epoch):
        """Convert epoch seconds to ISO 8601 string."""
        t = 1704067200 + epoch  # offset from 2024-01-01
        days = int(t // 86400)
        rem = int(t % 86400)
        # Simple conversion (approximate, good enough for synthetic data)
        year = 2024 + days // 365
        doy = days % 365
        month = min(12, doy // 30 + 1)
        day = max(1, doy % 30 + 1)
        h, m, s = rem // 3600, (rem % 3600) // 60, rem % 60
        return f"{year}-{month:02d}-{day:02d}T{h:02d}:{m:02d}:{s:02d}Z"
    
    # First event
    first_event = {
        'chain_id': chain_id,
        'sequence': 0,
        'event_type': trigger,
        'timestamp_offset_s': 0,
        'timestamp': _epoch_to_iso(current_time),
        'severity': SEVERITY_LEVELS[min(current_severity, 3)],
        'entity_id': entity_id,
        'caused_by': None,
        'world': world,
    }
    chain.append(first_event)
    
    # Follow DAG with proper branching and cycle detection
    visited = {trigger}
    branch_queue = [(trigger, current_time, current_severity, entity_id)]
    
    while branch_queue and len(chain) < max_depth + 1:
        current_event, current_time, current_severity, curr_entity = branch_queue.pop(0)
        
        if current_event not in dag:
            continue
        
        possible_next = dag[current_event]
        triggered = []
        
        for next_event, probability, delay, sev_change in possible_next:
            if rng.random() < probability:
                triggered.append((next_event, delay, sev_change))
        
        if not triggered:
            continue
        
        for next_event, delay, sev_change in triggered[:3]:
            if next_event in visited:
                continue
            visited.add(next_event)
            
            # EC-8: Log-normal delay (realistic distribution)
            event_delay = _lognormal_delay(delay, rng)
            event_time = current_time + event_delay
            event_severity = max(0, min(3, current_severity + sev_change))
            
            # EC-5: Inter-entity chains (event can propagate to related entity)
            event_entity = curr_entity
            if inter_entity and rng.random() < 0.2:
                event_entity = f"E-{rng.randint(1000,9999)}"
            
            event = {
                'chain_id': chain_id,
                'sequence': len(chain),
                'event_type': next_event,
                'timestamp_offset_s': round(event_time, 1),
                'timestamp': _epoch_to_iso(event_time),
                'severity': SEVERITY_LEVELS[event_severity],
                'entity_id': event_entity,
                'caused_by': current_event,
                'world': world,
            }
            chain.append(event)
            
            if len(chain) < max_depth + 1:
                branch_queue.append((next_event, event_time, event_severity, event_entity))
    
    # Build DAG edges
    edges = []
    for event in chain[1:]:
        edges.append({
            "source": event["caused_by"],
            "target": event["event_type"],
            "timestamp_offset": event["timestamp_offset_s"],
        })
    
    return {
        "events": chain,
        "edges": edges,
        "root_event": trigger,
        "chain_id": chain_id,
        "depth": len(chain),
        "world": world,
        "entity_id": entity_id,
    }


def generate_chain_dataset(worlds: List[str] = None, chains_per_world: int = 50,
                            seed: int = 6786, output_file: str = None) -> List[Dict]:
    """Generate dataset of event chains across multiple worlds."""
    if worlds is None:
        worlds = list(DAG_TEMPLATES.keys())
    
    rng = random.Random(seed)
    all_chains = []
    
    for world in worlds:
        dag = DAG_TEMPLATES[world]
        triggers = list(dag.keys())
        
        for i in range(chains_per_world):
            trigger = rng.choice(triggers)
            chain = generate_event_chain(world, trigger, seed + i + hash(world) % 1000)
            all_chains.extend(chain)
    
    if output_file:
        with open(output_file, 'w') as f:
            for event in all_chains:
                f.write(json.dumps(event) + '\n')
    
    return all_chains


# ═══════════════════════════════════════════════════════════════════════
# EC-2: Multi-World Causal Chains
# ═══════════════════════════════════════════════════════════════════════

def generate_multi_world_chain(worlds: list, seed: int = 42, max_depth: int = 8) -> Dict:
    """Generate a causal chain that spans multiple worlds/domains.
    
    Example: cyber attack → power outage → hospital disruption
    """
    rng = random.Random(seed)
    chain = {'chain_id': f'MULTI-WORLD-{seed:06d}', 'events': [], 'worlds_traversed': []}
    
    for i, world in enumerate(worlds[:min(len(worlds), 4)]):
        sub_chain = generate_event_chain(world, seed=seed + i * 100, max_depth=max_depth // len(worlds))
        for event in sub_chain['events']:
            event['chain_world_sequence'] = i
            event['cross_world'] = True
            chain['events'].append(event)
        chain['worlds_traversed'].append(world)
    
    # Link cross-world causality
    for i in range(1, len(chain['events'])):
        if chain['events'][i].get('chain_world_sequence', 0) != chain['events'][i-1].get('chain_world_sequence', 0):
            chain['events'][i]['cross_world_trigger'] = chain['events'][i-1]['event_type']
    
    chain['total_events'] = len(chain['events'])
    chain['worlds_count'] = len(chain['worlds_traversed'])
    return chain


# ═══════════════════════════════════════════════════════════════════════
# EC-10: Counterfactual Branches
# ═══════════════════════════════════════════════════════════════════════

def generate_counterfactual(world: str, seed: int = 42, branch_point: int = 2) -> Dict:
    """Generate actual chain + counterfactual 'what-if' alternative branch.
    
    At branch_point, we diverge into two paths:
    - actual: what happened (as generated)
    - counterfactual: what would have happened with different choices
    """
    rng = random.Random(seed)
    
    # Generate actual chain
    actual = generate_event_chain(world, seed=seed, max_depth=8)
    
    # Generate counterfactual (different seed = different path from branch point)
    counter = generate_event_chain(world, seed=seed + 999, max_depth=8)
    
    # Build counterfactual structure
    branch_idx = min(branch_point, len(actual['events']) - 1)
    
    return {
        'chain_id': f'CF-{seed:06d}',
        'world': world,
        'branch_point': branch_idx,
        'branch_event': actual['events'][branch_idx]['event_type'] if branch_idx < len(actual['events']) else None,
        'actual_path': actual['events'],
        'counterfactual_path': counter['events'],
        'actual_outcome': actual['events'][-1]['severity'] if actual['events'] else None,
        'counterfactual_outcome': counter['events'][-1]['severity'] if counter['events'] else None,
        'divergence_reason': 'Different response to trigger event',
    }


# ═══════════════════════════════════════════════════════════════════════
# HELIX MAX LEVEL — Extended Capabilities
# ═══════════════════════════════════════════════════════════════════════

def generate_parallel_chains(world: str, num_chains: int = 3, seed: int = 42,
                             max_depth: int = 10) -> Dict:
    """Generate multiple parallel chains that may interact.
    
    Real incidents have multiple simultaneous causal threads that
    occasionally cross. This simulates that.
    """
    rng = random.Random(seed)
    dag = DAG_TEMPLATES.get(world, _GENERIC_DAG_PATTERNS)
    triggers = list(dag.keys())
    
    chains = []
    all_events = []
    interactions = []
    
    for i in range(num_chains):
        trigger = rng.choice(triggers)
        chain = generate_event_chain(world, trigger=trigger, seed=seed + i * 77,
                                     max_depth=max_depth // num_chains + 2)
        chains.append(chain)
        for event in chain['events']:
            event['thread_id'] = i
            all_events.append(event)
    
    # Detect interactions: if two threads have events within 60s of each other
    all_events.sort(key=lambda e: e['timestamp_offset_s'])
    for i in range(len(all_events) - 1):
        for j in range(i + 1, min(i + 5, len(all_events))):
            if all_events[i]['thread_id'] != all_events[j]['thread_id']:
                time_diff = abs(all_events[j]['timestamp_offset_s'] - all_events[i]['timestamp_offset_s'])
                if time_diff < 60:
                    interactions.append({
                        'event_a': all_events[i]['event_type'],
                        'event_b': all_events[j]['event_type'],
                        'thread_a': all_events[i]['thread_id'],
                        'thread_b': all_events[j]['thread_id'],
                        'time_gap_s': round(time_diff, 1),
                        'interaction_type': 'temporal_proximity',
                    })
    
    return {
        'chain_id': f'PARALLEL-{seed:06d}',
        'world': world,
        'num_threads': num_chains,
        'total_events': len(all_events),
        'events': all_events,
        'interactions': interactions,
        'threads': [c['root_event'] for c in chains],
    }


def generate_cascade_chain(worlds: List[str] = None, seed: int = 42,
                           max_total: int = 20) -> Dict:
    """Generate a full cascade: one event in world A triggers world B triggers world C.
    
    Unlike multi_world_chain (which just concatenates), this models REAL cascading:
    - The LAST event of world A becomes the TRIGGER for world B
    - Severity escalates across world boundaries
    - Timing accumulates realistically
    """
    if worlds is None:
        worlds = random.Random(seed).sample(_ALL_WORLDS, 3)
    
    rng = random.Random(seed)
    cascade = []
    total_time = 0.0
    prev_trigger = None
    cross_world_edges = []
    
    for i, world in enumerate(worlds):
        dag = DAG_TEMPLATES.get(world, _GENERIC_DAG_PATTERNS)
        
        # Pick trigger: from previous world's last event, or random
        if prev_trigger and prev_trigger in dag:
            trigger = prev_trigger
        else:
            trigger = rng.choice(list(dag.keys()))
        
        chain = generate_event_chain(world, trigger=trigger, seed=seed + i * 200,
                                     max_depth=max_total // len(worlds))
        
        # Offset timestamps by accumulated time
        for event in chain['events']:
            event['timestamp_offset_s'] = round(event['timestamp_offset_s'] + total_time, 1)
            event['cascade_stage'] = i
            event['cascade_world'] = world
            cascade.append(event)
        
        # Cross-world edge
        if i > 0 and cascade:
            cross_world_edges.append({
                'from_world': worlds[i - 1],
                'to_world': world,
                'trigger_event': trigger,
                'time_offset': round(total_time, 1),
            })
        
        # Accumulate time + set next trigger
        if chain['events']:
            total_time += chain['events'][-1]['timestamp_offset_s'] + rng.uniform(30, 300)
            # Last event's type becomes potential trigger for next world
            prev_trigger = chain['events'][-1]['event_type']
    
    return {
        'chain_id': f'CASCADE-{seed:06d}',
        'worlds': worlds,
        'total_events': len(cascade),
        'total_time_s': round(total_time, 1),
        'events': cascade,
        'cross_world_edges': cross_world_edges,
        'cascade_depth': len(worlds),
    }


def predict_next_event(chain: Dict) -> Dict:
    """Given a partial chain, predict what happens next.
    
    Uses the DAG templates to find most likely next events.
    This is what Axima's reasoning engine calls at runtime.
    """
    if not chain.get('events'):
        return {'predictions': [], 'confidence': 0}
    
    last_event = chain['events'][-1]
    world = last_event.get('world', chain.get('world', ''))
    event_type = last_event['event_type']
    
    dag = DAG_TEMPLATES.get(world, _GENERIC_DAG_PATTERNS)
    
    if event_type not in dag:
        return {'predictions': [], 'confidence': 0, 'reason': 'terminal event (no successors)'}
    
    possible = dag[event_type]
    predictions = []
    for next_event, probability, delay, sev_change in possible:
        predictions.append({
            'event': next_event,
            'probability': probability,
            'expected_delay_s': delay,
            'severity_change': sev_change,
            'severity_direction': 'escalate' if sev_change > 0 else 'de-escalate' if sev_change < 0 else 'same',
        })
    
    predictions.sort(key=lambda p: -p['probability'])
    
    return {
        'current_event': event_type,
        'predictions': predictions,
        'confidence': max(p['probability'] for p in predictions) if predictions else 0,
        'world': world,
    }


def analyze_chain_risk(chain: Dict) -> Dict:
    """Analyze a chain for risk level, escalation speed, and intervention points.
    
    Returns recommendations for where to intervene to prevent escalation.
    """
    events = chain.get('events', [])
    if not events:
        return {'risk': 'none', 'score': 0}
    
    # Track severity over time
    severity_progression = []
    for e in events:
        sev_idx = SEVERITY_LEVELS.index(e.get('severity', 'info'))
        severity_progression.append(sev_idx)
    
    max_severity = max(severity_progression)
    avg_severity = sum(severity_progression) / len(severity_progression)
    
    # Escalation speed (how fast does severity increase?)
    escalation_rate = 0
    for i in range(1, len(severity_progression)):
        if severity_progression[i] > severity_progression[i - 1]:
            time_diff = events[i]['timestamp_offset_s'] - events[i - 1]['timestamp_offset_s']
            escalation_rate += 1 / max(time_diff, 1)
    
    # Find intervention points (where severity jumps)
    intervention_points = []
    for i in range(1, len(severity_progression)):
        if severity_progression[i] > severity_progression[i - 1]:
            intervention_points.append({
                'before_event': events[i]['event_type'],
                'at_sequence': i,
                'time_available_s': events[i]['timestamp_offset_s'] - events[i - 1]['timestamp_offset_s'],
                'would_prevent': [e['event_type'] for e in events[i:]],
            })
    
    # Risk score (0-100)
    risk_score = min(100, int(
        max_severity * 25 +
        avg_severity * 15 +
        escalation_rate * 20 +
        len(events) * 3
    ))
    
    risk_level = 'critical' if risk_score > 75 else 'high' if risk_score > 50 else 'medium' if risk_score > 25 else 'low'
    
    return {
        'risk_level': risk_level,
        'risk_score': risk_score,
        'max_severity': SEVERITY_LEVELS[max_severity],
        'escalation_rate': round(escalation_rate, 3),
        'intervention_points': intervention_points[:3],
        'total_events': len(events),
        'chain_duration_s': events[-1]['timestamp_offset_s'] if events else 0,
    }


def generate_training_batch(num_chains: int = 1000, seed: int = 42,
                            include_counterfactuals: bool = True) -> List[Dict]:
    """Generate a large batch of chains for AI training.
    
    Output format: each item has input (partial chain) + target (next events).
    Perfect for training Axima's causal prediction.
    """
    rng = random.Random(seed)
    batch = []
    worlds = list(DAG_TEMPLATES.keys())
    
    for i in range(num_chains):
        world = rng.choice(worlds)
        chain = generate_event_chain(world, seed=seed + i, max_depth=10)
        
        if len(chain['events']) < 3:
            continue
        
        # Create training pair: input = first N events, target = rest
        split_point = rng.randint(1, len(chain['events']) - 1)
        
        item = {
            'id': i,
            'world': world,
            'input_events': chain['events'][:split_point],
            'target_events': chain['events'][split_point:],
            'target_next': chain['events'][split_point]['event_type'],
            'chain_length': len(chain['events']),
        }
        
        # Add risk analysis
        item['risk'] = analyze_chain_risk(chain)
        
        # Add counterfactual
        if include_counterfactuals and rng.random() < 0.3:
            cf = generate_counterfactual(world, seed=seed + i + 5000, branch_point=split_point)
            item['counterfactual'] = cf['counterfactual_path']
        
        batch.append(item)
    
    return batch
