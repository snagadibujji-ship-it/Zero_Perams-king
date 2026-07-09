"""
Industry-Specific Simulation Parameters
=========================================
Converts encyclopedia knowledge into executable simulation parameters.

Each industry profile drives:
- DegradationEngine: how fast equipment wears, what causes accelerated degradation
- FatigueEngine: shift patterns, peak hours, recovery behavior
- EnvironmentEngine: which environmental factors matter most
- EconomicsEngine: cost structure, downtime cost, revenue model
- CascadingFailureEngine: what failures propagate and how
- StateTracker: overall state transition probabilities

These are NOT documentation. They are EXECUTABLE PARAMETERS consumed by
the simulation engines at runtime.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


@dataclass
class ShiftProfile:
    """How workers operate in time."""
    shift_type: str  # "continuous_24_7", "two_shift", "three_shift", "daylight_only", "seasonal", "split_shift"
    shift_duration_hours: float  # 8, 10, 12
    shifts_per_day: int  # 1, 2, 3
    active_days_per_week: int  # 5, 6, 7
    peak_hours: List[int]  # Hours of highest activity [6,7,8,9,10]
    dead_hours: List[int]  # Hours of minimal activity [1,2,3,4]
    seasonal_shutdown_weeks: int  # 0 (never) to 4 (summer/winter breaks)
    night_activity_level: float  # 0.0 (dead) to 1.0 (same as day)
    handover_overlap_minutes: int  # 0 to 60


@dataclass
class DegradationProfile:
    """How equipment wears in this industry."""
    base_degradation_rate: float  # Per-event health loss (0.0001 to 0.01)
    degradation_variance: float  # Random multiplier range (0.3 to 2.0)
    maintenance_recovery: float  # Health restored by PM (0.05 to 0.20)
    catastrophic_failure_prob: float  # Per-event chance of sudden failure (0.0001 to 0.005)
    thermal_stress_factor: float  # How much temperature accelerates wear (0 to 2.0)
    corrosion_factor: float  # Humidity/chemical corrosion rate multiplier (0 to 3.0)
    vibration_sensitivity: float  # How fast vibration grows with degradation (0.3 to 2.0)
    typical_rul_hours: float  # Expected life between major overhauls (500 to 50000)
    maintenance_interval_events: int  # How often PM occurs (50 to 5000)


@dataclass
class EnvironmentProfile:
    """Which environmental factors matter most for this industry."""
    temperature_sensitivity: float  # 0 (indoor climate-controlled) to 2.0 (outdoor exposed)
    humidity_sensitivity: float  # 0 (dry processes) to 2.0 (corrosion-sensitive)
    rain_stop_probability: float  # Chance that rain halts operations (0 to 0.9)
    wind_sensitivity: float  # 0 (enclosed) to 1.0 (crane/outdoor work)
    dust_sensitivity: float  # 0 (cleanroom) to 1.0 (open-air mining)
    power_grid_dependency: float  # 0 (off-grid) to 1.0 (totally grid-dependent)
    seasonal_demand_amplitude: float  # 0 (flat demand) to 1.0 (extreme seasonal swing)
    monsoon_impact: float  # 0 (not affected) to 1.0 (operations halt in monsoon)


@dataclass
class EconomicProfile:
    """Cost structure and business dynamics for this industry."""
    revenue_per_hour_usd: float  # Hourly revenue when operating (100 to 100000)
    downtime_cost_multiplier: float  # How much MORE downtime costs vs lost revenue (1.0 to 3.0)
    material_cost_pct: float  # Materials as % of total cost (0.10 to 0.70)
    energy_cost_pct: float  # Energy as % of total cost (0.02 to 0.35)
    labor_cost_pct: float  # Labor as % of total cost (0.05 to 0.60)
    inventory_sensitivity: float  # How fast stockouts cause problems (0 to 1.0)
    sla_penalty_severity: float  # Financial penalty for late delivery (0 to 1.0)
    demand_volatility: float  # How much demand fluctuates (0 to 1.0)
    industry_scale: str  # "small", "medium", "large" (drives base revenue)


@dataclass
class CascadeProfile:
    """What failures cascade and how in this industry."""
    cascade_probability: float  # Base chance that a failure triggers downstream (0.1 to 0.6)
    cascade_delay_events: Tuple[int, int]  # (min_delay, max_delay) events before cascade manifests
    primary_cascade_types: List[str]  # ["supply_stop", "quality_degradation", "safety_risk"]
    supplier_dependency: float  # How vulnerable to supplier disruption (0 to 1.0)
    single_point_failures: List[str]  # Assets that stop everything if they fail
    recovery_time_events: Tuple[int, int]  # (min, max) events to recover from major failure


@dataclass
class FatigueProfile:
    """How human performance degrades in this industry."""
    peak_alertness_hour: int  # Hour into shift when performance peaks (1-4)
    post_lunch_dip: float  # Alertness drop after lunch (0 to 0.3)
    night_shift_penalty: float  # Performance reduction at night (0.05 to 0.30)
    overtime_threshold_hours: float  # Hours after which overtime fatigue kicks in (8 to 12)
    overtime_error_multiplier: float  # How much more errors in overtime (1.5 to 3.0)
    physical_labor_fatigue_rate: float  # How fast physical workers tire (0.01 to 0.05/hour)
    monitoring_vigilance_decay: float  # How fast attention drops in monitoring tasks (0.01 to 0.04/hour)
    break_recovery_factor: float  # How much a break restores (0.3 to 0.8)


@dataclass
class IndustrySimProfile:
    """Complete simulation parameter set for one industry."""
    industry_id: str
    sector: str
    shift: ShiftProfile
    degradation: DegradationProfile
    environment: EnvironmentProfile
    economics: EconomicProfile
    cascade: CascadeProfile
    fatigue: FatigueProfile


# ═══════════════════════════════════════════════════════════════════
# INDUSTRY-SPECIFIC PARAMETER PROFILES
# ═══════════════════════════════════════════════════════════════════

INDUSTRY_PROFILES: Dict[str, IndustrySimProfile] = {}


def _profile(p: IndustrySimProfile):
    INDUSTRY_PROFILES[p.industry_id] = p


# ─── AGRICULTURE ────────────────────────────────────────────────

_AGRI_SHIFT = ShiftProfile(
    shift_type="daylight_only", shift_duration_hours=10,
    shifts_per_day=1, active_days_per_week=6,
    peak_hours=[6, 7, 8, 9, 10, 15, 16, 17],
    dead_hours=[0, 1, 2, 3, 4, 12, 13],
    seasonal_shutdown_weeks=0, night_activity_level=0.15,
    handover_overlap_minutes=0,
)

_AGRI_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.002, degradation_variance=1.5,
    maintenance_recovery=0.12, catastrophic_failure_prob=0.001,
    thermal_stress_factor=1.5, corrosion_factor=1.2,
    vibration_sensitivity=0.8, typical_rul_hours=3000,
    maintenance_interval_events=200,
)

_AGRI_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=1.8, humidity_sensitivity=1.0,
    rain_stop_probability=0.7, wind_sensitivity=0.3,
    dust_sensitivity=0.6, power_grid_dependency=0.3,
    seasonal_demand_amplitude=0.9, monsoon_impact=0.8,
)

_AGRI_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=200, downtime_cost_multiplier=1.5,
    material_cost_pct=0.25, energy_cost_pct=0.10,
    labor_cost_pct=0.40, inventory_sensitivity=0.3,
    sla_penalty_severity=0.2, demand_volatility=0.7,
    industry_scale="small",
)

_AGRI_CASCADE = CascadeProfile(
    cascade_probability=0.15, cascade_delay_events=(10, 50),
    primary_cascade_types=["supply_delay", "quality_degradation"],
    supplier_dependency=0.5, single_point_failures=["irrigation_pump", "harvester"],
    recovery_time_events=(20, 100),
)

_AGRI_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.20,
    night_shift_penalty=0.25, overtime_threshold_hours=10,
    overtime_error_multiplier=2.0, physical_labor_fatigue_rate=0.04,
    monitoring_vigilance_decay=0.01, break_recovery_factor=0.6,
)

for agri_id in ["rice_farming", "wheat_farming", "sugarcane_farming"]:
    _profile(IndustrySimProfile(
        industry_id=agri_id, sector="A_primary",
        shift=_AGRI_SHIFT, degradation=_AGRI_DEGRADATION,
        environment=_AGRI_ENVIRONMENT, economics=_AGRI_ECONOMICS,
        cascade=_AGRI_CASCADE, fatigue=_AGRI_FATIGUE,
    ))


# ─── OIL & GAS / REFINING ──────────────────────────────────────

_OG_SHIFT = ShiftProfile(
    shift_type="continuous_24_7", shift_duration_hours=12,
    shifts_per_day=2, active_days_per_week=7,
    peak_hours=[6, 7, 8, 9, 10, 11, 14, 15, 16],
    dead_hours=[2, 3, 4],
    seasonal_shutdown_weeks=0, night_activity_level=0.85,
    handover_overlap_minutes=30,
)

_OG_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0008, degradation_variance=1.2,
    maintenance_recovery=0.10, catastrophic_failure_prob=0.0003,
    thermal_stress_factor=1.8, corrosion_factor=2.5,
    vibration_sensitivity=1.5, typical_rul_hours=20000,
    maintenance_interval_events=1000,
)

_OG_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=1.2, humidity_sensitivity=1.5,
    rain_stop_probability=0.05, wind_sensitivity=0.2,
    dust_sensitivity=0.4, power_grid_dependency=0.3,
    seasonal_demand_amplitude=0.15, monsoon_impact=0.1,
)

_OG_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=50000, downtime_cost_multiplier=2.5,
    material_cost_pct=0.55, energy_cost_pct=0.20,
    labor_cost_pct=0.10, inventory_sensitivity=0.7,
    sla_penalty_severity=0.6, demand_volatility=0.4,
    industry_scale="large",
)

_OG_CASCADE = CascadeProfile(
    cascade_probability=0.40, cascade_delay_events=(3, 15),
    primary_cascade_types=["downstream_production_stop", "safety_risk", "environmental_release"],
    supplier_dependency=0.3, single_point_failures=["compressor", "furnace", "reactor"],
    recovery_time_events=(5, 50),
)

_OG_FATIGUE = FatigueProfile(
    peak_alertness_hour=3, post_lunch_dip=0.10,
    night_shift_penalty=0.15, overtime_threshold_hours=12,
    overtime_error_multiplier=1.8, physical_labor_fatigue_rate=0.02,
    monitoring_vigilance_decay=0.03, break_recovery_factor=0.5,
)

for og_id in ["oil_refining", "offshore_oil_drilling"]:
    _profile(IndustrySimProfile(
        industry_id=og_id, sector="B_processing",
        shift=_OG_SHIFT, degradation=_OG_DEGRADATION,
        environment=_OG_ENVIRONMENT, economics=_OG_ECONOMICS,
        cascade=_OG_CASCADE, fatigue=_OG_FATIGUE,
    ))


# ─── AUTOMOTIVE MANUFACTURING ──────────────────────────────────

_AUTO_SHIFT = ShiftProfile(
    shift_type="two_shift", shift_duration_hours=8.5,
    shifts_per_day=2, active_days_per_week=5,
    peak_hours=[7, 8, 9, 10, 11, 14, 15, 16],
    dead_hours=[0, 1, 2, 3, 4, 5, 23],
    seasonal_shutdown_weeks=3, night_activity_level=0.7,
    handover_overlap_minutes=15,
)

_AUTO_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.001, degradation_variance=1.0,
    maintenance_recovery=0.08, catastrophic_failure_prob=0.0005,
    thermal_stress_factor=0.8, corrosion_factor=0.5,
    vibration_sensitivity=1.2, typical_rul_hours=15000,
    maintenance_interval_events=500,
)

_AUTO_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.3, humidity_sensitivity=0.5,
    rain_stop_probability=0.0, wind_sensitivity=0.0,
    dust_sensitivity=0.3, power_grid_dependency=0.9,
    seasonal_demand_amplitude=0.3, monsoon_impact=0.05,
)

_AUTO_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=80000, downtime_cost_multiplier=3.0,
    material_cost_pct=0.60, energy_cost_pct=0.05,
    labor_cost_pct=0.15, inventory_sensitivity=0.95,
    sla_penalty_severity=0.8, demand_volatility=0.3,
    industry_scale="large",
)

_AUTO_CASCADE = CascadeProfile(
    cascade_probability=0.55, cascade_delay_events=(1, 8),
    primary_cascade_types=["line_stop", "quality_degradation", "downstream_starvation"],
    supplier_dependency=0.95, single_point_failures=["paint_booth", "press_line", "body_shop_robot"],
    recovery_time_events=(3, 30),
)

_AUTO_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.15,
    night_shift_penalty=0.12, overtime_threshold_hours=8.5,
    overtime_error_multiplier=2.0, physical_labor_fatigue_rate=0.03,
    monitoring_vigilance_decay=0.02, break_recovery_factor=0.6,
)

_profile(IndustrySimProfile(
    industry_id="automobile_assembly", sector="C_manufacturing",
    shift=_AUTO_SHIFT, degradation=_AUTO_DEGRADATION,
    environment=_AUTO_ENVIRONMENT, economics=_AUTO_ECONOMICS,
    cascade=_AUTO_CASCADE, fatigue=_AUTO_FATIGUE,
))


# ─── HEALTHCARE ─────────────────────────────────────────────────

_HEALTH_SHIFT = ShiftProfile(
    shift_type="continuous_24_7", shift_duration_hours=12,
    shifts_per_day=2, active_days_per_week=7,
    peak_hours=[8, 9, 10, 11, 14, 15, 16, 19, 20],
    dead_hours=[2, 3, 4, 5],
    seasonal_shutdown_weeks=0, night_activity_level=0.6,
    handover_overlap_minutes=30,
)

_HEALTH_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0005, degradation_variance=0.8,
    maintenance_recovery=0.15, catastrophic_failure_prob=0.0002,
    thermal_stress_factor=0.2, corrosion_factor=0.3,
    vibration_sensitivity=0.4, typical_rul_hours=30000,
    maintenance_interval_events=2000,
)

_HEALTH_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.1, humidity_sensitivity=0.2,
    rain_stop_probability=0.0, wind_sensitivity=0.0,
    dust_sensitivity=0.1, power_grid_dependency=1.0,
    seasonal_demand_amplitude=0.2, monsoon_impact=0.05,
)

_HEALTH_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=15000, downtime_cost_multiplier=2.0,
    material_cost_pct=0.30, energy_cost_pct=0.05,
    labor_cost_pct=0.55, inventory_sensitivity=0.8,
    sla_penalty_severity=0.3, demand_volatility=0.5,
    industry_scale="large",
)

_HEALTH_CASCADE = CascadeProfile(
    cascade_probability=0.25, cascade_delay_events=(1, 5),
    primary_cascade_types=["patient_risk", "capacity_overflow", "staff_burnout"],
    supplier_dependency=0.6, single_point_failures=["oxygen_plant", "generator", "ct_scanner"],
    recovery_time_events=(2, 20),
)

_HEALTH_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.12,
    night_shift_penalty=0.20, overtime_threshold_hours=12,
    overtime_error_multiplier=2.5, physical_labor_fatigue_rate=0.025,
    monitoring_vigilance_decay=0.035, break_recovery_factor=0.5,
)

_profile(IndustrySimProfile(
    industry_id="hospital", sector="H_services",
    shift=_HEALTH_SHIFT, degradation=_HEALTH_DEGRADATION,
    environment=_HEALTH_ENVIRONMENT, economics=_HEALTH_ECONOMICS,
    cascade=_HEALTH_CASCADE, fatigue=_HEALTH_FATIGUE,
))


# ─── STEEL / METALS ─────────────────────────────────────────────

_STEEL_SHIFT = ShiftProfile(
    shift_type="continuous_24_7", shift_duration_hours=8,
    shifts_per_day=3, active_days_per_week=7,
    peak_hours=[6, 7, 8, 9, 10, 14, 15, 16, 17],
    dead_hours=[2, 3, 4],
    seasonal_shutdown_weeks=0, night_activity_level=0.9,
    handover_overlap_minutes=20,
)

_STEEL_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0015, degradation_variance=1.3,
    maintenance_recovery=0.08, catastrophic_failure_prob=0.001,
    thermal_stress_factor=2.0, corrosion_factor=1.8,
    vibration_sensitivity=1.5, typical_rul_hours=10000,
    maintenance_interval_events=800,
)

_STEEL_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.5, humidity_sensitivity=0.8,
    rain_stop_probability=0.0, wind_sensitivity=0.1,
    dust_sensitivity=0.7, power_grid_dependency=0.95,
    seasonal_demand_amplitude=0.2, monsoon_impact=0.1,
)

_STEEL_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=40000, downtime_cost_multiplier=2.5,
    material_cost_pct=0.50, energy_cost_pct=0.25,
    labor_cost_pct=0.08, inventory_sensitivity=0.6,
    sla_penalty_severity=0.5, demand_volatility=0.3,
    industry_scale="large",
)

_STEEL_CASCADE = CascadeProfile(
    cascade_probability=0.45, cascade_delay_events=(2, 10),
    primary_cascade_types=["downstream_stop", "quality_degradation", "safety_risk"],
    supplier_dependency=0.7, single_point_failures=["blast_furnace", "rolling_mill", "caster"],
    recovery_time_events=(5, 100),
)

_STEEL_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.15,
    night_shift_penalty=0.18, overtime_threshold_hours=8,
    overtime_error_multiplier=2.2, physical_labor_fatigue_rate=0.035,
    monitoring_vigilance_decay=0.025, break_recovery_factor=0.55,
)

_profile(IndustrySimProfile(
    industry_id="steel_rolling", sector="B_processing",
    shift=_STEEL_SHIFT, degradation=_STEEL_DEGRADATION,
    environment=_STEEL_ENVIRONMENT, economics=_STEEL_ECONOMICS,
    cascade=_STEEL_CASCADE, fatigue=_STEEL_FATIGUE,
))



# ─── MINING ─────────────────────────────────────────────────────

_MINING_SHIFT = ShiftProfile(
    shift_type="continuous_24_7", shift_duration_hours=8,
    shifts_per_day=3, active_days_per_week=7,
    peak_hours=[6, 7, 8, 9, 10, 14, 15, 16],
    dead_hours=[1, 2, 3, 4],
    seasonal_shutdown_weeks=0, night_activity_level=0.75,
    handover_overlap_minutes=20,
)

_MINING_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.003, degradation_variance=1.8,
    maintenance_recovery=0.10, catastrophic_failure_prob=0.002,
    thermal_stress_factor=1.0, corrosion_factor=1.5,
    vibration_sensitivity=1.8, typical_rul_hours=5000,
    maintenance_interval_events=300,
)

_MINING_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=1.2, humidity_sensitivity=1.3,
    rain_stop_probability=0.4, wind_sensitivity=0.3,
    dust_sensitivity=1.0, power_grid_dependency=0.6,
    seasonal_demand_amplitude=0.15, monsoon_impact=0.5,
)

_MINING_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=25000, downtime_cost_multiplier=2.0,
    material_cost_pct=0.20, energy_cost_pct=0.25,
    labor_cost_pct=0.30, inventory_sensitivity=0.4,
    sla_penalty_severity=0.3, demand_volatility=0.35,
    industry_scale="large",
)

_MINING_CASCADE = CascadeProfile(
    cascade_probability=0.35, cascade_delay_events=(3, 20),
    primary_cascade_types=["safety_risk", "supply_stop", "environmental_release"],
    supplier_dependency=0.3, single_point_failures=["conveyor_belt", "crusher", "hoist_system"],
    recovery_time_events=(10, 80),
)

_MINING_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.18,
    night_shift_penalty=0.22, overtime_threshold_hours=8,
    overtime_error_multiplier=2.5, physical_labor_fatigue_rate=0.045,
    monitoring_vigilance_decay=0.02, break_recovery_factor=0.5,
)

for mining_id in ["coal_mining", "iron_ore_mining", "bauxite_mining", "copper_mining", "diamond_mining"]:
    _profile(IndustrySimProfile(
        industry_id=mining_id, sector="A_primary",
        shift=_MINING_SHIFT, degradation=_MINING_DEGRADATION,
        environment=_MINING_ENVIRONMENT, economics=_MINING_ECONOMICS,
        cascade=_MINING_CASCADE, fatigue=_MINING_FATIGUE,
    ))


# ─── POWER GENERATION ───────────────────────────────────────────

_POWER_SHIFT = ShiftProfile(
    shift_type="continuous_24_7", shift_duration_hours=8,
    shifts_per_day=3, active_days_per_week=7,
    peak_hours=[8, 9, 10, 11, 17, 18, 19, 20, 21],
    dead_hours=[2, 3, 4, 5],
    seasonal_shutdown_weeks=0, night_activity_level=0.90,
    handover_overlap_minutes=30,
)

_POWER_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0006, degradation_variance=0.9,
    maintenance_recovery=0.08, catastrophic_failure_prob=0.0002,
    thermal_stress_factor=1.8, corrosion_factor=1.2,
    vibration_sensitivity=1.3, typical_rul_hours=40000,
    maintenance_interval_events=2000,
)

_POWER_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=1.0, humidity_sensitivity=0.8,
    rain_stop_probability=0.0, wind_sensitivity=0.2,
    dust_sensitivity=0.4, power_grid_dependency=0.1,
    seasonal_demand_amplitude=0.4, monsoon_impact=0.15,
)

_POWER_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=60000, downtime_cost_multiplier=2.8,
    material_cost_pct=0.40, energy_cost_pct=0.30,
    labor_cost_pct=0.08, inventory_sensitivity=0.5,
    sla_penalty_severity=0.9, demand_volatility=0.4,
    industry_scale="large",
)

_POWER_CASCADE = CascadeProfile(
    cascade_probability=0.50, cascade_delay_events=(1, 8),
    primary_cascade_types=["grid_instability", "blackout_cascade", "safety_risk"],
    supplier_dependency=0.4, single_point_failures=["turbine", "transformer", "cooling_tower"],
    recovery_time_events=(5, 60),
)

_POWER_FATIGUE = FatigueProfile(
    peak_alertness_hour=3, post_lunch_dip=0.10,
    night_shift_penalty=0.15, overtime_threshold_hours=8,
    overtime_error_multiplier=2.0, physical_labor_fatigue_rate=0.02,
    monitoring_vigilance_decay=0.035, break_recovery_factor=0.55,
)

for power_id in ["thermal_power_plant", "solar_farm", "wind_farm", "nuclear_power_plant", "hydroelectric_dam"]:
    _profile(IndustrySimProfile(
        industry_id=power_id, sector="D_utilities",
        shift=_POWER_SHIFT, degradation=_POWER_DEGRADATION,
        environment=_POWER_ENVIRONMENT, economics=_POWER_ECONOMICS,
        cascade=_POWER_CASCADE, fatigue=_POWER_FATIGUE,
    ))


# ─── FOOD PROCESSING ───────────────────────────────────────────

_FOOD_SHIFT = ShiftProfile(
    shift_type="two_shift", shift_duration_hours=8,
    shifts_per_day=2, active_days_per_week=6,
    peak_hours=[5, 6, 7, 8, 9, 10, 11, 14, 15],
    dead_hours=[0, 1, 2, 3, 22, 23],
    seasonal_shutdown_weeks=1, night_activity_level=0.4,
    handover_overlap_minutes=15,
)

_FOOD_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0012, degradation_variance=1.1,
    maintenance_recovery=0.12, catastrophic_failure_prob=0.0006,
    thermal_stress_factor=0.8, corrosion_factor=1.8,
    vibration_sensitivity=0.9, typical_rul_hours=8000,
    maintenance_interval_events=400,
)

_FOOD_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.6, humidity_sensitivity=1.5,
    rain_stop_probability=0.05, wind_sensitivity=0.05,
    dust_sensitivity=0.2, power_grid_dependency=0.85,
    seasonal_demand_amplitude=0.5, monsoon_impact=0.2,
)

_FOOD_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=8000, downtime_cost_multiplier=2.0,
    material_cost_pct=0.55, energy_cost_pct=0.08,
    labor_cost_pct=0.20, inventory_sensitivity=0.9,
    sla_penalty_severity=0.7, demand_volatility=0.4,
    industry_scale="medium",
)

_FOOD_CASCADE = CascadeProfile(
    cascade_probability=0.30, cascade_delay_events=(2, 12),
    primary_cascade_types=["spoilage_risk", "quality_degradation", "supply_stop"],
    supplier_dependency=0.8, single_point_failures=["boiler", "refrigeration_unit", "packaging_line"],
    recovery_time_events=(5, 40),
)

_FOOD_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.15,
    night_shift_penalty=0.12, overtime_threshold_hours=8,
    overtime_error_multiplier=1.8, physical_labor_fatigue_rate=0.03,
    monitoring_vigilance_decay=0.02, break_recovery_factor=0.6,
)

for food_id in ["rice_milling", "sugar_milling", "dairy_processing", "meat_processing", "beverage_bottling"]:
    _profile(IndustrySimProfile(
        industry_id=food_id, sector="B_processing",
        shift=_FOOD_SHIFT, degradation=_FOOD_DEGRADATION,
        environment=_FOOD_ENVIRONMENT, economics=_FOOD_ECONOMICS,
        cascade=_FOOD_CASCADE, fatigue=_FOOD_FATIGUE,
    ))


# ─── PHARMACEUTICAL ─────────────────────────────────────────────

_PHARMA_SHIFT = ShiftProfile(
    shift_type="two_shift", shift_duration_hours=8,
    shifts_per_day=2, active_days_per_week=5,
    peak_hours=[7, 8, 9, 10, 11, 13, 14, 15, 16],
    dead_hours=[0, 1, 2, 3, 4, 22, 23],
    seasonal_shutdown_weeks=2, night_activity_level=0.3,
    handover_overlap_minutes=30,
)

_PHARMA_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0004, degradation_variance=0.6,
    maintenance_recovery=0.15, catastrophic_failure_prob=0.0001,
    thermal_stress_factor=0.3, corrosion_factor=0.8,
    vibration_sensitivity=0.5, typical_rul_hours=25000,
    maintenance_interval_events=1500,
)

_PHARMA_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.1, humidity_sensitivity=0.1,
    rain_stop_probability=0.0, wind_sensitivity=0.0,
    dust_sensitivity=0.05, power_grid_dependency=0.95,
    seasonal_demand_amplitude=0.2, monsoon_impact=0.0,
)

_PHARMA_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=35000, downtime_cost_multiplier=2.5,
    material_cost_pct=0.30, energy_cost_pct=0.05,
    labor_cost_pct=0.35, inventory_sensitivity=0.7,
    sla_penalty_severity=0.95, demand_volatility=0.25,
    industry_scale="large",
)

_PHARMA_CASCADE = CascadeProfile(
    cascade_probability=0.20, cascade_delay_events=(5, 30),
    primary_cascade_types=["batch_rejection", "quality_deviation", "regulatory_halt"],
    supplier_dependency=0.7, single_point_failures=["cleanroom_hvac", "tablet_press", "autoclave"],
    recovery_time_events=(10, 60),
)

_PHARMA_FATIGUE = FatigueProfile(
    peak_alertness_hour=3, post_lunch_dip=0.12,
    night_shift_penalty=0.10, overtime_threshold_hours=8,
    overtime_error_multiplier=2.2, physical_labor_fatigue_rate=0.015,
    monitoring_vigilance_decay=0.03, break_recovery_factor=0.65,
)

for pharma_id in ["pharmaceutical_tablet", "vaccine_manufacturing", "biotech_lab"]:
    _profile(IndustrySimProfile(
        industry_id=pharma_id, sector="C_manufacturing",
        shift=_PHARMA_SHIFT, degradation=_PHARMA_DEGRADATION,
        environment=_PHARMA_ENVIRONMENT, economics=_PHARMA_ECONOMICS,
        cascade=_PHARMA_CASCADE, fatigue=_PHARMA_FATIGUE,
    ))


# ─── ELECTRONICS ────────────────────────────────────────────────

_ELEC_SHIFT = ShiftProfile(
    shift_type="continuous_24_7", shift_duration_hours=12,
    shifts_per_day=2, active_days_per_week=7,
    peak_hours=[7, 8, 9, 10, 11, 14, 15, 16, 17],
    dead_hours=[2, 3, 4, 5],
    seasonal_shutdown_weeks=1, night_activity_level=0.85,
    handover_overlap_minutes=20,
)

_ELEC_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0005, degradation_variance=0.7,
    maintenance_recovery=0.12, catastrophic_failure_prob=0.0002,
    thermal_stress_factor=0.5, corrosion_factor=0.3,
    vibration_sensitivity=0.6, typical_rul_hours=20000,
    maintenance_interval_events=1200,
)

_ELEC_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.2, humidity_sensitivity=0.15,
    rain_stop_probability=0.0, wind_sensitivity=0.0,
    dust_sensitivity=0.05, power_grid_dependency=1.0,
    seasonal_demand_amplitude=0.35, monsoon_impact=0.0,
)

_ELEC_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=90000, downtime_cost_multiplier=3.0,
    material_cost_pct=0.50, energy_cost_pct=0.10,
    labor_cost_pct=0.20, inventory_sensitivity=0.85,
    sla_penalty_severity=0.85, demand_volatility=0.5,
    industry_scale="large",
)

_ELEC_CASCADE = CascadeProfile(
    cascade_probability=0.45, cascade_delay_events=(1, 10),
    primary_cascade_types=["yield_loss", "contamination", "line_stop"],
    supplier_dependency=0.9, single_point_failures=["lithography_machine", "reflow_oven", "cleanroom_filter"],
    recovery_time_events=(5, 40),
)

_ELEC_FATIGUE = FatigueProfile(
    peak_alertness_hour=3, post_lunch_dip=0.10,
    night_shift_penalty=0.12, overtime_threshold_hours=12,
    overtime_error_multiplier=1.8, physical_labor_fatigue_rate=0.015,
    monitoring_vigilance_decay=0.03, break_recovery_factor=0.6,
)

for elec_id in ["electronics_pcb", "semiconductor_fab", "electronics_assembly"]:
    _profile(IndustrySimProfile(
        industry_id=elec_id, sector="C_manufacturing",
        shift=_ELEC_SHIFT, degradation=_ELEC_DEGRADATION,
        environment=_ELEC_ENVIRONMENT, economics=_ELEC_ECONOMICS,
        cascade=_ELEC_CASCADE, fatigue=_ELEC_FATIGUE,
    ))


# ─── TEXTILE ───────────────────────────────────────────────────

_TEXTILE_SHIFT = ShiftProfile(
    shift_type="two_shift", shift_duration_hours=10,
    shifts_per_day=2, active_days_per_week=6,
    peak_hours=[6, 7, 8, 9, 10, 11, 14, 15, 16],
    dead_hours=[0, 1, 2, 3, 4, 23],
    seasonal_shutdown_weeks=2, night_activity_level=0.6,
    handover_overlap_minutes=10,
)

_TEXTILE_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0018, degradation_variance=1.4,
    maintenance_recovery=0.10, catastrophic_failure_prob=0.0008,
    thermal_stress_factor=0.6, corrosion_factor=1.0,
    vibration_sensitivity=1.2, typical_rul_hours=6000,
    maintenance_interval_events=350,
)

_TEXTILE_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.5, humidity_sensitivity=1.2,
    rain_stop_probability=0.0, wind_sensitivity=0.05,
    dust_sensitivity=0.7, power_grid_dependency=0.8,
    seasonal_demand_amplitude=0.6, monsoon_impact=0.1,
)

_TEXTILE_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=3000, downtime_cost_multiplier=1.5,
    material_cost_pct=0.50, energy_cost_pct=0.08,
    labor_cost_pct=0.30, inventory_sensitivity=0.6,
    sla_penalty_severity=0.5, demand_volatility=0.5,
    industry_scale="medium",
)

_TEXTILE_CASCADE = CascadeProfile(
    cascade_probability=0.25, cascade_delay_events=(5, 25),
    primary_cascade_types=["quality_degradation", "supply_delay", "order_backlog"],
    supplier_dependency=0.7, single_point_failures=["dyeing_machine", "spinning_frame", "loom"],
    recovery_time_events=(8, 50),
)

_TEXTILE_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.18,
    night_shift_penalty=0.15, overtime_threshold_hours=10,
    overtime_error_multiplier=1.8, physical_labor_fatigue_rate=0.035,
    monitoring_vigilance_decay=0.015, break_recovery_factor=0.55,
)

for textile_id in ["cotton_spinning", "leather_tanning", "garment_factory", "denim_mill"]:
    _profile(IndustrySimProfile(
        industry_id=textile_id, sector="C_manufacturing",
        shift=_TEXTILE_SHIFT, degradation=_TEXTILE_DEGRADATION,
        environment=_TEXTILE_ENVIRONMENT, economics=_TEXTILE_ECONOMICS,
        cascade=_TEXTILE_CASCADE, fatigue=_TEXTILE_FATIGUE,
    ))


# ─── CONSTRUCTION ──────────────────────────────────────────────

_CONSTR_SHIFT = ShiftProfile(
    shift_type="daylight_only", shift_duration_hours=10,
    shifts_per_day=1, active_days_per_week=6,
    peak_hours=[7, 8, 9, 10, 11, 14, 15, 16],
    dead_hours=[0, 1, 2, 3, 4, 5, 20, 21, 22, 23],
    seasonal_shutdown_weeks=2, night_activity_level=0.1,
    handover_overlap_minutes=0,
)

_CONSTR_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0025, degradation_variance=1.6,
    maintenance_recovery=0.10, catastrophic_failure_prob=0.0015,
    thermal_stress_factor=1.2, corrosion_factor=1.0,
    vibration_sensitivity=1.5, typical_rul_hours=4000,
    maintenance_interval_events=250,
)

_CONSTR_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=1.5, humidity_sensitivity=0.8,
    rain_stop_probability=0.8, wind_sensitivity=0.9,
    dust_sensitivity=0.8, power_grid_dependency=0.3,
    seasonal_demand_amplitude=0.4, monsoon_impact=0.9,
)

_CONSTR_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=12000, downtime_cost_multiplier=1.8,
    material_cost_pct=0.45, energy_cost_pct=0.12,
    labor_cost_pct=0.35, inventory_sensitivity=0.5,
    sla_penalty_severity=0.7, demand_volatility=0.3,
    industry_scale="large",
)

_CONSTR_CASCADE = CascadeProfile(
    cascade_probability=0.30, cascade_delay_events=(5, 30),
    primary_cascade_types=["schedule_delay", "safety_risk", "rework_required"],
    supplier_dependency=0.6, single_point_failures=["crane", "concrete_mixer", "pile_driver"],
    recovery_time_events=(10, 70),
)

_CONSTR_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.20,
    night_shift_penalty=0.25, overtime_threshold_hours=10,
    overtime_error_multiplier=2.2, physical_labor_fatigue_rate=0.05,
    monitoring_vigilance_decay=0.015, break_recovery_factor=0.5,
)

for constr_id in ["road_construction", "building_construction", "bridge_construction"]:
    _profile(IndustrySimProfile(
        industry_id=constr_id, sector="F_construction",
        shift=_CONSTR_SHIFT, degradation=_CONSTR_DEGRADATION,
        environment=_CONSTR_ENVIRONMENT, economics=_CONSTR_ECONOMICS,
        cascade=_CONSTR_CASCADE, fatigue=_CONSTR_FATIGUE,
    ))


# ─── CHEMICAL ──────────────────────────────────────────────────

_CHEM_SHIFT = ShiftProfile(
    shift_type="continuous_24_7", shift_duration_hours=8,
    shifts_per_day=3, active_days_per_week=7,
    peak_hours=[6, 7, 8, 9, 10, 14, 15, 16, 17],
    dead_hours=[2, 3, 4],
    seasonal_shutdown_weeks=0, night_activity_level=0.85,
    handover_overlap_minutes=25,
)

_CHEM_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0010, degradation_variance=1.2,
    maintenance_recovery=0.09, catastrophic_failure_prob=0.0005,
    thermal_stress_factor=1.5, corrosion_factor=2.8,
    vibration_sensitivity=1.0, typical_rul_hours=15000,
    maintenance_interval_events=900,
)

_CHEM_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.8, humidity_sensitivity=1.0,
    rain_stop_probability=0.0, wind_sensitivity=0.1,
    dust_sensitivity=0.3, power_grid_dependency=0.8,
    seasonal_demand_amplitude=0.2, monsoon_impact=0.05,
)

_CHEM_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=30000, downtime_cost_multiplier=2.5,
    material_cost_pct=0.50, energy_cost_pct=0.20,
    labor_cost_pct=0.10, inventory_sensitivity=0.7,
    sla_penalty_severity=0.6, demand_volatility=0.3,
    industry_scale="large",
)

_CHEM_CASCADE = CascadeProfile(
    cascade_probability=0.45, cascade_delay_events=(2, 12),
    primary_cascade_types=["safety_risk", "environmental_release", "downstream_stop"],
    supplier_dependency=0.5, single_point_failures=["reactor_vessel", "distillation_column", "heat_exchanger"],
    recovery_time_events=(5, 60),
)

_CHEM_FATIGUE = FatigueProfile(
    peak_alertness_hour=3, post_lunch_dip=0.10,
    night_shift_penalty=0.15, overtime_threshold_hours=8,
    overtime_error_multiplier=2.0, physical_labor_fatigue_rate=0.02,
    monitoring_vigilance_decay=0.035, break_recovery_factor=0.5,
)

for chem_id in ["fertilizer_plant", "paint_manufacturing", "petrochemical_plant"]:
    _profile(IndustrySimProfile(
        industry_id=chem_id, sector="B_processing",
        shift=_CHEM_SHIFT, degradation=_CHEM_DEGRADATION,
        environment=_CHEM_ENVIRONMENT, economics=_CHEM_ECONOMICS,
        cascade=_CHEM_CASCADE, fatigue=_CHEM_FATIGUE,
    ))


# ─── LOGISTICS ─────────────────────────────────────────────────

_LOGISTICS_SHIFT = ShiftProfile(
    shift_type="continuous_24_7", shift_duration_hours=8,
    shifts_per_day=3, active_days_per_week=7,
    peak_hours=[6, 7, 8, 9, 10, 15, 16, 17, 18],
    dead_hours=[1, 2, 3, 4],
    seasonal_shutdown_weeks=0, night_activity_level=0.6,
    handover_overlap_minutes=15,
)

_LOGISTICS_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0012, degradation_variance=1.3,
    maintenance_recovery=0.12, catastrophic_failure_prob=0.0004,
    thermal_stress_factor=0.4, corrosion_factor=0.6,
    vibration_sensitivity=1.0, typical_rul_hours=12000,
    maintenance_interval_events=600,
)

_LOGISTICS_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.4, humidity_sensitivity=0.5,
    rain_stop_probability=0.15, wind_sensitivity=0.3,
    dust_sensitivity=0.3, power_grid_dependency=0.7,
    seasonal_demand_amplitude=0.5, monsoon_impact=0.3,
)

_LOGISTICS_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=10000, downtime_cost_multiplier=2.0,
    material_cost_pct=0.10, energy_cost_pct=0.20,
    labor_cost_pct=0.40, inventory_sensitivity=0.95,
    sla_penalty_severity=0.8, demand_volatility=0.45,
    industry_scale="large",
)

_LOGISTICS_CASCADE = CascadeProfile(
    cascade_probability=0.40, cascade_delay_events=(2, 15),
    primary_cascade_types=["delivery_delay", "capacity_overflow", "supply_chain_disruption"],
    supplier_dependency=0.3, single_point_failures=["container_crane", "sorting_system", "fleet_management"],
    recovery_time_events=(5, 35),
)

_LOGISTICS_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.15,
    night_shift_penalty=0.18, overtime_threshold_hours=8,
    overtime_error_multiplier=2.0, physical_labor_fatigue_rate=0.035,
    monitoring_vigilance_decay=0.02, break_recovery_factor=0.55,
)

for logistics_id in ["logistics_warehouse", "port_operations", "railway_freight"]:
    _profile(IndustrySimProfile(
        industry_id=logistics_id, sector="G_logistics",
        shift=_LOGISTICS_SHIFT, degradation=_LOGISTICS_DEGRADATION,
        environment=_LOGISTICS_ENVIRONMENT, economics=_LOGISTICS_ECONOMICS,
        cascade=_LOGISTICS_CASCADE, fatigue=_LOGISTICS_FATIGUE,
    ))


# ─── IT / SOFTWARE ─────────────────────────────────────────────

_IT_SHIFT = ShiftProfile(
    shift_type="split_shift", shift_duration_hours=9,
    shifts_per_day=1, active_days_per_week=5,
    peak_hours=[10, 11, 14, 15, 16, 17, 18],
    dead_hours=[0, 1, 2, 3, 4, 5, 6],
    seasonal_shutdown_weeks=0, night_activity_level=0.2,
    handover_overlap_minutes=0,
)

_IT_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0003, degradation_variance=0.5,
    maintenance_recovery=0.18, catastrophic_failure_prob=0.0001,
    thermal_stress_factor=0.4, corrosion_factor=0.1,
    vibration_sensitivity=0.2, typical_rul_hours=50000,
    maintenance_interval_events=3000,
)

_IT_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.1, humidity_sensitivity=0.1,
    rain_stop_probability=0.0, wind_sensitivity=0.0,
    dust_sensitivity=0.05, power_grid_dependency=1.0,
    seasonal_demand_amplitude=0.1, monsoon_impact=0.0,
)

_IT_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=20000, downtime_cost_multiplier=2.5,
    material_cost_pct=0.05, energy_cost_pct=0.08,
    labor_cost_pct=0.60, inventory_sensitivity=0.1,
    sla_penalty_severity=0.9, demand_volatility=0.3,
    industry_scale="medium",
)

_IT_CASCADE = CascadeProfile(
    cascade_probability=0.35, cascade_delay_events=(1, 5),
    primary_cascade_types=["service_outage", "data_loss", "dependency_failure"],
    supplier_dependency=0.5, single_point_failures=["database_cluster", "network_switch", "cooling_unit"],
    recovery_time_events=(2, 20),
)

_IT_FATIGUE = FatigueProfile(
    peak_alertness_hour=3, post_lunch_dip=0.20,
    night_shift_penalty=0.10, overtime_threshold_hours=9,
    overtime_error_multiplier=2.5, physical_labor_fatigue_rate=0.01,
    monitoring_vigilance_decay=0.04, break_recovery_factor=0.7,
)

for it_id in ["software_company", "data_center", "ai_research_lab"]:
    _profile(IndustrySimProfile(
        industry_id=it_id, sector="J_information",
        shift=_IT_SHIFT, degradation=_IT_DEGRADATION,
        environment=_IT_ENVIRONMENT, economics=_IT_ECONOMICS,
        cascade=_IT_CASCADE, fatigue=_IT_FATIGUE,
    ))


# ─── CEMENT ────────────────────────────────────────────────────

_CEMENT_SHIFT = ShiftProfile(
    shift_type="continuous_24_7", shift_duration_hours=8,
    shifts_per_day=3, active_days_per_week=7,
    peak_hours=[6, 7, 8, 9, 10, 14, 15, 16, 17],
    dead_hours=[2, 3, 4],
    seasonal_shutdown_weeks=0, night_activity_level=0.85,
    handover_overlap_minutes=20,
)

_CEMENT_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0020, degradation_variance=1.4,
    maintenance_recovery=0.08, catastrophic_failure_prob=0.001,
    thermal_stress_factor=2.0, corrosion_factor=1.5,
    vibration_sensitivity=1.6, typical_rul_hours=8000,
    maintenance_interval_events=500,
)

_CEMENT_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.6, humidity_sensitivity=1.0,
    rain_stop_probability=0.1, wind_sensitivity=0.2,
    dust_sensitivity=0.95, power_grid_dependency=0.9,
    seasonal_demand_amplitude=0.3, monsoon_impact=0.2,
)

_CEMENT_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=20000, downtime_cost_multiplier=2.2,
    material_cost_pct=0.35, energy_cost_pct=0.30,
    labor_cost_pct=0.10, inventory_sensitivity=0.5,
    sla_penalty_severity=0.5, demand_volatility=0.3,
    industry_scale="large",
)

_CEMENT_CASCADE = CascadeProfile(
    cascade_probability=0.40, cascade_delay_events=(3, 15),
    primary_cascade_types=["kiln_shutdown", "quality_degradation", "supply_stop"],
    supplier_dependency=0.4, single_point_failures=["rotary_kiln", "ball_mill", "clinker_cooler"],
    recovery_time_events=(8, 70),
)

_CEMENT_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.15,
    night_shift_penalty=0.18, overtime_threshold_hours=8,
    overtime_error_multiplier=2.0, physical_labor_fatigue_rate=0.035,
    monitoring_vigilance_decay=0.025, break_recovery_factor=0.5,
)

_profile(IndustrySimProfile(
    industry_id="cement_manufacturing", sector="B_processing",
    shift=_CEMENT_SHIFT, degradation=_CEMENT_DEGRADATION,
    environment=_CEMENT_ENVIRONMENT, economics=_CEMENT_ECONOMICS,
    cascade=_CEMENT_CASCADE, fatigue=_CEMENT_FATIGUE,
))


# ─── RETAIL / HOSPITALITY ──────────────────────────────────────

_RETAIL_SHIFT = ShiftProfile(
    shift_type="split_shift", shift_duration_hours=10,
    shifts_per_day=2, active_days_per_week=7,
    peak_hours=[10, 11, 12, 13, 18, 19, 20, 21],
    dead_hours=[1, 2, 3, 4, 5, 6],
    seasonal_shutdown_weeks=0, night_activity_level=0.3,
    handover_overlap_minutes=10,
)

_RETAIL_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0008, degradation_variance=1.0,
    maintenance_recovery=0.15, catastrophic_failure_prob=0.0003,
    thermal_stress_factor=0.3, corrosion_factor=0.4,
    vibration_sensitivity=0.3, typical_rul_hours=15000,
    maintenance_interval_events=1000,
)

_RETAIL_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.2, humidity_sensitivity=0.3,
    rain_stop_probability=0.0, wind_sensitivity=0.0,
    dust_sensitivity=0.1, power_grid_dependency=0.9,
    seasonal_demand_amplitude=0.7, monsoon_impact=0.1,
)

_RETAIL_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=5000, downtime_cost_multiplier=1.5,
    material_cost_pct=0.55, energy_cost_pct=0.08,
    labor_cost_pct=0.25, inventory_sensitivity=0.8,
    sla_penalty_severity=0.4, demand_volatility=0.6,
    industry_scale="medium",
)

_RETAIL_CASCADE = CascadeProfile(
    cascade_probability=0.20, cascade_delay_events=(3, 15),
    primary_cascade_types=["stockout", "customer_loss", "spoilage"],
    supplier_dependency=0.8, single_point_failures=["pos_system", "refrigeration", "hvac"],
    recovery_time_events=(3, 20),
)

_RETAIL_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.15,
    night_shift_penalty=0.12, overtime_threshold_hours=10,
    overtime_error_multiplier=1.5, physical_labor_fatigue_rate=0.025,
    monitoring_vigilance_decay=0.015, break_recovery_factor=0.65,
)

for retail_id in ["supermarket_retail", "restaurant_kitchen", "hotel_operations"]:
    _profile(IndustrySimProfile(
        industry_id=retail_id, sector="G_retail_hospitality",
        shift=_RETAIL_SHIFT, degradation=_RETAIL_DEGRADATION,
        environment=_RETAIL_ENVIRONMENT, economics=_RETAIL_ECONOMICS,
        cascade=_RETAIL_CASCADE, fatigue=_RETAIL_FATIGUE,
    ))

# ─── LIVESTOCK / AQUACULTURE ─────────────────────────────────────

_LIVESTOCK_SHIFT = ShiftProfile(
    shift_type="daylight_only", shift_duration_hours=10,
    shifts_per_day=1, active_days_per_week=7,
    peak_hours=[5, 6, 7, 8, 16, 17, 18],
    dead_hours=[0, 1, 2, 3, 22, 23],
    seasonal_shutdown_weeks=0, night_activity_level=0.25,
    handover_overlap_minutes=0,
)

_LIVESTOCK_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0018, degradation_variance=1.4,
    maintenance_recovery=0.10, catastrophic_failure_prob=0.0008,
    thermal_stress_factor=1.6, corrosion_factor=1.8,
    vibration_sensitivity=0.5, typical_rul_hours=4000,
    maintenance_interval_events=250,
)

_LIVESTOCK_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=1.9, humidity_sensitivity=1.5,
    rain_stop_probability=0.3, wind_sensitivity=0.2,
    dust_sensitivity=0.4, power_grid_dependency=0.5,
    seasonal_demand_amplitude=0.4, monsoon_impact=0.5,
)

_LIVESTOCK_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=300, downtime_cost_multiplier=2.0,
    material_cost_pct=0.50, energy_cost_pct=0.08,
    labor_cost_pct=0.25, inventory_sensitivity=0.9,
    sla_penalty_severity=0.3, demand_volatility=0.3,
    industry_scale="small",
)

_LIVESTOCK_CASCADE = CascadeProfile(
    cascade_probability=0.35, cascade_delay_events=(5, 30),
    primary_cascade_types=["disease_spread", "supply_contamination", "mass_mortality"],
    supplier_dependency=0.6, single_point_failures=["feed_system", "water_pump", "climate_control"],
    recovery_time_events=(20, 200),
)

_LIVESTOCK_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.18,
    night_shift_penalty=0.20, overtime_threshold_hours=10,
    overtime_error_multiplier=1.8, physical_labor_fatigue_rate=0.035,
    monitoring_vigilance_decay=0.015, break_recovery_factor=0.6,
)

for _lid in ["poultry_farming", "dairy_farming", "shrimp_farming"]:
    _profile(IndustrySimProfile(
        industry_id=_lid, sector="A_primary",
        shift=_LIVESTOCK_SHIFT, degradation=_LIVESTOCK_DEGRADATION,
        environment=_LIVESTOCK_ENVIRONMENT, economics=_LIVESTOCK_ECONOMICS,
        cascade=_LIVESTOCK_CASCADE, fatigue=_LIVESTOCK_FATIGUE,
    ))


# ─── TIMBER / FORESTRY ──────────────────────────────────────────

_TIMBER_SHIFT = ShiftProfile(
    shift_type="daylight_only", shift_duration_hours=9,
    shifts_per_day=1, active_days_per_week=5,
    peak_hours=[7, 8, 9, 10, 11, 14, 15],
    dead_hours=[0, 1, 2, 3, 4, 5, 19, 20, 21, 22, 23],
    seasonal_shutdown_weeks=4, night_activity_level=0.0,
    handover_overlap_minutes=0,
)

_TIMBER_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.003, degradation_variance=1.8,
    maintenance_recovery=0.12, catastrophic_failure_prob=0.002,
    thermal_stress_factor=0.8, corrosion_factor=0.5,
    vibration_sensitivity=1.8, typical_rul_hours=2000,
    maintenance_interval_events=150,
)

_TIMBER_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.8, humidity_sensitivity=0.4,
    rain_stop_probability=0.8, wind_sensitivity=0.7,
    dust_sensitivity=0.3, power_grid_dependency=0.2,
    seasonal_demand_amplitude=0.6, monsoon_impact=0.9,
)

_TIMBER_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=500, downtime_cost_multiplier=1.2,
    material_cost_pct=0.10, energy_cost_pct=0.15,
    labor_cost_pct=0.45, inventory_sensitivity=0.3,
    sla_penalty_severity=0.2, demand_volatility=0.5,
    industry_scale="small",
)

_TIMBER_CASCADE = CascadeProfile(
    cascade_probability=0.20, cascade_delay_events=(10, 40),
    primary_cascade_types=["safety_risk", "equipment_damage", "environmental_impact"],
    supplier_dependency=0.2, single_point_failures=["chainsaw", "skidder", "loader"],
    recovery_time_events=(5, 30),
)

_TIMBER_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.15,
    night_shift_penalty=0.25, overtime_threshold_hours=9,
    overtime_error_multiplier=2.5, physical_labor_fatigue_rate=0.05,
    monitoring_vigilance_decay=0.01, break_recovery_factor=0.7,
)

_profile(IndustrySimProfile(
    industry_id="timber_logging", sector="A_primary",
    shift=_TIMBER_SHIFT, degradation=_TIMBER_DEGRADATION,
    environment=_TIMBER_ENVIRONMENT, economics=_TIMBER_ECONOMICS,
    cascade=_TIMBER_CASCADE, fatigue=_TIMBER_FATIGUE,
))


# ─── AEROSPACE ──────────────────────────────────────────────────

_AERO_SHIFT = ShiftProfile(
    shift_type="two_shift", shift_duration_hours=10,
    shifts_per_day=2, active_days_per_week=5,
    peak_hours=[7, 8, 9, 10, 11, 14, 15, 16],
    dead_hours=[0, 1, 2, 3, 4, 5, 23],
    seasonal_shutdown_weeks=2, night_activity_level=0.4,
    handover_overlap_minutes=30,
)

_AERO_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0003, degradation_variance=0.5,
    maintenance_recovery=0.15, catastrophic_failure_prob=0.00005,
    thermal_stress_factor=1.0, corrosion_factor=0.8,
    vibration_sensitivity=0.6, typical_rul_hours=50000,
    maintenance_interval_events=3000,
)

_AERO_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.2, humidity_sensitivity=0.3,
    rain_stop_probability=0.0, wind_sensitivity=0.0,
    dust_sensitivity=0.05, power_grid_dependency=0.8,
    seasonal_demand_amplitude=0.1, monsoon_impact=0.0,
)

_AERO_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=100000, downtime_cost_multiplier=2.0,
    material_cost_pct=0.55, energy_cost_pct=0.03,
    labor_cost_pct=0.30, inventory_sensitivity=0.9,
    sla_penalty_severity=0.9, demand_volatility=0.2,
    industry_scale="large",
)

_AERO_CASCADE = CascadeProfile(
    cascade_probability=0.15, cascade_delay_events=(5, 30),
    primary_cascade_types=["certification_delay", "quality_recall", "supply_stop"],
    supplier_dependency=0.85, single_point_failures=["autoclave", "cnc_5axis", "test_chamber"],
    recovery_time_events=(30, 200),
)

_AERO_FATIGUE = FatigueProfile(
    peak_alertness_hour=3, post_lunch_dip=0.10,
    night_shift_penalty=0.10, overtime_threshold_hours=10,
    overtime_error_multiplier=2.5, physical_labor_fatigue_rate=0.02,
    monitoring_vigilance_decay=0.03, break_recovery_factor=0.5,
)

for _aid in ["aerospace_assembly", "satellite_manufacturing"]:
    _profile(IndustrySimProfile(
        industry_id=_aid, sector="C_manufacturing",
        shift=_AERO_SHIFT, degradation=_AERO_DEGRADATION,
        environment=_AERO_ENVIRONMENT, economics=_AERO_ECONOMICS,
        cascade=_AERO_CASCADE, fatigue=_AERO_FATIGUE,
    ))


# ─── BATTERY / ENERGY STORAGE ───────────────────────────────────

_BATTERY_SHIFT = ShiftProfile(
    shift_type="continuous_24_7", shift_duration_hours=8,
    shifts_per_day=3, active_days_per_week=7,
    peak_hours=[7, 8, 9, 10, 14, 15, 16],
    dead_hours=[2, 3, 4],
    seasonal_shutdown_weeks=0, night_activity_level=0.7,
    handover_overlap_minutes=20,
)

_BATTERY_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0008, degradation_variance=0.9,
    maintenance_recovery=0.10, catastrophic_failure_prob=0.0008,
    thermal_stress_factor=1.8, corrosion_factor=1.5,
    vibration_sensitivity=0.5, typical_rul_hours=12000,
    maintenance_interval_events=600,
)

_BATTERY_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=1.5, humidity_sensitivity=1.2,
    rain_stop_probability=0.0, wind_sensitivity=0.0,
    dust_sensitivity=0.2, power_grid_dependency=0.9,
    seasonal_demand_amplitude=0.2, monsoon_impact=0.05,
)

_BATTERY_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=25000, downtime_cost_multiplier=2.0,
    material_cost_pct=0.65, energy_cost_pct=0.12,
    labor_cost_pct=0.10, inventory_sensitivity=0.8,
    sla_penalty_severity=0.7, demand_volatility=0.5,
    industry_scale="large",
)

_BATTERY_CASCADE = CascadeProfile(
    cascade_probability=0.35, cascade_delay_events=(2, 12),
    primary_cascade_types=["thermal_runaway", "contamination", "supply_stop"],
    supplier_dependency=0.9, single_point_failures=["dry_room", "electrode_coater", "formation_chamber"],
    recovery_time_events=(10, 60),
)

_BATTERY_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.12,
    night_shift_penalty=0.15, overtime_threshold_hours=8,
    overtime_error_multiplier=2.2, physical_labor_fatigue_rate=0.02,
    monitoring_vigilance_decay=0.03, break_recovery_factor=0.55,
)

_profile(IndustrySimProfile(
    industry_id="battery_manufacturing", sector="C_manufacturing",
    shift=_BATTERY_SHIFT, degradation=_BATTERY_DEGRADATION,
    environment=_BATTERY_ENVIRONMENT, economics=_BATTERY_ECONOMICS,
    cascade=_BATTERY_CASCADE, fatigue=_BATTERY_FATIGUE,
))


# ─── ALUMINUM SMELTING ──────────────────────────────────────────

_ALUM_SHIFT = ShiftProfile(
    shift_type="continuous_24_7", shift_duration_hours=8,
    shifts_per_day=3, active_days_per_week=7,
    peak_hours=[6, 7, 8, 14, 15, 22],
    dead_hours=[3, 4],
    seasonal_shutdown_weeks=0, night_activity_level=0.9,
    handover_overlap_minutes=20,
)

_ALUM_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.002, degradation_variance=1.3,
    maintenance_recovery=0.07, catastrophic_failure_prob=0.001,
    thermal_stress_factor=2.0, corrosion_factor=2.2,
    vibration_sensitivity=1.0, typical_rul_hours=8000,
    maintenance_interval_events=600,
)

_ALUM_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.4, humidity_sensitivity=0.6,
    rain_stop_probability=0.0, wind_sensitivity=0.0,
    dust_sensitivity=0.8, power_grid_dependency=1.0,
    seasonal_demand_amplitude=0.15, monsoon_impact=0.05,
)

_ALUM_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=35000, downtime_cost_multiplier=3.0,
    material_cost_pct=0.40, energy_cost_pct=0.35,
    labor_cost_pct=0.08, inventory_sensitivity=0.5,
    sla_penalty_severity=0.5, demand_volatility=0.3,
    industry_scale="large",
)

_ALUM_CASCADE = CascadeProfile(
    cascade_probability=0.40, cascade_delay_events=(2, 8),
    primary_cascade_types=["pot_failure", "power_disruption", "environmental_release"],
    supplier_dependency=0.6, single_point_failures=["potline", "rectifier", "anode_plant"],
    recovery_time_events=(10, 150),
)

_ALUM_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.15,
    night_shift_penalty=0.18, overtime_threshold_hours=8,
    overtime_error_multiplier=2.3, physical_labor_fatigue_rate=0.04,
    monitoring_vigilance_decay=0.025, break_recovery_factor=0.5,
)

_profile(IndustrySimProfile(
    industry_id="aluminum_smelting", sector="B_processing",
    shift=_ALUM_SHIFT, degradation=_ALUM_DEGRADATION,
    environment=_ALUM_ENVIRONMENT, economics=_ALUM_ECONOMICS,
    cascade=_ALUM_CASCADE, fatigue=_ALUM_FATIGUE,
))


# ─── FOOD / BEVERAGE SMALL ──────────────────────────────────────

_FOOD_SMALL_SHIFT = ShiftProfile(
    shift_type="two_shift", shift_duration_hours=8,
    shifts_per_day=2, active_days_per_week=6,
    peak_hours=[5, 6, 7, 8, 9, 14, 15],
    dead_hours=[0, 1, 2, 3, 22, 23],
    seasonal_shutdown_weeks=1, night_activity_level=0.3,
    handover_overlap_minutes=10,
)

_FOOD_SMALL_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0015, degradation_variance=1.2,
    maintenance_recovery=0.12, catastrophic_failure_prob=0.0006,
    thermal_stress_factor=1.0, corrosion_factor=1.5,
    vibration_sensitivity=0.8, typical_rul_hours=5000,
    maintenance_interval_events=300,
)

_FOOD_SMALL_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=1.2, humidity_sensitivity=1.0,
    rain_stop_probability=0.05, wind_sensitivity=0.0,
    dust_sensitivity=0.2, power_grid_dependency=0.8,
    seasonal_demand_amplitude=0.4, monsoon_impact=0.1,
)

_FOOD_SMALL_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=2000, downtime_cost_multiplier=1.8,
    material_cost_pct=0.45, energy_cost_pct=0.10,
    labor_cost_pct=0.25, inventory_sensitivity=0.85,
    sla_penalty_severity=0.4, demand_volatility=0.5,
    industry_scale="medium",
)

_FOOD_SMALL_CASCADE = CascadeProfile(
    cascade_probability=0.30, cascade_delay_events=(3, 15),
    primary_cascade_types=["contamination", "spoilage", "recall"],
    supplier_dependency=0.7, single_point_failures=["oven", "mixer", "cold_storage"],
    recovery_time_events=(5, 40),
)

_FOOD_SMALL_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.15,
    night_shift_penalty=0.15, overtime_threshold_hours=8,
    overtime_error_multiplier=1.8, physical_labor_fatigue_rate=0.03,
    monitoring_vigilance_decay=0.02, break_recovery_factor=0.6,
)

for _fid in ["brewery", "bakery_factory"]:
    _profile(IndustrySimProfile(
        industry_id=_fid, sector="C_manufacturing",
        shift=_FOOD_SMALL_SHIFT, degradation=_FOOD_SMALL_DEGRADATION,
        environment=_FOOD_SMALL_ENVIRONMENT, economics=_FOOD_SMALL_ECONOMICS,
        cascade=_FOOD_SMALL_CASCADE, fatigue=_FOOD_SMALL_FATIGUE,
    ))


# ─── CALL CENTER / BPO ──────────────────────────────────────────

_CALLCENTER_SHIFT = ShiftProfile(
    shift_type="continuous_24_7", shift_duration_hours=9,
    shifts_per_day=3, active_days_per_week=7,
    peak_hours=[9, 10, 11, 14, 15, 16, 19, 20],
    dead_hours=[2, 3, 4, 5],
    seasonal_shutdown_weeks=0, night_activity_level=0.6,
    handover_overlap_minutes=15,
)

_CALLCENTER_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.0003, degradation_variance=0.5,
    maintenance_recovery=0.15, catastrophic_failure_prob=0.0001,
    thermal_stress_factor=0.1, corrosion_factor=0.0,
    vibration_sensitivity=0.1, typical_rul_hours=40000,
    maintenance_interval_events=5000,
)

_CALLCENTER_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.1, humidity_sensitivity=0.1,
    rain_stop_probability=0.0, wind_sensitivity=0.0,
    dust_sensitivity=0.0, power_grid_dependency=0.95,
    seasonal_demand_amplitude=0.3, monsoon_impact=0.0,
)

_CALLCENTER_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=3000, downtime_cost_multiplier=1.5,
    material_cost_pct=0.05, energy_cost_pct=0.08,
    labor_cost_pct=0.65, inventory_sensitivity=0.1,
    sla_penalty_severity=0.8, demand_volatility=0.4,
    industry_scale="medium",
)

_CALLCENTER_CASCADE = CascadeProfile(
    cascade_probability=0.20, cascade_delay_events=(1, 5),
    primary_cascade_types=["sla_breach", "customer_churn", "staff_burnout"],
    supplier_dependency=0.3, single_point_failures=["pbx_system", "network_switch", "crm_server"],
    recovery_time_events=(2, 15),
)

_CALLCENTER_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.12,
    night_shift_penalty=0.20, overtime_threshold_hours=9,
    overtime_error_multiplier=2.0, physical_labor_fatigue_rate=0.01,
    monitoring_vigilance_decay=0.04, break_recovery_factor=0.7,
)

_profile(IndustrySimProfile(
    industry_id="call_center", sector="H_services",
    shift=_CALLCENTER_SHIFT, degradation=_CALLCENTER_DEGRADATION,
    environment=_CALLCENTER_ENVIRONMENT, economics=_CALLCENTER_ECONOMICS,
    cascade=_CALLCENTER_CASCADE, fatigue=_CALLCENTER_FATIGUE,
))


# ─── BIOGAS / SMALL POWER ───────────────────────────────────────

_BIOGAS_SHIFT = ShiftProfile(
    shift_type="two_shift", shift_duration_hours=10,
    shifts_per_day=2, active_days_per_week=7,
    peak_hours=[6, 7, 8, 9, 16, 17, 18],
    dead_hours=[1, 2, 3, 4],
    seasonal_shutdown_weeks=0, night_activity_level=0.4,
    handover_overlap_minutes=15,
)

_BIOGAS_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.002, degradation_variance=1.5,
    maintenance_recovery=0.10, catastrophic_failure_prob=0.001,
    thermal_stress_factor=1.2, corrosion_factor=2.0,
    vibration_sensitivity=1.0, typical_rul_hours=6000,
    maintenance_interval_events=300,
)

_BIOGAS_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=1.3, humidity_sensitivity=1.0,
    rain_stop_probability=0.2, wind_sensitivity=0.1,
    dust_sensitivity=0.3, power_grid_dependency=0.4,
    seasonal_demand_amplitude=0.5, monsoon_impact=0.4,
)

_BIOGAS_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=800, downtime_cost_multiplier=1.5,
    material_cost_pct=0.30, energy_cost_pct=0.05,
    labor_cost_pct=0.30, inventory_sensitivity=0.6,
    sla_penalty_severity=0.3, demand_volatility=0.4,
    industry_scale="small",
)

_BIOGAS_CASCADE = CascadeProfile(
    cascade_probability=0.25, cascade_delay_events=(5, 20),
    primary_cascade_types=["feedstock_shortage", "gas_leak", "digester_failure"],
    supplier_dependency=0.7, single_point_failures=["digester", "gas_holder", "generator"],
    recovery_time_events=(10, 60),
)

_BIOGAS_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.18,
    night_shift_penalty=0.18, overtime_threshold_hours=10,
    overtime_error_multiplier=1.8, physical_labor_fatigue_rate=0.03,
    monitoring_vigilance_decay=0.02, break_recovery_factor=0.6,
)

_profile(IndustrySimProfile(
    industry_id="biogas_plant", sector="D_energy",
    shift=_BIOGAS_SHIFT, degradation=_BIOGAS_DEGRADATION,
    environment=_BIOGAS_ENVIRONMENT, economics=_BIOGAS_ECONOMICS,
    cascade=_BIOGAS_CASCADE, fatigue=_BIOGAS_FATIGUE,
))


# ─── DEFAULT PROFILE (for industries without specific params) ───

_DEFAULT_SHIFT = ShiftProfile(
    shift_type="two_shift", shift_duration_hours=8,
    shifts_per_day=2, active_days_per_week=6,
    peak_hours=[7, 8, 9, 10, 11, 14, 15, 16],
    dead_hours=[0, 1, 2, 3, 4, 5],
    seasonal_shutdown_weeks=1, night_activity_level=0.5,
    handover_overlap_minutes=15,
)

_DEFAULT_DEGRADATION = DegradationProfile(
    base_degradation_rate=0.001, degradation_variance=1.2,
    maintenance_recovery=0.10, catastrophic_failure_prob=0.0005,
    thermal_stress_factor=1.0, corrosion_factor=1.0,
    vibration_sensitivity=1.0, typical_rul_hours=5000,
    maintenance_interval_events=400,
)

_DEFAULT_ENVIRONMENT = EnvironmentProfile(
    temperature_sensitivity=0.5, humidity_sensitivity=0.5,
    rain_stop_probability=0.1, wind_sensitivity=0.2,
    dust_sensitivity=0.3, power_grid_dependency=0.7,
    seasonal_demand_amplitude=0.3, monsoon_impact=0.2,
)

_DEFAULT_ECONOMICS = EconomicProfile(
    revenue_per_hour_usd=5000, downtime_cost_multiplier=1.5,
    material_cost_pct=0.35, energy_cost_pct=0.10,
    labor_cost_pct=0.25, inventory_sensitivity=0.5,
    sla_penalty_severity=0.4, demand_volatility=0.4,
    industry_scale="medium",
)

_DEFAULT_CASCADE = CascadeProfile(
    cascade_probability=0.30, cascade_delay_events=(5, 25),
    primary_cascade_types=["downstream_production_stop", "quality_degradation"],
    supplier_dependency=0.5, single_point_failures=[],
    recovery_time_events=(10, 50),
)

_DEFAULT_FATIGUE = FatigueProfile(
    peak_alertness_hour=2, post_lunch_dip=0.15,
    night_shift_penalty=0.15, overtime_threshold_hours=8,
    overtime_error_multiplier=2.0, physical_labor_fatigue_rate=0.03,
    monitoring_vigilance_decay=0.02, break_recovery_factor=0.6,
)

DEFAULT_PROFILE = IndustrySimProfile(
    industry_id="_default", sector="unknown",
    shift=_DEFAULT_SHIFT, degradation=_DEFAULT_DEGRADATION,
    environment=_DEFAULT_ENVIRONMENT, economics=_DEFAULT_ECONOMICS,
    cascade=_DEFAULT_CASCADE, fatigue=_DEFAULT_FATIGUE,
)


def get_industry_profile(industry_id: str) -> IndustrySimProfile:
    """Get the simulation profile for an industry. Falls back to default."""
    return INDUSTRY_PROFILES.get(industry_id, DEFAULT_PROFILE)


def get_all_profiled_industries() -> List[str]:
    """Get list of industries that have specific profiles."""
    return list(INDUSTRY_PROFILES.keys())
