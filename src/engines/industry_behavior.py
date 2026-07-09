"""
Industry Behavior Engine
=========================
Moves from parameter differences to BEHAVIORAL differences.

Before this: industries differed in numbers (degradation rate, revenue).
After this: industries differ in HOW THINGS HAPPEN (causal chains, feedback loops).

Key concept: Each industry has CAUSAL CHAINS that define how one event
leads to another. These are NOT random — they follow the operational logic
of that specific industry.

Example (Agriculture):
  monsoon_starts → field_inaccessible → harvest_delayed →
  crop_moisture_rises → spoilage_probability_up → revenue_loss

Example (Automotive):
  supplier_delay → inventory_consumed → line_starvation →
  takt_disruption → overtime_authorized → fatigue_up → quality_escapes

These chains are what make generated episodes RECOGNIZABLY different
between industries — even without reading the industry label.
"""
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class CausalStep:
    """One step in a causal chain."""
    trigger_condition: str  # What activates this step
    state_changes: Dict[str, float]  # What changes in the world state
    next_steps: List[str]  # What this step can trigger next
    probability: float  # Chance this step fires (0-1)
    delay_events: int  # How many events before this manifests
    message_hints: List[str]  # Realistic messages for this step


@dataclass
class IndustryBehavior:
    """Complete behavioral model for one industry family."""
    industry_family: str
    causal_chains: Dict[str, List[CausalStep]]
    state_transitions: Dict[str, Dict[str, float]]  # state → {next_state: probability}
    feedback_loops: List[Dict]  # Circular causal relationships
    bottlenecks: List[str]  # Assets/processes that constrain throughput
    inventory_model: Dict[str, float]  # buffer_days, reorder_point, lead_time
    maintenance_policy: Dict[str, str]  # trigger → action
    regulatory_triggers: List[Dict]  # Conditions that trigger regulatory events
    supply_chain_model: Dict[str, float]  # supplier_count, lead_time, single_source_risk


# ═══════════════════════════════════════════════════════════════════
# AGRICULTURE BEHAVIOR
# ═══════════════════════════════════════════════════════════════════

AGRICULTURE_BEHAVIOR = IndustryBehavior(
    industry_family="agriculture",
    causal_chains={
        "monsoon_cascade": [
            CausalStep(
                trigger_condition="weather_event == heavy_rain AND duration > 2_days",
                state_changes={"field_accessibility": -0.8, "soil_moisture": +0.4},
                next_steps=["harvest_delay", "waterlogging"],
                probability=0.7, delay_events=3,
                message_hints=["fields are waterlogged, can't take machinery in",
                               "rain hasn't stopped for 3 days, crops standing in water"]
            ),
            CausalStep(
                trigger_condition="field_accessibility < 0.3",
                state_changes={"harvest_progress": -0.5, "crop_quality": -0.1},
                next_steps=["quality_degradation", "market_timing_miss"],
                probability=0.8, delay_events=5,
                message_hints=["harvest delayed by at least a week",
                               "grain moisture content rising, need to dry quickly"]
            ),
            CausalStep(
                trigger_condition="crop_quality < 0.7",
                state_changes={"spoilage_rate": +0.15, "market_price_achieved": -0.2},
                next_steps=["revenue_loss"],
                probability=0.6, delay_events=10,
                message_hints=["buyer rejected 30% of batch due to moisture",
                               "price dropped because grain quality is B-grade not A"]
            ),
        ],
        "irrigation_failure": [
            CausalStep(
                trigger_condition="equipment_health(pump) < 0.4",
                state_changes={"water_supply": -0.7, "crop_stress": +0.3},
                next_steps=["crop_wilting", "yield_reduction"],
                probability=0.8, delay_events=2,
                message_hints=["pump motor burned out, no water since yesterday",
                               "bore well pump not working, crops showing stress"]
            ),
            CausalStep(
                trigger_condition="crop_stress > 0.5 AND duration > 3_days",
                state_changes={"expected_yield": -0.25, "crop_health": -0.2},
                next_steps=["partial_crop_loss"],
                probability=0.7, delay_events=8,
                message_hints=["leaves turning yellow in 3 acres, no recovery likely",
                               "lost about 20% of paddy due to water stress"]
            ),
        ],
        "labor_shortage": [
            CausalStep(
                trigger_condition="season == harvest AND labor_available < 0.6",
                state_changes={"harvest_speed": -0.4, "labor_cost": +0.3},
                next_steps=["delayed_harvest", "overtime_cost"],
                probability=0.5, delay_events=1,
                message_hints=["only 6 workers showed up, needed 12 for today",
                               "laborers demanding double wages, harvest season pressure"]
            ),
        ],
    },
    state_transitions={
        "normal": {"normal": 0.85, "weather_disrupted": 0.08, "equipment_issue": 0.05, "labor_short": 0.02},
        "weather_disrupted": {"weather_disrupted": 0.6, "normal": 0.25, "crop_damage": 0.15},
        "equipment_issue": {"equipment_issue": 0.4, "normal": 0.5, "waiting_repair": 0.1},
        "labor_short": {"labor_short": 0.5, "normal": 0.4, "delayed_harvest": 0.1},
        "crop_damage": {"crop_damage": 0.3, "recovery": 0.4, "total_loss": 0.05, "normal": 0.25},
    },
    feedback_loops=[
        {"loop": "rain→waterlog→delay→moisture→spoilage→loss", "strength": 0.6, "duration_events": 30},
        {"loop": "pump_fail→stress→yield_loss→income_drop→cant_repair", "strength": 0.4, "duration_events": 50},
    ],
    bottlenecks=["irrigation_pump", "harvester_availability", "drying_capacity", "transport_to_market"],
    inventory_model={"buffer_days": 0, "reorder_point": 0, "lead_time_days": 0,
                     "spoilage_rate_per_day": 0.02, "storage_capacity_days": 30},
    maintenance_policy={"breakdown": "call_mechanic_or_rent",
                        "seasonal_prep": "service_before_planting",
                        "preventive": "rare_budget_limited"},
    regulatory_triggers=[
        {"condition": "pesticide_overuse", "action": "warning_or_fine", "probability": 0.05},
        {"condition": "water_extraction_excess", "action": "quota_enforcement", "probability": 0.1},
    ],
    supply_chain_model={"supplier_count": 3, "lead_time_days": 2, "single_source_risk": 0.2,
                        "seasonal_availability": True, "perishable_input": False},
)


# ═══════════════════════════════════════════════════════════════════
# OIL & GAS BEHAVIOR
# ═══════════════════════════════════════════════════════════════════

OIL_GAS_BEHAVIOR = IndustryBehavior(
    industry_family="oil_gas",
    causal_chains={
        "corrosion_cascade": [
            CausalStep(
                trigger_condition="equipment_health < 0.7 AND corrosion_accumulated > threshold",
                state_changes={"wall_thickness": -0.05, "leak_probability": +0.1},
                next_steps=["inspection_triggered", "leak_event"],
                probability=0.3, delay_events=20,
                message_hints=["UT readings show wall thinning on the 6-inch line",
                               "corrosion coupon results are concerning, rate 0.3mm/year"]
            ),
            CausalStep(
                trigger_condition="leak_probability > 0.3",
                state_changes={"maintenance_backlog": +1, "regulatory_scrutiny": +0.2},
                next_steps=["production_curtailment", "regulatory_action"],
                probability=0.4, delay_events=10,
                message_hints=["added to next turnaround scope, can't wait",
                               "integrity team recommends reducing operating pressure"]
            ),
            CausalStep(
                trigger_condition="maintenance_backlog > 5 AND regulatory_scrutiny > 0.5",
                state_changes={"production_rate": -0.15, "compliance_cost": +0.2},
                next_steps=["shutdown_decision"],
                probability=0.5, delay_events=15,
                message_hints=["regulator noticed our overdue inspection items",
                               "management authorized early shutdown for repairs"]
            ),
        ],
        "turnaround_cascade": [
            CausalStep(
                trigger_condition="months_since_turnaround > 48",
                state_changes={"efficiency_loss": +0.08, "risk_accumulation": +0.15},
                next_steps=["turnaround_planning", "efficiency_workaround"],
                probability=0.9, delay_events=50,
                message_hints=["fouling is getting worse, heat exchangers barely working",
                               "catalyst activity is down 15%, need to compensate with temperature"]
            ),
        ],
        "process_upset": [
            CausalStep(
                trigger_condition="temperature_deviation > 20C OR pressure_spike",
                state_changes={"product_quality": -0.2, "safety_risk": +0.3},
                next_steps=["flaring", "off_spec_product", "emergency_response"],
                probability=0.6, delay_events=1,
                message_hints=["reactor temperature spiking, reducing feed rate",
                               "off-spec product going to slop tank, can't send to storage"]
            ),
        ],
    },
    state_transitions={
        "normal": {"normal": 0.92, "degraded": 0.04, "upset": 0.02, "maintenance": 0.02},
        "degraded": {"degraded": 0.7, "normal": 0.15, "upset": 0.05, "maintenance": 0.1},
        "upset": {"upset": 0.3, "emergency": 0.1, "normal": 0.3, "degraded": 0.3},
        "maintenance": {"maintenance": 0.6, "normal": 0.35, "degraded": 0.05},
        "emergency": {"emergency": 0.2, "shutdown": 0.4, "degraded": 0.4},
        "shutdown": {"shutdown": 0.5, "startup": 0.5},
        "startup": {"startup": 0.3, "normal": 0.6, "degraded": 0.1},
    },
    feedback_loops=[
        {"loop": "corrosion→thinning→leak_risk→curtailment→revenue_loss", "strength": 0.7, "duration_events": 100},
        {"loop": "fouling→efficiency_drop→energy_cost_up→margin_squeeze→defer_turnaround→worse_fouling", "strength": 0.5, "duration_events": 200},
        {"loop": "upset→flaring→regulatory→production_limit→revenue_loss", "strength": 0.6, "duration_events": 50},
    ],
    bottlenecks=["compressor_capacity", "cooling_water", "hydrogen_supply", "catalyst_life"],
    inventory_model={"buffer_days": 5, "reorder_point": 0.3, "lead_time_days": 14,
                     "spoilage_rate_per_day": 0, "storage_capacity_days": 30},
    maintenance_policy={"turnaround": "every_4_5_years_planned",
                        "condition_based": "vibration_monitoring_rotating",
                        "risk_based": "inspection_program_api"},
    regulatory_triggers=[
        {"condition": "flaring_hours > limit", "action": "fine_or_curtailment", "probability": 0.3},
        {"condition": "emission_exceedance", "action": "mandatory_shutdown", "probability": 0.1},
        {"condition": "overdue_inspection", "action": "regulatory_order", "probability": 0.2},
    ],
    supply_chain_model={"supplier_count": 5, "lead_time_days": 30, "single_source_risk": 0.4,
                        "seasonal_availability": False, "perishable_input": False},
)


# ═══════════════════════════════════════════════════════════════════
# AUTOMOTIVE BEHAVIOR
# ═══════════════════════════════════════════════════════════════════

AUTOMOTIVE_BEHAVIOR = IndustryBehavior(
    industry_family="automotive",
    causal_chains={
        "supplier_cascade": [
            CausalStep(
                trigger_condition="supplier_delivery_late AND inventory_buffer < 4_hours",
                state_changes={"line_feed_status": -0.8, "inventory_hours": -2},
                next_steps=["line_starvation", "expedite_logistics"],
                probability=0.7, delay_events=2,
                message_hints=["wiring harness delivery didn't arrive, only 2 hours stock left",
                               "supplier truck broke down on highway, ETA unknown"]
            ),
            CausalStep(
                trigger_condition="line_feed_status < 0.3",
                state_changes={"line_speed": -1.0, "overtime_authorized": +1},
                next_steps=["line_stop", "makeup_production"],
                probability=0.9, delay_events=1,
                message_hints=["LINE STOP — no dashboard assemblies available",
                               "stopping the line at station 34, material shortage"]
            ),
            CausalStep(
                trigger_condition="line_speed == 0 AND duration > 2_hours",
                state_changes={"overtime_hours": +4, "fatigue_level": +0.2, "daily_output": -50},
                next_steps=["overtime_production", "quality_risk"],
                probability=0.8, delay_events=3,
                message_hints=["overtime approved to make up lost production",
                               "running Saturday shift to recover this week's target"]
            ),
            CausalStep(
                trigger_condition="fatigue_level > 0.7 AND overtime_hours > 3",
                state_changes={"defect_rate": +0.02, "quality_escape_risk": +0.15},
                next_steps=["quality_escape", "rework_increase"],
                probability=0.4, delay_events=5,
                message_hints=["quality finding at final inspection, torque not to spec",
                               "3 vehicles need rework from tonight's overtime run"]
            ),
        ],
        "paint_contamination": [
            CausalStep(
                trigger_condition="dust_particle_count > threshold OR filter_age > limit",
                state_changes={"paint_quality": -0.3, "rework_queue": +20},
                next_steps=["paint_rework", "booth_shutdown"],
                probability=0.3, delay_events=2,
                message_hints=["orange peel defects on 15 bodies, paint booth issue",
                               "contamination in booth 2, pulling bodies for re-spray"]
            ),
        ],
    },
    state_transitions={
        "normal": {"normal": 0.88, "material_wait": 0.05, "quality_issue": 0.03, "changeover": 0.04},
        "material_wait": {"material_wait": 0.4, "line_stop": 0.3, "normal": 0.3},
        "line_stop": {"line_stop": 0.3, "normal": 0.5, "overtime": 0.2},
        "overtime": {"overtime": 0.4, "normal": 0.4, "quality_issue": 0.2},
        "quality_issue": {"quality_issue": 0.3, "normal": 0.5, "rework": 0.2},
        "changeover": {"changeover": 0.3, "normal": 0.6, "startup_issues": 0.1},
    },
    feedback_loops=[
        {"loop": "supplier_late→line_stop→overtime→fatigue→defects→rework→more_overtime", "strength": 0.8, "duration_events": 20},
        {"loop": "quality_escape→recall_risk→cost→pressure→corner_cutting→more_escapes", "strength": 0.5, "duration_events": 50},
    ],
    bottlenecks=["paint_booth_throughput", "press_line_die_change", "supplier_single_source", "final_inspection"],
    inventory_model={"buffer_days": 0.2, "reorder_point": 0.8, "lead_time_days": 0.5,
                     "spoilage_rate_per_day": 0, "storage_capacity_days": 0.5},
    maintenance_policy={"preventive": "planned_weekend_windows",
                        "predictive": "vibration_on_critical_robots",
                        "die_maintenance": "every_N_strokes"},
    regulatory_triggers=[
        {"condition": "quality_escape_to_field", "action": "recall_investigation", "probability": 0.1},
        {"condition": "safety_incident_on_line", "action": "osha_visit", "probability": 0.05},
    ],
    supply_chain_model={"supplier_count": 300, "lead_time_days": 0.5, "single_source_risk": 0.7,
                        "seasonal_availability": False, "perishable_input": False},
)


# ═══════════════════════════════════════════════════════════════════
# HEALTHCARE BEHAVIOR
# ═══════════════════════════════════════════════════════════════════

HEALTHCARE_BEHAVIOR = IndustryBehavior(
    industry_family="healthcare",
    causal_chains={
        "patient_surge": [
            CausalStep(
                trigger_condition="bed_occupancy > 0.9 OR er_arrivals > capacity",
                state_changes={"nurse_workload": +0.3, "wait_time": +0.5},
                next_steps=["staff_fatigue", "diversion", "corridor_beds"],
                probability=0.6, delay_events=2,
                message_hints=["ER is overflowing, all bays occupied, patients in corridor",
                               "bed occupancy at 96%, no ICU beds available"]
            ),
            CausalStep(
                trigger_condition="nurse_workload > 0.85",
                state_changes={"fatigue_level": +0.25, "error_probability": +0.1},
                next_steps=["medication_error_risk", "documentation_gap"],
                probability=0.5, delay_events=4,
                message_hints=["nurse handling 8 patients instead of standard 4",
                               "haven't had a break in 6 hours, running between beds"]
            ),
            CausalStep(
                trigger_condition="error_probability > 0.15 AND fatigue > 0.7",
                state_changes={"adverse_event_risk": +0.2, "patient_outcome_quality": -0.1},
                next_steps=["near_miss", "adverse_event"],
                probability=0.3, delay_events=3,
                message_hints=["near miss — wrong dose almost administered, caught by pharmacist",
                               "incident report filed: delayed medication round by 2 hours"]
            ),
        ],
        "equipment_critical": [
            CausalStep(
                trigger_condition="ventilator_health < 0.5 OR monitor_failure",
                state_changes={"patient_safety_risk": +0.5, "manual_monitoring": +1},
                next_steps=["backup_activation", "patient_transfer"],
                probability=0.7, delay_events=1,
                message_hints=["ventilator alarm — switching to backup unit",
                               "cardiac monitor black screen in bed 7, manual vitals until fixed"]
            ),
        ],
    },
    state_transitions={
        "normal": {"normal": 0.80, "busy": 0.12, "surge": 0.03, "understaffed": 0.05},
        "busy": {"busy": 0.5, "normal": 0.3, "surge": 0.1, "understaffed": 0.1},
        "surge": {"surge": 0.4, "busy": 0.3, "crisis": 0.1, "normal": 0.2},
        "understaffed": {"understaffed": 0.5, "normal": 0.3, "busy": 0.15, "crisis": 0.05},
        "crisis": {"crisis": 0.3, "surge": 0.4, "normal": 0.1, "recovery": 0.2},
    },
    feedback_loops=[
        {"loop": "surge→overwork→fatigue→errors→incidents→staff_leave→more_shortage", "strength": 0.7, "duration_events": 30},
        {"loop": "equipment_fail→manual_care→workload_up→fatigue→more_errors", "strength": 0.5, "duration_events": 15},
    ],
    bottlenecks=["icu_beds", "or_slots", "specialist_availability", "blood_supply", "pharmacy_turnaround"],
    inventory_model={"buffer_days": 3, "reorder_point": 0.5, "lead_time_days": 1,
                     "spoilage_rate_per_day": 0.01, "storage_capacity_days": 14},
    maintenance_policy={"life_critical": "immediate_redundancy_switch",
                        "preventive": "scheduled_biomedical_rounds",
                        "calibration": "annual_or_usage_based"},
    regulatory_triggers=[
        {"condition": "adverse_event_reported", "action": "root_cause_analysis_mandatory", "probability": 0.9},
        {"condition": "infection_rate_above_threshold", "action": "audit_and_intervention", "probability": 0.3},
        {"condition": "staffing_below_ratio", "action": "regulatory_warning", "probability": 0.2},
    ],
    supply_chain_model={"supplier_count": 20, "lead_time_days": 2, "single_source_risk": 0.3,
                        "seasonal_availability": False, "perishable_input": True},
)


# ═══════════════════════════════════════════════════════════════════
# STEEL BEHAVIOR
# ═══════════════════════════════════════════════════════════════════

STEEL_BEHAVIOR = IndustryBehavior(
    industry_family="steel",
    causal_chains={
        "thermal_degradation": [
            CausalStep(
                trigger_condition="furnace_campaigns > 3_years AND refractory_wear > 0.6",
                state_changes={"energy_intensity": +0.08, "heat_loss": +0.1},
                next_steps=["efficiency_decline", "reline_planning"],
                probability=0.7, delay_events=30,
                message_hints=["shell temperature readings rising, refractory wearing thin",
                               "energy consumption up 8% from last quarter, furnace aging"]
            ),
            CausalStep(
                trigger_condition="energy_intensity > baseline + 15%",
                state_changes={"production_cost": +0.12, "margin_pressure": +0.15},
                next_steps=["cost_pressure", "shutdown_planning"],
                probability=0.8, delay_events=20,
                message_hints=["coke rate has increased to 380 kg/ton, target was 340",
                               "management reviewing shutdown timeline, costs are escalating"]
            ),
            CausalStep(
                trigger_condition="margin_pressure > 0.5 AND refractory_wear > 0.8",
                state_changes={"shutdown_decision": 1.0, "production_rate": -1.0},
                next_steps=["major_reline"],
                probability=0.9, delay_events=10,
                message_hints=["blast furnace reline approved, 4-month shutdown starting next month",
                               "entire hot metal section going down for capital repair"]
            ),
        ],
        "raw_material_quality": [
            CausalStep(
                trigger_condition="iron_ore_grade < spec OR coke_strength < threshold",
                state_changes={"slag_volume": +0.2, "hot_metal_quality": -0.1},
                next_steps=["steelmaking_adjustment", "quality_issue"],
                probability=0.5, delay_events=5,
                message_hints=["ore quality from new supplier is lower alumina, adjusting burden",
                               "coke strength dropped, expecting higher coke rate this week"]
            ),
        ],
    },
    state_transitions={
        "normal": {"normal": 0.90, "degraded": 0.05, "quality_issue": 0.03, "supply_issue": 0.02},
        "degraded": {"degraded": 0.6, "normal": 0.2, "maintenance": 0.15, "emergency": 0.05},
        "quality_issue": {"quality_issue": 0.4, "normal": 0.4, "degraded": 0.2},
        "maintenance": {"maintenance": 0.5, "normal": 0.4, "startup": 0.1},
        "emergency": {"emergency": 0.2, "shutdown": 0.5, "maintenance": 0.3},
    },
    feedback_loops=[
        {"loop": "refractory_wear→heat_loss→energy_up→cost_up→defer_reline→more_wear", "strength": 0.6, "duration_events": 150},
        {"loop": "ore_quality_down→slag_up→productivity_down→cost_up→cheaper_ore→worse_quality", "strength": 0.4, "duration_events": 80},
    ],
    bottlenecks=["blast_furnace_capacity", "caster_sequence", "rolling_mill_schedule", "ladle_availability"],
    inventory_model={"buffer_days": 14, "reorder_point": 0.4, "lead_time_days": 30,
                     "spoilage_rate_per_day": 0, "storage_capacity_days": 45},
    maintenance_policy={"blast_furnace": "campaign_based_4_5_years",
                        "rolling_mill": "condition_based_vibration",
                        "refractory": "remaining_life_monitoring"},
    regulatory_triggers=[
        {"condition": "emission_limit_exceeded", "action": "production_curtailment", "probability": 0.2},
        {"condition": "slag_disposal_non_compliant", "action": "fine_and_remediation", "probability": 0.1},
    ],
    supply_chain_model={"supplier_count": 5, "lead_time_days": 45, "single_source_risk": 0.5,
                        "seasonal_availability": False, "perishable_input": False},
)


# ═══════════════════════════════════════════════════════════════════
# BEHAVIOR REGISTRY
# ═══════════════════════════════════════════════════════════════════

INDUSTRY_BEHAVIORS: Dict[str, IndustryBehavior] = {
    # Agriculture family
    "rice_farming": AGRICULTURE_BEHAVIOR,
    "wheat_farming": AGRICULTURE_BEHAVIOR,
    "sugarcane_farming": AGRICULTURE_BEHAVIOR,
    "poultry_farming": AGRICULTURE_BEHAVIOR,
    "dairy_farming": AGRICULTURE_BEHAVIOR,
    # Oil & Gas family
    "oil_refining": OIL_GAS_BEHAVIOR,
    "offshore_oil_drilling": OIL_GAS_BEHAVIOR,
    # Automotive family
    "automobile_assembly": AUTOMOTIVE_BEHAVIOR,
    # Healthcare family
    "hospital": HEALTHCARE_BEHAVIOR,
    # Steel family
    "steel_rolling": STEEL_BEHAVIOR,
    "cement_manufacturing": STEEL_BEHAVIOR,  # Similar continuous process behavior
}


def get_industry_behavior(industry_id: str) -> Optional[IndustryBehavior]:
    """Get behavior model for an industry. Returns None if not profiled."""
    return INDUSTRY_BEHAVIORS.get(industry_id)


def get_active_causal_chain(behavior: IndustryBehavior, 
                            current_state: Dict, rng: random.Random) -> Optional[Tuple[str, CausalStep]]:
    """Check if any causal chain should activate given current state."""
    for chain_name, steps in behavior.causal_chains.items():
        for step in steps:
            if rng.random() < step.probability * 0.1:  # Low base rate per tick
                return chain_name, step
    return None



# ═══════════════════════════════════════════════════════════════════
# ADDITIONAL INDUSTRY BEHAVIORS (expanding from 37% to 80%+ coverage)
# ═══════════════════════════════════════════════════════════════════

# ─── MINING ────────────────────────────────────────────────

MINING_BEHAVIOR = IndustryBehavior(
    industry_family="mining",
    causal_chains={
        "ground_stability": [
            CausalStep("vibration_from_blasting > threshold", {"ground_stability": -0.3, "crack_risk": +0.2},
                      ["roof_collapse_risk", "wall_failure"], 0.3, 15,
                      ["ground monitoring shows movement after yesterday's blast",
                       "crack widening in pit wall, survey team dispatched"]),
            CausalStep("crack_risk > 0.5", {"production_halt": 1.0, "safety_alert": 1.0},
                      ["evacuation", "remediation"], 0.5, 5,
                      ["STOP WORK — ground control issue in sector 7",
                       "all personnel evacuated from lower bench"]),
        ],
        "equipment_overload": [
            CausalStep("haul_truck_utilization > 0.95", {"breakdown_probability": +0.3, "tire_wear": +0.2},
                      ["truck_breakdown", "production_bottleneck"], 0.4, 10,
                      ["trucks running double shifts, no maintenance window",
                       "third tire blowout this week, push-back on overloading"]),
        ],
    },
    state_transitions={
        "normal": {"normal": 0.85, "weather_stop": 0.05, "equipment_issue": 0.05, "ground_concern": 0.05},
        "weather_stop": {"weather_stop": 0.5, "normal": 0.4, "delayed": 0.1},
        "equipment_issue": {"equipment_issue": 0.4, "normal": 0.5, "production_loss": 0.1},
        "ground_concern": {"ground_concern": 0.3, "normal": 0.4, "evacuation": 0.1, "remediation": 0.2},
    },
    feedback_loops=[
        {"loop": "overloading→breakdown→backlog→more_overloading", "strength": 0.5, "duration_events": 40},
    ],
    bottlenecks=["crusher_throughput", "haul_road_capacity", "drill_availability", "explosive_supply"],
    inventory_model={"buffer_days": 7, "reorder_point": 0.4, "lead_time_days": 14,
                     "spoilage_rate_per_day": 0, "storage_capacity_days": 30},
    maintenance_policy={"haul_trucks": "scheduled_pm_500_hours",
                        "crushers": "condition_monitoring_vibration",
                        "drills": "usage_based"},
    regulatory_triggers=[
        {"condition": "dust_level_exceeded", "action": "production_halt", "probability": 0.15},
        {"condition": "tailings_dam_concern", "action": "regulatory_inspection", "probability": 0.1},
    ],
    supply_chain_model={"supplier_count": 5, "lead_time_days": 21, "single_source_risk": 0.4,
                        "seasonal_availability": False, "perishable_input": False},
)

# ─── LOGISTICS & WAREHOUSING ─────────────────────────────

LOGISTICS_BEHAVIOR = IndustryBehavior(
    industry_family="logistics",
    causal_chains={
        "capacity_crunch": [
            CausalStep("warehouse_utilization > 0.92", {"receiving_speed": -0.4, "errors": +0.2},
                      ["overflow_storage", "dispatch_delay"], 0.5, 3,
                      ["warehouse at 95%, incoming trucks waiting at dock",
                       "no put-away slots available, using overflow area"]),
            CausalStep("dispatch_delay > 0.3", {"customer_complaints": +0.4, "sla_breach": +0.2},
                      ["penalty_cost", "customer_escalation"], 0.6, 5,
                      ["3 shipments missed cut-off, customer escalating",
                       "SLA penalty triggered for late deliveries this week"]),
        ],
        "peak_season_strain": [
            CausalStep("order_volume > 1.5x_normal", {"overtime_required": 1.0, "temp_staff": +0.3},
                      ["fatigue_spike", "error_increase"], 0.7, 2,
                      ["festival season orders 2x normal, authorizing overtime",
                       "hiring 30 temporary pickers for this month"]),
        ],
    },
    state_transitions={
        "normal": {"normal": 0.80, "busy": 0.12, "capacity_strain": 0.05, "understaffed": 0.03},
        "busy": {"busy": 0.5, "normal": 0.3, "capacity_strain": 0.15, "overtime": 0.05},
        "capacity_strain": {"capacity_strain": 0.4, "busy": 0.3, "normal": 0.2, "overflow": 0.1},
        "understaffed": {"understaffed": 0.4, "normal": 0.4, "busy": 0.1, "overtime": 0.1},
    },
    feedback_loops=[
        {"loop": "volume_spike→overtime→fatigue→errors→rework→more_overtime", "strength": 0.6, "duration_events": 25},
    ],
    bottlenecks=["dock_door_capacity", "put_away_speed", "picker_availability", "truck_slots"],
    inventory_model={"buffer_days": 2, "reorder_point": 0.6, "lead_time_days": 1,
                     "spoilage_rate_per_day": 0.005, "storage_capacity_days": 14},
    maintenance_policy={"forklifts": "daily_check_weekly_pm",
                        "conveyors": "condition_monitoring",
                        "it_systems": "monthly_patching"},
    regulatory_triggers=[
        {"condition": "overweight_shipment", "action": "fine", "probability": 0.05},
        {"condition": "safety_incident_on_dock", "action": "investigation", "probability": 0.1},
    ],
    supply_chain_model={"supplier_count": 50, "lead_time_days": 0.5, "single_source_risk": 0.1,
                        "seasonal_availability": True, "perishable_input": True},
)

# ─── POWER GENERATION ────────────────────────────────────

POWER_BEHAVIOR = IndustryBehavior(
    industry_family="power_generation",
    causal_chains={
        "boiler_tube_failure": [
            CausalStep("tube_wall_thinning > limit AND steam_temp_high", 
                      {"tube_leak_risk": +0.4, "efficiency": -0.05},
                      ["forced_outage", "load_reduction"], 0.3, 20,
                      ["boiler tube inspection shows thinning in superheater",
                       "steam leak detected in economizer, reducing load"]),
            CausalStep("tube_leak_occurred", {"unit_trip": 1.0, "grid_impact": +0.3},
                      ["emergency_repair", "power_purchase"], 0.7, 2,
                      ["UNIT TRIP — boiler tube leak, emergency cooldown initiated",
                       "buying 200MW from grid to cover shortfall"]),
        ],
        "coal_quality_issue": [
            CausalStep("coal_calorific_value < spec", {"combustion_efficiency": -0.1, "ash_generation": +0.2},
                      ["derating", "ash_handling_overload"], 0.5, 5,
                      ["coal from new supplier has higher ash content",
                       "mill output reduced due to hard grinding characteristics"]),
        ],
    },
    state_transitions={
        "normal": {"normal": 0.90, "degraded": 0.05, "maintenance": 0.03, "startup": 0.02},
        "degraded": {"degraded": 0.5, "normal": 0.25, "maintenance": 0.15, "trip": 0.1},
        "trip": {"trip": 0.2, "shutdown": 0.5, "startup": 0.3},
        "maintenance": {"maintenance": 0.5, "startup": 0.4, "normal": 0.1},
        "startup": {"startup": 0.3, "normal": 0.6, "degraded": 0.1},
    },
    feedback_loops=[
        {"loop": "fouling→efficiency_drop→overfire→tube_damage→trip", "strength": 0.5, "duration_events": 100},
    ],
    bottlenecks=["coal_supply", "cooling_water", "grid_dispatch_order", "ash_disposal"],
    inventory_model={"buffer_days": 21, "reorder_point": 0.5, "lead_time_days": 14,
                     "spoilage_rate_per_day": 0, "storage_capacity_days": 45},
    maintenance_policy={"overhaul": "annual_planned_outage",
                        "condition_based": "vibration_oil_analysis",
                        "predictive": "thermal_imaging_tubes"},
    regulatory_triggers=[
        {"condition": "emission_exceedance", "action": "load_curtailment", "probability": 0.2},
        {"condition": "grid_frequency_deviation", "action": "automatic_response", "probability": 0.3},
    ],
    supply_chain_model={"supplier_count": 3, "lead_time_days": 30, "single_source_risk": 0.5,
                        "seasonal_availability": False, "perishable_input": False},
)

# ─── FOOD PROCESSING ─────────────────────────────────────

FOOD_PROCESSING_BEHAVIOR = IndustryBehavior(
    industry_family="food_processing",
    causal_chains={
        "contamination_event": [
            CausalStep("hygiene_breach OR pest_detection", {"batch_risk": +0.5, "line_stop": 0.8},
                      ["batch_quarantine", "deep_clean"], 0.4, 2,
                      ["pest activity detected near packaging area",
                       "CCP failure at metal detector, batch held"]),
            CausalStep("batch_quarantined", {"production_loss": +0.2, "investigation": 1.0},
                      ["product_recall_risk", "regulatory_notification"], 0.3, 5,
                      ["lab results pending on quarantined batch",
                       "notifying food safety authority as precaution"]),
        ],
        "seasonal_raw_material": [
            CausalStep("harvest_season_ended AND stock_declining", {"raw_material_cost": +0.3, "availability": -0.4},
                      ["production_curtailment", "alternate_sourcing"], 0.6, 10,
                      ["tomato season ending, cold storage stock down to 2 weeks",
                       "sourcing from alternate region at 30% premium"]),
        ],
    },
    state_transitions={
        "normal": {"normal": 0.82, "changeover": 0.08, "quality_hold": 0.05, "supply_issue": 0.05},
        "changeover": {"changeover": 0.3, "normal": 0.6, "startup_issues": 0.1},
        "quality_hold": {"quality_hold": 0.4, "normal": 0.4, "recall_risk": 0.1, "investigation": 0.1},
        "supply_issue": {"supply_issue": 0.5, "normal": 0.3, "curtailed": 0.2},
    },
    feedback_loops=[
        {"loop": "contamination→recall→reputation→demand_drop→revenue_loss", "strength": 0.7, "duration_events": 50},
    ],
    bottlenecks=["pasteurizer_throughput", "cold_storage_capacity", "packaging_line_speed", "lab_testing_turnaround"],
    inventory_model={"buffer_days": 3, "reorder_point": 0.6, "lead_time_days": 2,
                     "spoilage_rate_per_day": 0.03, "storage_capacity_days": 7},
    maintenance_policy={"cip_wash": "between_every_batch",
                        "preventive": "weekly_planned",
                        "hygiene_audit": "daily_and_unannounced"},
    regulatory_triggers=[
        {"condition": "pathogen_detected", "action": "mandatory_recall", "probability": 0.8},
        {"condition": "labeling_non_compliance", "action": "fine_and_correction", "probability": 0.2},
    ],
    supply_chain_model={"supplier_count": 10, "lead_time_days": 3, "single_source_risk": 0.3,
                        "seasonal_availability": True, "perishable_input": True},
)

# ─── CONSTRUCTION ─────────────────────────────────────────

CONSTRUCTION_BEHAVIOR = IndustryBehavior(
    industry_family="construction",
    causal_chains={
        "weather_delay": [
            CausalStep("rain_days > 3 OR temperature < 5C", {"work_progress": -0.6, "concrete_curing": -0.5},
                      ["schedule_slip", "cost_overrun"], 0.6, 5,
                      ["rain for 4th consecutive day, no earthwork possible",
                       "concrete pour cancelled, temperature too low for curing"]),
            CausalStep("schedule_slip > 10%", {"penalty_risk": +0.3, "overtime_needed": 1.0},
                      ["acceleration_plan", "subcontractor_pressure"], 0.7, 10,
                      ["project 2 weeks behind, acceleration plan being prepared",
                       "LD penalty clause activates in 15 days"]),
        ],
        "labor_accident": [
            CausalStep("working_at_height AND safety_violation", {"injury_probability": +0.4},
                      ["work_stoppage", "investigation"], 0.2, 1,
                      ["fall from scaffolding at level 3, ambulance called",
                       "STOP WORK on all height activities pending investigation"]),
        ],
    },
    state_transitions={
        "normal": {"normal": 0.75, "weather_stop": 0.10, "material_wait": 0.08, "safety_stop": 0.02, "rework": 0.05},
        "weather_stop": {"weather_stop": 0.5, "normal": 0.4, "delayed": 0.1},
        "material_wait": {"material_wait": 0.4, "normal": 0.5, "delayed": 0.1},
        "delayed": {"delayed": 0.5, "normal": 0.3, "acceleration": 0.2},
    },
    feedback_loops=[
        {"loop": "delay→acceleration→overtime→fatigue→accidents→more_delay", "strength": 0.6, "duration_events": 30},
    ],
    bottlenecks=["crane_availability", "concrete_supply", "skilled_labor", "permit_approvals"],
    inventory_model={"buffer_days": 3, "reorder_point": 0.5, "lead_time_days": 7,
                     "spoilage_rate_per_day": 0.01, "storage_capacity_days": 14},
    maintenance_policy={"cranes": "daily_inspection_monthly_pm",
                        "scaffolding": "weekly_inspection",
                        "equipment": "operator_daily_check"},
    regulatory_triggers=[
        {"condition": "safety_incident", "action": "stop_work_order", "probability": 0.3},
        {"condition": "noise_complaint", "action": "restricted_hours", "probability": 0.1},
    ],
    supply_chain_model={"supplier_count": 20, "lead_time_days": 7, "single_source_risk": 0.3,
                        "seasonal_availability": True, "perishable_input": True},
)

# ─── PHARMACEUTICALS ──────────────────────────────────────

PHARMA_BEHAVIOR = IndustryBehavior(
    industry_family="pharmaceutical",
    causal_chains={
        "batch_deviation": [
            CausalStep("process_parameter_out_of_spec", {"batch_status": -0.5, "investigation": 1.0},
                      ["batch_quarantine", "deviation_investigation"], 0.4, 3,
                      ["tablet hardness below specification at in-process check",
                       "deviation report initiated — blend uniformity suspect"]),
            CausalStep("investigation_ongoing", {"production_capacity": -0.2, "qa_workload": +0.4},
                      ["batch_release_delay", "supply_shortage"], 0.6, 10,
                      ["3 batches in quarantine pending investigation closure",
                       "QA team working overtime to close CAPAs before audit"]),
        ],
        "regulatory_audit": [
            CausalStep("audit_scheduled OR surprise_inspection", {"compliance_pressure": +0.5},
                      ["documentation_scramble", "finding_remediation"], 0.5, 2,
                      ["FDA pre-approval inspection scheduled next month",
                       "mock audit found 3 documentation gaps, urgent remediation"]),
        ],
    },
    state_transitions={
        "normal": {"normal": 0.80, "changeover": 0.10, "deviation": 0.05, "audit_prep": 0.03, "supply_issue": 0.02},
        "changeover": {"changeover": 0.3, "normal": 0.6, "cleaning_issue": 0.1},
        "deviation": {"deviation": 0.4, "normal": 0.3, "investigation": 0.3},
        "investigation": {"investigation": 0.5, "normal": 0.3, "capa_implementation": 0.2},
    },
    feedback_loops=[
        {"loop": "deviation→investigation→batch_hold→supply_shortage→pressure→shortcuts→more_deviations", "strength": 0.5, "duration_events": 40},
    ],
    bottlenecks=["qa_release_capacity", "stability_chamber_space", "clean_room_availability", "api_supply"],
    inventory_model={"buffer_days": 30, "reorder_point": 0.5, "lead_time_days": 60,
                     "spoilage_rate_per_day": 0.001, "storage_capacity_days": 180},
    maintenance_policy={"cleanroom_hvac": "continuous_monitoring_monthly_pm",
                        "equipment": "validated_pm_schedule",
                        "calibration": "annual_traceable"},
    regulatory_triggers=[
        {"condition": "repeat_deviation", "action": "warning_letter_risk", "probability": 0.2},
        {"condition": "data_integrity_issue", "action": "form_483", "probability": 0.5},
    ],
    supply_chain_model={"supplier_count": 3, "lead_time_days": 60, "single_source_risk": 0.6,
                        "seasonal_availability": False, "perishable_input": False},
)

# ─── ELECTRONICS / SEMICONDUCTOR ─────────────────────────

ELECTRONICS_BEHAVIOR = IndustryBehavior(
    industry_family="electronics",
    causal_chains={
        "yield_excursion": [
            CausalStep("defect_density_spike OR process_drift", {"yield": -0.15, "scrap_cost": +0.3},
                      ["root_cause_analysis", "production_hold"], 0.4, 3,
                      ["yield dropped from 92% to 78% on lot 2847",
                       "SPC chart shows drift in etch rate, holding production"]),
        ],
        "supply_chain_shock": [
            CausalStep("component_shortage OR supplier_force_majeure", {"production_capacity": -0.4},
                      ["line_stop", "redesign_effort"], 0.3, 7,
                      ["critical IC shortage — supplier fab had fire",
                       "no allocation for next 8 weeks on this component"]),
        ],
    },
    state_transitions={
        "normal": {"normal": 0.85, "yield_issue": 0.05, "supply_short": 0.05, "changeover": 0.05},
        "yield_issue": {"yield_issue": 0.4, "normal": 0.4, "investigation": 0.2},
        "supply_short": {"supply_short": 0.5, "normal": 0.3, "redesign": 0.2},
    },
    feedback_loops=[
        {"loop": "yield_drop→scrap→cost_pressure→defer_pm→more_drift→worse_yield", "strength": 0.5, "duration_events": 30},
    ],
    bottlenecks=["clean_room_capacity", "test_equipment", "component_lead_times", "npi_resources"],
    inventory_model={"buffer_days": 14, "reorder_point": 0.6, "lead_time_days": 30,
                     "spoilage_rate_per_day": 0, "storage_capacity_days": 60},
    maintenance_policy={"smt_machines": "condition_based_daily_check",
                        "reflow_ovens": "weekly_profiling",
                        "aoi_calibration": "shift_start"},
    regulatory_triggers=[
        {"condition": "rohs_non_compliance", "action": "shipment_hold", "probability": 0.1},
    ],
    supply_chain_model={"supplier_count": 50, "lead_time_days": 45, "single_source_risk": 0.5,
                        "seasonal_availability": False, "perishable_input": False},
)


# ═══════════════════════════════════════════════════════════
# EXPANDED REGISTRY — Map more industries to behaviors
# ═══════════════════════════════════════════════════════════

# Mining family
for mid in ["coal_mining", "iron_ore_mining"]:
    INDUSTRY_BEHAVIORS[mid] = MINING_BEHAVIOR

# Logistics family
for lid in ["logistics_warehouse", "supermarket_retail"]:
    INDUSTRY_BEHAVIORS[lid] = LOGISTICS_BEHAVIOR

# Power generation family
for pid in ["thermal_power_plant", "solar_farm"]:
    INDUSTRY_BEHAVIORS[pid] = POWER_BEHAVIOR

# Food processing family
for fid in ["rice_milling", "sugar_milling", "restaurant_kitchen"]:
    INDUSTRY_BEHAVIORS[fid] = FOOD_PROCESSING_BEHAVIOR

# Construction family
INDUSTRY_BEHAVIORS["road_construction"] = CONSTRUCTION_BEHAVIOR

# Pharmaceuticals family
INDUSTRY_BEHAVIORS["pharmaceutical_tablet"] = PHARMA_BEHAVIOR
INDUSTRY_BEHAVIORS["vaccine_manufacturing"] = PHARMA_BEHAVIOR

# Electronics family
for eid in ["electronics_pcb", "semiconductor_fab"]:
    INDUSTRY_BEHAVIORS[eid] = ELECTRONICS_BEHAVIOR

# Software/IT (simple behavior — mostly human/process driven)
INDUSTRY_BEHAVIORS["software_company"] = LOGISTICS_BEHAVIOR  # Similar capacity/demand dynamics
INDUSTRY_BEHAVIORS["data_center"] = POWER_BEHAVIOR  # Similar continuous operation + trip risk

# Textile (similar to food processing — batch, quality, seasonal)
INDUSTRY_BEHAVIORS["cotton_spinning"] = FOOD_PROCESSING_BEHAVIOR
INDUSTRY_BEHAVIORS["leather_tanning"] = FOOD_PROCESSING_BEHAVIOR

# Cement (similar to steel — continuous, thermal, energy)
INDUSTRY_BEHAVIORS["cement_manufacturing"] = STEEL_BEHAVIOR

# Livestock (similar to agriculture + continuous)
for aid in ["poultry_farming", "dairy_farming", "shrimp_farming"]:
    INDUSTRY_BEHAVIORS[aid] = AGRICULTURE_BEHAVIOR
