"""
Ecosystem Simulation Engine
=============================
Transforms isolated industry simulations into an interconnected industrial ecosystem.

Phase 1: Industry Dependency Graph
Phase 2: Market Dynamics Engine
Phase 3: Regional World Model
Phase 4: Enterprise Lifecycle
Phase 5: Black Swan / Shock Propagation

This module makes industries AFFECT each other:
- Oil price spike → transport costs rise → all industries feel pressure
- Steel shortage → automotive line stops → dealer inventory drops
- Port shutdown → import-dependent industries halt within days
- Pandemic → labor availability crashes → all industries degrade
"""
import random
import math
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════════
# PHASE 1: INDUSTRY DEPENDENCY GRAPH
# ═══════════════════════════════════════════════════════════════════

@dataclass
class DependencyLink:
    """A directed dependency between two industries."""
    source_industry: str       # Industry that provides
    target_industry: str       # Industry that depends
    dependency_type: str       # "material", "energy", "labor", "logistics", "infrastructure"
    strength: float            # 0.0 (weak) to 1.0 (critical)
    lead_time_days: float      # How quickly disruption propagates
    substitutability: float    # 0.0 (no alternative) to 1.0 (easily replaced)


class IndustryDependencyGraph:
    """Models how industries depend on and affect each other.
    
    This is NOT a static data structure. It's a live simulation component
    that propagates state changes across industries.
    
    When oil_refining has a disruption:
      → transport costs rise (strength=0.8, lead_time=2 days)
      → petrochemical feed drops (strength=0.9, lead_time=1 day)
      → power generation affected (strength=0.5, lead_time=3 days)
    
    When steel_rolling has a shortage:
      → automotive can't get panels (strength=0.7, lead_time=7 days)
      → construction slows (strength=0.6, lead_time=14 days)
    """
    
    def __init__(self):
        self.links: List[DependencyLink] = []
        self.upstream_map: Dict[str, List[DependencyLink]] = defaultdict(list)
        self.downstream_map: Dict[str, List[DependencyLink]] = defaultdict(list)
        self._build_graph()
    
    def _build_graph(self):
        """Build the complete industry dependency graph."""
        
        # ─── ENERGY DEPENDENCIES ────────────────────────────────
        # Oil & Gas → Almost everything (energy supply)
        self._link("oil_refining", "automobile_assembly", "energy", 0.6, 3, 0.3)
        self._link("oil_refining", "logistics_warehouse", "energy", 0.8, 2, 0.2)
        self._link("oil_refining", "road_construction", "material", 0.7, 5, 0.2)
        self._link("oil_refining", "rice_farming", "energy", 0.4, 3, 0.5)
        self._link("oil_refining", "steel_rolling", "energy", 0.5, 3, 0.4)
        self._link("oil_refining", "cement_manufacturing", "energy", 0.5, 3, 0.4)
        self._link("oil_refining", "cotton_spinning", "energy", 0.4, 3, 0.5)
        self._link("oil_refining", "hospital", "energy", 0.3, 1, 0.7)
        
        # Power generation → All electricity-dependent industries
        self._link("thermal_power_plant", "semiconductor_fab", "infrastructure", 0.95, 0.01, 0.1)
        self._link("thermal_power_plant", "data_center", "infrastructure", 0.95, 0.01, 0.2)
        self._link("thermal_power_plant", "steel_rolling", "infrastructure", 0.7, 0.1, 0.3)
        self._link("thermal_power_plant", "hospital", "infrastructure", 0.9, 0.01, 0.3)
        self._link("thermal_power_plant", "automobile_assembly", "infrastructure", 0.8, 0.1, 0.2)
        
        # ─── MATERIAL SUPPLY CHAINS ────────────────────────────
        # Steel → Automotive, Construction, Machinery
        self._link("steel_rolling", "automobile_assembly", "material", 0.7, 7, 0.3)
        self._link("steel_rolling", "road_construction", "material", 0.6, 14, 0.4)
        self._link("steel_rolling", "aerospace_assembly", "material", 0.5, 21, 0.4)
        
        # Mining → Steel, Cement, Power
        self._link("iron_ore_mining", "steel_rolling", "material", 0.9, 14, 0.2)
        self._link("coal_mining", "steel_rolling", "material", 0.8, 10, 0.3)
        self._link("coal_mining", "thermal_power_plant", "material", 0.9, 7, 0.2)
        self._link("coal_mining", "cement_manufacturing", "material", 0.6, 10, 0.4)
        
        # Agriculture → Food Processing
        self._link("rice_farming", "rice_milling", "material", 0.95, 1, 0.1)
        self._link("sugarcane_farming", "sugar_milling", "material", 0.95, 1, 0.1)
        self._link("wheat_farming", "rice_milling", "material", 0.5, 3, 0.5)
        self._link("dairy_farming", "hospital", "material", 0.2, 2, 0.7)
        self._link("poultry_farming", "restaurant_kitchen", "material", 0.4, 1, 0.5)
        
        # Cotton → Textile
        self._link("rice_farming", "cotton_spinning", "material", 0.0, 0, 1.0)  # No link (different crop)
        
        # Chemicals → Pharma, Agriculture, Manufacturing
        self._link("oil_refining", "pharmaceutical_tablet", "material", 0.4, 7, 0.5)
        self._link("oil_refining", "electronics_pcb", "material", 0.3, 10, 0.5)
        
        # ─── LOGISTICS DEPENDENCIES ────────────────────────────
        # Ports/Logistics → Import-dependent industries
        self._link("logistics_warehouse", "automobile_assembly", "logistics", 0.6, 3, 0.3)
        self._link("logistics_warehouse", "electronics_pcb", "logistics", 0.7, 5, 0.3)
        self._link("logistics_warehouse", "supermarket_retail", "logistics", 0.5, 2, 0.4)
        self._link("logistics_warehouse", "pharmaceutical_tablet", "logistics", 0.5, 3, 0.4)
        
        # ─── LABOR POOL DEPENDENCIES ──────────────────────────
        # Shared labor pools (when one industry booms, others lose workers)
        self._link("road_construction", "steel_rolling", "labor", 0.2, 30, 0.6)
        self._link("road_construction", "cement_manufacturing", "labor", 0.3, 30, 0.5)
        self._link("software_company", "data_center", "labor", 0.3, 60, 0.5)
        self._link("rice_farming", "road_construction", "labor", 0.4, 7, 0.4)
        
        # ─── INFRASTRUCTURE SHARED ─────────────────────────────
        # Water supply shared
        self._link("rice_farming", "steel_rolling", "infrastructure", 0.1, 30, 0.8)
        self._link("rice_farming", "thermal_power_plant", "infrastructure", 0.2, 14, 0.6)
        
        # Build index maps
        for link in self.links:
            self.upstream_map[link.target_industry].append(link)
            self.downstream_map[link.source_industry].append(link)
    
    def _link(self, source: str, target: str, dep_type: str, 
              strength: float, lead_time: float, substitutability: float):
        """Add a dependency link."""
        if strength > 0:
            link = DependencyLink(source, target, dep_type, strength, lead_time, substitutability)
            self.links.append(link)
    
    def get_upstream_dependencies(self, industry_id: str) -> List[DependencyLink]:
        """What does this industry depend ON?"""
        return self.upstream_map.get(industry_id, [])
    
    def get_downstream_dependents(self, industry_id: str) -> List[DependencyLink]:
        """What depends on this industry?"""
        return self.downstream_map.get(industry_id, [])
    
    def propagate_disruption(self, source_industry: str, disruption_severity: float,
                             rng: random.Random) -> List[Dict]:
        """Propagate a disruption from one industry to its dependents.
        
        Returns list of downstream impacts with timing and severity.
        """
        impacts = []
        visited = {source_industry}
        queue = [(source_industry, disruption_severity, 0)]  # (industry, severity, depth)
        
        while queue:
            current, severity, depth = queue.pop(0)
            if depth > 3:  # Max 3 hops of propagation
                continue
            
            for link in self.get_downstream_dependents(current):
                if link.target_industry in visited:
                    continue
                
                # Calculate impact: severity × strength × (1 - substitutability)
                impact_strength = severity * link.strength * (1.0 - link.substitutability)
                
                # Add randomness
                impact_strength *= rng.uniform(0.7, 1.3)
                
                if impact_strength > 0.05:  # Only propagate meaningful impacts
                    impact = {
                        "target_industry": link.target_industry,
                        "source_chain": [source_industry, current] if current != source_industry else [source_industry],
                        "impact_severity": round(min(1.0, impact_strength), 3),
                        "dependency_type": link.dependency_type,
                        "lead_time_days": link.lead_time_days,
                        "depth": depth + 1,
                    }
                    impacts.append(impact)
                    visited.add(link.target_industry)
                    
                    # Continue propagation if strong enough
                    if impact_strength > 0.2:
                        queue.append((link.target_industry, impact_strength * 0.6, depth + 1))
        
        return impacts
    
    def get_dependency_summary(self, industry_id: str) -> Dict:
        """Get a summary of all dependencies for one industry."""
        upstream = self.get_upstream_dependencies(industry_id)
        downstream = self.get_downstream_dependents(industry_id)
        
        return {
            "industry": industry_id,
            "depends_on": [
                {"source": l.source_industry, "type": l.dependency_type, "strength": l.strength}
                for l in sorted(upstream, key=lambda x: -x.strength)
            ],
            "supplies_to": [
                {"target": l.target_industry, "type": l.dependency_type, "strength": l.strength}
                for l in sorted(downstream, key=lambda x: -x.strength)
            ],
            "critical_upstream": [l.source_industry for l in upstream if l.strength > 0.7],
            "vulnerability_score": sum(l.strength * (1 - l.substitutability) for l in upstream) / max(1, len(upstream)),
        }



# ═══════════════════════════════════════════════════════════════════
# PHASE 2: MARKET DYNAMICS ENGINE
# ═══════════════════════════════════════════════════════════════════

@dataclass
class MarketState:
    """Live market conditions that affect all industries."""
    # Commodity prices (index: 1.0 = normal)
    oil_price_index: float = 1.0
    steel_price_index: float = 1.0
    food_price_index: float = 1.0
    energy_price_index: float = 1.0
    
    # Labor market
    labor_availability: float = 1.0  # 1.0 = normal, 0.5 = severe shortage
    wage_pressure: float = 0.0  # 0.0 = stable, 1.0 = extreme inflation
    
    # Logistics
    shipping_cost_index: float = 1.0
    port_congestion: float = 0.0  # 0.0 = clear, 1.0 = severe
    
    # Finance
    interest_rate_index: float = 1.0  # 1.0 = normal, 2.0 = high rates
    credit_availability: float = 1.0  # 1.0 = easy, 0.0 = frozen
    
    # Demand
    global_demand_index: float = 1.0  # 1.0 = normal, 0.7 = recession, 1.3 = boom


class MarketDynamicsEngine:
    """Simulates market-level feedback loops that affect all industries.
    
    This is the ECOSYSTEM layer. Individual industries don't just have
    internal state — they respond to and contribute to market conditions.
    
    Key dynamics:
    - Supply shortage → price rises → demand destruction → price falls
    - Demand boom → capacity strain → quality drops → customer loss
    - Cost inflation → margin squeeze → investment cut → productivity drop
    - Credit tightening → capex freeze → aging equipment → more failures
    """
    
    def __init__(self, rng: random.Random, initial_conditions: Dict = None):
        self.rng = rng
        self.state = MarketState(**(initial_conditions or {}))
        self.tick_count = 0
        self.price_history: List[Dict] = []
        self._momentum = defaultdict(float)  # Price momentum (trend following)
    
    def tick(self, industry_states: Dict[str, Dict] = None):
        """Advance market state by one time step.
        
        industry_states: {industry_id: {production_rate, demand, inventory_level, ...}}
        """
        self.tick_count += 1
        
        # Random market noise (small daily fluctuations)
        self._apply_noise()
        
        # Mean reversion (prices tend back toward 1.0 over time)
        self._apply_mean_reversion()
        
        # Momentum (trends persist for a while)
        self._apply_momentum()
        
        # Industry feedback (if states provided)
        if industry_states:
            self._process_industry_feedback(industry_states)
        
        # Clamp all values to reasonable ranges
        self._clamp_state()
        
        # Record history
        self.price_history.append(self.get_snapshot())
        if len(self.price_history) > 200:
            self.price_history = self.price_history[-200:]
    
    def _apply_noise(self):
        """Small random fluctuations (daily market noise)."""
        self.state.oil_price_index += self.rng.gauss(0, 0.005)
        self.state.steel_price_index += self.rng.gauss(0, 0.003)
        self.state.food_price_index += self.rng.gauss(0, 0.004)
        self.state.energy_price_index += self.rng.gauss(0, 0.004)
        self.state.shipping_cost_index += self.rng.gauss(0, 0.003)
        self.state.labor_availability += self.rng.gauss(0, 0.002)
        self.state.global_demand_index += self.rng.gauss(0, 0.002)
    
    def _apply_mean_reversion(self):
        """Prices revert toward equilibrium over time."""
        reversion_rate = 0.002
        self.state.oil_price_index += (1.0 - self.state.oil_price_index) * reversion_rate
        self.state.steel_price_index += (1.0 - self.state.steel_price_index) * reversion_rate
        self.state.food_price_index += (1.0 - self.state.food_price_index) * reversion_rate
        self.state.energy_price_index += (1.0 - self.state.energy_price_index) * reversion_rate
        self.state.shipping_cost_index += (1.0 - self.state.shipping_cost_index) * reversion_rate
        self.state.labor_availability += (1.0 - self.state.labor_availability) * reversion_rate
        self.state.global_demand_index += (1.0 - self.state.global_demand_index) * reversion_rate
    
    def _apply_momentum(self):
        """Price trends persist (momentum effect)."""
        for attr in ['oil_price_index', 'steel_price_index', 'food_price_index', 'energy_price_index']:
            current = getattr(self.state, attr)
            if len(self.price_history) > 5:
                past = self.price_history[-5].get(attr, 1.0)
                trend = (current - past) / 5.0
                self._momentum[attr] = self._momentum[attr] * 0.9 + trend * 0.1
                setattr(self.state, attr, current + self._momentum[attr] * 0.5)
    
    def _process_industry_feedback(self, industry_states: Dict[str, Dict]):
        """Industries affect market conditions."""
        for iid, state in industry_states.items():
            prod_rate = state.get("production_rate", 1.0)
            
            # Low production → supply shortage → price increase
            if "oil" in iid or "refin" in iid:
                if prod_rate < 0.8:
                    self.state.oil_price_index += 0.01 * (0.8 - prod_rate)
                    self.state.energy_price_index += 0.005 * (0.8 - prod_rate)
            
            if "steel" in iid or "iron" in iid:
                if prod_rate < 0.8:
                    self.state.steel_price_index += 0.008 * (0.8 - prod_rate)
            
            if "farm" in iid or "agri" in iid:
                if prod_rate < 0.7:
                    self.state.food_price_index += 0.01 * (0.7 - prod_rate)
    
    def _clamp_state(self):
        """Keep values in reasonable ranges."""
        self.state.oil_price_index = max(0.3, min(3.0, self.state.oil_price_index))
        self.state.steel_price_index = max(0.4, min(2.5, self.state.steel_price_index))
        self.state.food_price_index = max(0.5, min(3.0, self.state.food_price_index))
        self.state.energy_price_index = max(0.3, min(3.0, self.state.energy_price_index))
        self.state.shipping_cost_index = max(0.5, min(4.0, self.state.shipping_cost_index))
        self.state.labor_availability = max(0.3, min(1.2, self.state.labor_availability))
        self.state.wage_pressure = max(0.0, min(1.0, self.state.wage_pressure))
        self.state.port_congestion = max(0.0, min(1.0, self.state.port_congestion))
        self.state.global_demand_index = max(0.5, min(1.5, self.state.global_demand_index))
        self.state.interest_rate_index = max(0.5, min(3.0, self.state.interest_rate_index))
        self.state.credit_availability = max(0.1, min(1.2, self.state.credit_availability))
    
    def get_industry_cost_modifier(self, industry_id: str) -> Dict[str, float]:
        """Get market-driven cost modifiers for a specific industry."""
        modifiers = {
            "energy_cost_multiplier": self.state.energy_price_index,
            "material_cost_multiplier": 1.0,
            "logistics_cost_multiplier": self.state.shipping_cost_index,
            "labor_cost_multiplier": 1.0 + self.state.wage_pressure * 0.3,
            "demand_multiplier": self.state.global_demand_index,
            "credit_multiplier": self.state.credit_availability,
        }
        
        # Industry-specific material cost sensitivity
        if "steel" in industry_id or "auto" in industry_id:
            modifiers["material_cost_multiplier"] = self.state.steel_price_index
        elif "farm" in industry_id or "food" in industry_id or "mill" in industry_id:
            modifiers["material_cost_multiplier"] = self.state.food_price_index
        elif "refin" in industry_id or "petro" in industry_id:
            modifiers["material_cost_multiplier"] = self.state.oil_price_index
        
        return modifiers
    
    def apply_shock(self, shock_type: str, severity: float):
        """Apply an external market shock."""
        if shock_type == "oil_spike":
            self.state.oil_price_index += severity * 0.5
            self.state.energy_price_index += severity * 0.3
            self.state.shipping_cost_index += severity * 0.2
        elif shock_type == "demand_crash":
            self.state.global_demand_index -= severity * 0.3
            self.state.credit_availability -= severity * 0.2
        elif shock_type == "supply_chain_disruption":
            self.state.shipping_cost_index += severity * 0.6
            self.state.port_congestion += severity * 0.4
        elif shock_type == "labor_crisis":
            self.state.labor_availability -= severity * 0.3
            self.state.wage_pressure += severity * 0.4
        elif shock_type == "inflation":
            self.state.oil_price_index += severity * 0.2
            self.state.food_price_index += severity * 0.2
            self.state.wage_pressure += severity * 0.3
            self.state.interest_rate_index += severity * 0.3
    
    def get_snapshot(self) -> Dict:
        """Get current market state as dict."""
        return {
            "oil_price_index": round(self.state.oil_price_index, 3),
            "steel_price_index": round(self.state.steel_price_index, 3),
            "food_price_index": round(self.state.food_price_index, 3),
            "energy_price_index": round(self.state.energy_price_index, 3),
            "shipping_cost_index": round(self.state.shipping_cost_index, 3),
            "labor_availability": round(self.state.labor_availability, 3),
            "wage_pressure": round(self.state.wage_pressure, 3),
            "port_congestion": round(self.state.port_congestion, 3),
            "global_demand_index": round(self.state.global_demand_index, 3),
            "interest_rate_index": round(self.state.interest_rate_index, 3),
            "credit_availability": round(self.state.credit_availability, 3),
        }



# ═══════════════════════════════════════════════════════════════════
# PHASE 3: REGIONAL WORLD MODEL
# ═══════════════════════════════════════════════════════════════════

@dataclass
class RegionalProfile:
    """How a region modifies industry behavior."""
    region_id: str
    climate_zone: str  # "tropical", "arid", "temperate", "cold", "monsoon"
    power_stability: float  # 0.0 (constant outages) to 1.0 (perfect grid)
    infrastructure_quality: float  # 0.0 (poor roads, no rail) to 1.0 (world-class)
    labor_cost_index: float  # 0.3 (cheap) to 3.0 (expensive)
    regulation_intensity: float  # 0.2 (lax) to 1.0 (strict)
    monsoon_months: List[int]  # Months with monsoon (e.g., [6,7,8,9] for India)
    avg_temperature_c: float  # Annual average
    humidity_avg: float  # 0.0 to 1.0
    earthquake_risk: float  # 0.0 to 1.0
    flood_risk: float  # 0.0 to 1.0
    port_access: bool  # Whether region has major port
    skilled_labor_availability: float  # 0.3 to 1.0


# ─── REGIONAL PROFILES ──────────────────────────────────

REGIONS: Dict[str, RegionalProfile] = {
    # South Asia
    "IN_AP": RegionalProfile("IN_AP", "tropical", 0.7, 0.6, 0.4, 0.5,
                             [6,7,8,9], 28.0, 0.7, 0.3, 0.4, True, 0.6),
    "IN_GJ": RegionalProfile("IN_GJ", "arid", 0.8, 0.7, 0.5, 0.6,
                             [7,8,9], 27.0, 0.5, 0.5, 0.2, True, 0.7),
    "IN_MH": RegionalProfile("IN_MH", "tropical", 0.8, 0.8, 0.6, 0.7,
                             [6,7,8,9], 26.0, 0.7, 0.3, 0.3, True, 0.8),
    # Middle East
    "AE_DXB": RegionalProfile("AE_DXB", "arid", 0.95, 0.95, 1.5, 0.7,
                              [], 35.0, 0.5, 0.1, 0.0, True, 0.7),
    "SA_RYD": RegionalProfile("SA_RYD", "arid", 0.9, 0.85, 1.2, 0.6,
                              [], 33.0, 0.3, 0.1, 0.0, False, 0.5),
    # East Asia
    "CN_GD": RegionalProfile("CN_GD", "monsoon", 0.95, 0.9, 0.7, 0.8,
                             [5,6,7,8,9], 22.0, 0.8, 0.2, 0.3, True, 0.9),
    "JP_TK": RegionalProfile("JP_TK", "temperate", 0.99, 0.98, 2.5, 0.95,
                             [6,7], 16.0, 0.7, 0.8, 0.2, True, 0.95),
    # North America
    "US_TX": RegionalProfile("US_TX", "arid", 0.9, 0.9, 2.0, 0.6,
                             [], 20.0, 0.6, 0.1, 0.2, True, 0.85),
    "US_MI": RegionalProfile("US_MI", "cold", 0.95, 0.85, 2.2, 0.7,
                             [], 9.0, 0.6, 0.1, 0.1, False, 0.8),
    # Europe
    "DE_NRW": RegionalProfile("DE_NRW", "temperate", 0.99, 0.95, 2.8, 0.95,
                              [], 10.0, 0.7, 0.1, 0.1, False, 0.9),
    "NO_OSL": RegionalProfile("NO_OSL", "cold", 0.99, 0.95, 3.0, 0.9,
                              [], 6.0, 0.7, 0.1, 0.1, True, 0.85),
    # Africa
    "NG_LG": RegionalProfile("NG_LG", "tropical", 0.4, 0.4, 0.3, 0.3,
                             [4,5,6,7,8,9,10], 27.0, 0.8, 0.1, 0.3, True, 0.4),
    # Southeast Asia
    "TH_BK": RegionalProfile("TH_BK", "monsoon", 0.85, 0.75, 0.5, 0.5,
                             [5,6,7,8,9,10], 28.0, 0.8, 0.2, 0.5, True, 0.7),
    # South America
    "BR_SP": RegionalProfile("BR_SP", "tropical", 0.85, 0.7, 0.6, 0.6,
                             [11,12,1,2,3], 20.0, 0.7, 0.2, 0.2, True, 0.75),
}


class RegionalWorldModel:
    """Modifies industry behavior based on regional context.
    
    The same industry behaves DIFFERENTLY depending on where it operates:
    - Agriculture in monsoon regions: seasonal halts, flood risk
    - Manufacturing in Nigeria: power outages, generator dependency
    - Steel in Germany: high labor cost, strict regulation, reliable grid
    - Oil & gas in Gulf: extreme heat stress, imported labor
    """
    
    def __init__(self, region_id: str, rng: random.Random):
        self.region = REGIONS.get(region_id, REGIONS["IN_AP"])
        self.rng = rng
        self.current_month: int = 1
    
    def set_month(self, month: int):
        """Update current month for seasonal effects."""
        self.current_month = month
    
    def is_monsoon_active(self) -> bool:
        """Check if monsoon is currently active."""
        return self.current_month in self.region.monsoon_months
    
    def get_modifiers(self, industry_id: str) -> Dict[str, float]:
        """Get regional modifiers for an industry's behavior."""
        mods = {
            "degradation_multiplier": 1.0,
            "energy_cost_multiplier": 1.0,
            "labor_cost_multiplier": self.region.labor_cost_index,
            "logistics_delay_multiplier": 1.0,
            "power_outage_probability": 0.0,
            "weather_disruption_probability": 0.0,
            "regulatory_inspection_frequency": self.region.regulation_intensity,
            "skilled_labor_factor": self.region.skilled_labor_availability,
        }
        
        # Power stability
        if self.region.power_stability < 0.8:
            outage_prob = (1.0 - self.region.power_stability) * 0.05  # Per event
            mods["power_outage_probability"] = outage_prob
            # Poor power = more UPS/generator cost
            mods["energy_cost_multiplier"] += (1.0 - self.region.power_stability) * 0.3
        
        # Climate effects
        if self.region.avg_temperature_c > 35:
            mods["degradation_multiplier"] += 0.3  # Heat accelerates degradation
        if self.region.humidity_avg > 0.7:
            mods["degradation_multiplier"] += 0.2  # Humidity = corrosion
        
        # Infrastructure
        if self.region.infrastructure_quality < 0.6:
            mods["logistics_delay_multiplier"] = 1.0 + (1.0 - self.region.infrastructure_quality) * 0.5
        
        # Monsoon effects
        if self.is_monsoon_active():
            # Outdoor industries severely affected
            if any(x in industry_id for x in ["farm", "mining", "construction", "road"]):
                mods["weather_disruption_probability"] = 0.3
                mods["logistics_delay_multiplier"] += 0.4
            else:
                # Indoor industries: logistics affected, not production
                mods["logistics_delay_multiplier"] += 0.2
        
        # Earthquake zone
        if self.region.earthquake_risk > 0.5:
            mods["degradation_multiplier"] += 0.1  # Seismic micro-damage
        
        return mods
    
    def generate_regional_event(self) -> Optional[Dict]:
        """Generate a region-specific random event."""
        # Power outage
        if self.rng.random() < (1.0 - self.region.power_stability) * 0.01:
            duration_hours = self.rng.uniform(0.5, 8) if self.region.power_stability < 0.6 else self.rng.uniform(0.1, 2)
            return {"type": "power_outage", "duration_hours": round(duration_hours, 1),
                    "severity": round(1.0 - self.region.power_stability, 2)}
        
        # Flood (monsoon or general)
        if self.is_monsoon_active() and self.rng.random() < self.region.flood_risk * 0.005:
            return {"type": "flood_event", "severity": round(self.rng.uniform(0.3, 0.9), 2),
                    "duration_days": self.rng.randint(1, 7)}
        
        # Heat event (arid regions)
        if self.region.avg_temperature_c > 30 and self.rng.random() < 0.003:
            return {"type": "heat_advisory", "temperature_c": round(self.region.avg_temperature_c + self.rng.uniform(5, 15), 1),
                    "outdoor_work_restricted": True}
        
        # Regulatory surprise
        if self.rng.random() < self.region.regulation_intensity * 0.002:
            return {"type": "regulatory_inspection", "severity": round(self.rng.uniform(0.3, 0.8), 2),
                    "finding_probability": round(self.region.regulation_intensity * 0.4, 2)}
        
        return None
    
    def get_state(self) -> Dict:
        """Get current regional state for SEATR record."""
        return {
            "region": self.region.region_id,
            "climate": self.region.climate_zone,
            "monsoon_active": self.is_monsoon_active(),
            "power_stability": self.region.power_stability,
            "infrastructure_quality": self.region.infrastructure_quality,
            "labor_cost_index": self.region.labor_cost_index,
            "regulation_intensity": self.region.regulation_intensity,
            "current_month": self.current_month,
        }



# ═══════════════════════════════════════════════════════════════════
# PHASE 4: ENTERPRISE LIFECYCLE
# ═══════════════════════════════════════════════════════════════════

@dataclass
class LifecycleState:
    """Current lifecycle stage of a business/plant."""
    stage: str  # "startup", "growth", "expansion", "maturity", "decline", "turnaround"
    age_years: float
    stage_progress: float  # 0.0 (just entered) to 1.0 (about to transition)
    debt_ratio: float  # 0.0 (no debt) to 1.0 (heavily leveraged)
    investment_rate: float  # How much being invested in upgrades (0 to 1.0)
    workforce_quality: float  # 0.5 (poor) to 1.0 (excellent)
    maintenance_discipline: float  # 0.3 (neglected) to 1.0 (world-class)
    automation_level: float  # 0.0 (manual) to 1.0 (fully automated)
    market_share_trend: float  # -1.0 (losing) to +1.0 (gaining)


class EnterpriseLifecycleEngine:
    """Models how a business changes behavior as it ages and evolves.
    
    A startup behaves very differently from a mature plant:
    - Startup: high risk, low discipline, frequent breakdowns, fast adaptation
    - Growth: improving, investing, hiring, quality gaps
    - Maturity: stable, optimized, risk of complacency
    - Decline: cost-cutting, deferred maintenance, experienced staff leaving
    - Turnaround: restructuring, high stress, new management
    
    This lifecycle stage MODIFIES all other engines:
    - Degradation: neglected maintenance → faster wear
    - Fatigue: understaffed decline → more overtime → more errors
    - Economics: high debt → cost pressure → deferred investment
    - Cascades: aging equipment → more single-point failures
    """
    
    STAGE_TRANSITIONS = {
        "startup": {"startup": 0.7, "growth": 0.25, "decline": 0.05},
        "growth": {"growth": 0.7, "expansion": 0.2, "maturity": 0.08, "decline": 0.02},
        "expansion": {"expansion": 0.5, "maturity": 0.4, "growth": 0.05, "decline": 0.05},
        "maturity": {"maturity": 0.8, "decline": 0.12, "expansion": 0.05, "turnaround": 0.03},
        "decline": {"decline": 0.6, "turnaround": 0.2, "maturity": 0.1, "shutdown": 0.1},
        "turnaround": {"turnaround": 0.4, "growth": 0.3, "maturity": 0.2, "decline": 0.1},
    }
    
    def __init__(self, rng: random.Random, initial_stage: str = "maturity",
                 age_years: float = 10.0):
        self.rng = rng
        self.state = LifecycleState(
            stage=initial_stage,
            age_years=age_years,
            stage_progress=rng.uniform(0.2, 0.8),
            debt_ratio=self._initial_debt(initial_stage, rng),
            investment_rate=self._initial_investment(initial_stage, rng),
            workforce_quality=self._initial_workforce(initial_stage, rng),
            maintenance_discipline=self._initial_maintenance(initial_stage, rng),
            automation_level=rng.uniform(0.2, 0.7),
            market_share_trend=self._initial_trend(initial_stage, rng),
        )
    
    def _initial_debt(self, stage: str, rng: random.Random) -> float:
        defaults = {"startup": 0.7, "growth": 0.5, "expansion": 0.6,
                    "maturity": 0.3, "decline": 0.5, "turnaround": 0.8}
        return defaults.get(stage, 0.4) + rng.uniform(-0.1, 0.1)
    
    def _initial_investment(self, stage: str, rng: random.Random) -> float:
        defaults = {"startup": 0.8, "growth": 0.7, "expansion": 0.8,
                    "maturity": 0.4, "decline": 0.15, "turnaround": 0.6}
        return defaults.get(stage, 0.4) + rng.uniform(-0.1, 0.1)
    
    def _initial_workforce(self, stage: str, rng: random.Random) -> float:
        defaults = {"startup": 0.6, "growth": 0.7, "expansion": 0.75,
                    "maturity": 0.85, "decline": 0.65, "turnaround": 0.6}
        return defaults.get(stage, 0.7) + rng.uniform(-0.05, 0.05)
    
    def _initial_maintenance(self, stage: str, rng: random.Random) -> float:
        defaults = {"startup": 0.5, "growth": 0.6, "expansion": 0.65,
                    "maturity": 0.8, "decline": 0.4, "turnaround": 0.55}
        return defaults.get(stage, 0.6) + rng.uniform(-0.05, 0.05)
    
    def _initial_trend(self, stage: str, rng: random.Random) -> float:
        defaults = {"startup": 0.3, "growth": 0.5, "expansion": 0.4,
                    "maturity": 0.0, "decline": -0.4, "turnaround": 0.1}
        return defaults.get(stage, 0.0) + rng.uniform(-0.1, 0.1)
    
    def tick(self):
        """Advance lifecycle by one time step (roughly 1 week of simulation)."""
        self.state.age_years += 1/52  # ~1 week
        self.state.stage_progress += self.rng.uniform(0.001, 0.005)
        
        # Stage transition check
        if self.state.stage_progress > 1.0:
            self._transition_stage()
        
        # Evolve state based on current stage
        self._evolve_state()
    
    def _transition_stage(self):
        """Transition to next lifecycle stage."""
        transitions = self.STAGE_TRANSITIONS.get(self.state.stage, {"maturity": 1.0})
        roll = self.rng.random()
        cumulative = 0.0
        for next_stage, prob in transitions.items():
            cumulative += prob
            if roll < cumulative:
                self.state.stage = next_stage
                self.state.stage_progress = 0.0
                break
    
    def _evolve_state(self):
        """Evolve internal state based on current stage."""
        stage = self.state.stage
        
        if stage == "startup":
            self.state.workforce_quality += self.rng.uniform(0, 0.002)  # Learning
            self.state.maintenance_discipline += self.rng.uniform(-0.001, 0.002)
            self.state.debt_ratio += self.rng.uniform(-0.001, 0.002)  # Burning cash
        elif stage == "growth":
            self.state.workforce_quality += self.rng.uniform(0, 0.001)
            self.state.automation_level += self.rng.uniform(0, 0.001)
            self.state.maintenance_discipline += self.rng.uniform(0, 0.001)
        elif stage == "maturity":
            self.state.workforce_quality += self.rng.uniform(-0.001, 0.001)
            self.state.maintenance_discipline += self.rng.uniform(-0.001, 0.0005)  # Slow decay
        elif stage == "decline":
            self.state.workforce_quality -= self.rng.uniform(0, 0.002)  # Good people leave
            self.state.maintenance_discipline -= self.rng.uniform(0, 0.003)  # Budget cuts
            self.state.investment_rate -= self.rng.uniform(0, 0.002)
            self.state.debt_ratio += self.rng.uniform(0, 0.001)
        elif stage == "turnaround":
            self.state.investment_rate += self.rng.uniform(0, 0.003)  # New investment
            self.state.debt_ratio += self.rng.uniform(0, 0.002)  # Taking on debt to fix
            self.state.workforce_quality += self.rng.uniform(-0.001, 0.002)
        
        # Clamp values
        self.state.workforce_quality = max(0.3, min(1.0, self.state.workforce_quality))
        self.state.maintenance_discipline = max(0.2, min(1.0, self.state.maintenance_discipline))
        self.state.investment_rate = max(0.05, min(1.0, self.state.investment_rate))
        self.state.debt_ratio = max(0.0, min(1.0, self.state.debt_ratio))
        self.state.automation_level = max(0.0, min(1.0, self.state.automation_level))
    
    def get_modifiers(self) -> Dict[str, float]:
        """Get modifiers that affect other engines based on lifecycle state."""
        maint = self.state.maintenance_discipline
        workforce = self.state.workforce_quality
        invest = self.state.investment_rate
        
        return {
            # Degradation: poor maintenance = faster wear
            "degradation_multiplier": 1.0 + (1.0 - maint) * 0.8,
            # Fatigue: understaffed = more overtime
            "overtime_probability": max(0, (1.0 - workforce) * 0.3 + (1.0 - maint) * 0.2),
            # Cascade: aging + neglected = more failures propagate
            "cascade_probability_multiplier": 1.0 + (1.0 - invest) * 0.5,
            # Quality: poor workforce = more defects
            "quality_defect_multiplier": 1.0 + (1.0 - workforce) * 0.6,
            # Cost pressure from debt
            "cost_pressure": self.state.debt_ratio * 0.5,
            # Automation reduces labor sensitivity
            "labor_dependency": 1.0 - self.state.automation_level * 0.5,
            # Safety: neglect + poor workforce = more incidents
            "safety_incident_multiplier": 1.0 + (1.0 - maint) * 0.4 + (1.0 - workforce) * 0.3,
        }
    
    def get_state(self) -> Dict:
        """Get lifecycle state for SEATR record."""
        return {
            "stage": self.state.stage,
            "age_years": round(self.state.age_years, 1),
            "stage_progress": round(self.state.stage_progress, 2),
            "debt_ratio": round(self.state.debt_ratio, 2),
            "investment_rate": round(self.state.investment_rate, 2),
            "workforce_quality": round(self.state.workforce_quality, 2),
            "maintenance_discipline": round(self.state.maintenance_discipline, 2),
            "automation_level": round(self.state.automation_level, 2),
            "market_share_trend": round(self.state.market_share_trend, 2),
        }



# ═══════════════════════════════════════════════════════════════════
# PHASE 5: BLACK SWAN / SHOCK PROPAGATION
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ShockEvent:
    """A rare, high-impact event that propagates across the ecosystem."""
    shock_type: str
    severity: float  # 0.0 to 1.0
    origin_region: Optional[str]
    origin_industry: Optional[str]
    start_tick: int
    duration_ticks: int
    affected_industries: List[str]
    market_impacts: Dict[str, float]
    recovery_rate: float  # How fast things normalize (0.01 = slow, 0.1 = fast)
    active: bool = True


class BlackSwanEngine:
    """Generates and propagates rare shock events across the ecosystem.
    
    Shocks are LOW probability, HIGH impact events that cascade:
    - Pandemic → labor crash → all industries → supply chain → months
    - Earthquake → infrastructure damage → regional halt → weeks
    - Cyberattack → IT/OT systems → production stop → days
    - Port shutdown → import freeze → manufacturing halt → weeks
    - Fuel shortage → transport stop → supply chain → days
    
    Key properties:
    - Shocks have realistic probabilities (not every episode has one)
    - They propagate through the dependency graph
    - They affect market prices
    - They trigger cascading failures
    - Recovery is gradual, not instant
    """
    
    SHOCK_CATALOG = {
        "pandemic": {
            "base_probability_per_tick": 0.00001,  # Very rare
            "severity_range": (0.4, 0.9),
            "duration_range": (100, 500),  # Long
            "market_impacts": {"labor_availability": -0.4, "shipping_cost_index": 0.5,
                              "global_demand_index": -0.3, "port_congestion": 0.4},
            "affected_industries": "all",
            "primary_effect": "labor_shortage",
            "recovery_rate": 0.005,
        },
        "earthquake": {
            "base_probability_per_tick": 0.0001,
            "severity_range": (0.3, 0.8),
            "duration_range": (20, 80),
            "market_impacts": {"shipping_cost_index": 0.2, "steel_price_index": 0.1},
            "affected_industries": "regional",
            "primary_effect": "infrastructure_damage",
            "recovery_rate": 0.02,
        },
        "cyberattack": {
            "base_probability_per_tick": 0.0005,
            "severity_range": (0.2, 0.7),
            "duration_range": (5, 30),
            "market_impacts": {},
            "affected_industries": ["data_center", "software_company", "semiconductor_fab",
                                     "hospital", "thermal_power_plant", "automobile_assembly"],
            "primary_effect": "systems_down",
            "recovery_rate": 0.05,
        },
        "port_shutdown": {
            "base_probability_per_tick": 0.0003,
            "severity_range": (0.4, 0.8),
            "duration_range": (10, 60),
            "market_impacts": {"shipping_cost_index": 0.8, "port_congestion": 0.7},
            "affected_industries": "import_dependent",
            "primary_effect": "supply_chain_halt",
            "recovery_rate": 0.03,
        },
        "fuel_shortage": {
            "base_probability_per_tick": 0.0002,
            "severity_range": (0.3, 0.7),
            "duration_range": (15, 50),
            "market_impacts": {"oil_price_index": 0.6, "energy_price_index": 0.4,
                              "shipping_cost_index": 0.3},
            "affected_industries": "energy_dependent",
            "primary_effect": "energy_crisis",
            "recovery_rate": 0.02,
        },
        "flood": {
            "base_probability_per_tick": 0.0004,
            "severity_range": (0.3, 0.8),
            "duration_range": (10, 40),
            "market_impacts": {"food_price_index": 0.3, "shipping_cost_index": 0.2},
            "affected_industries": "outdoor",
            "primary_effect": "operational_halt",
            "recovery_rate": 0.03,
        },
        "trade_war": {
            "base_probability_per_tick": 0.00005,
            "severity_range": (0.3, 0.6),
            "duration_range": (100, 300),
            "market_impacts": {"shipping_cost_index": 0.3, "steel_price_index": 0.2,
                              "global_demand_index": -0.1},
            "affected_industries": "export_dependent",
            "primary_effect": "market_disruption",
            "recovery_rate": 0.003,
        },
        "grid_collapse": {
            "base_probability_per_tick": 0.0002,
            "severity_range": (0.5, 0.9),
            "duration_range": (3, 15),
            "market_impacts": {"energy_price_index": 0.3},
            "affected_industries": "electricity_dependent",
            "primary_effect": "power_loss",
            "recovery_rate": 0.1,
        },
        "regulatory_ban": {
            "base_probability_per_tick": 0.0001,
            "severity_range": (0.3, 0.7),
            "duration_range": (50, 200),
            "market_impacts": {},
            "affected_industries": "regulated",
            "primary_effect": "compliance_halt",
            "recovery_rate": 0.008,
        },
    }
    
    # Which industries are affected by which shock categories
    INDUSTRY_VULNERABILITY = {
        "import_dependent": ["automobile_assembly", "electronics_pcb", "pharmaceutical_tablet",
                            "semiconductor_fab"],
        "energy_dependent": ["steel_rolling", "cement_manufacturing", "aluminium_smelting",
                            "automobile_assembly", "data_center"],
        "outdoor": ["rice_farming", "wheat_farming", "sugarcane_farming", "road_construction",
                   "coal_mining", "iron_ore_mining", "timber_logging"],
        "electricity_dependent": ["semiconductor_fab", "data_center", "hospital",
                                  "steel_rolling", "automobile_assembly"],
        "export_dependent": ["automobile_assembly", "electronics_pcb", "cotton_spinning",
                            "pharmaceutical_tablet", "software_company"],
        "regulated": ["pharmaceutical_tablet", "hospital", "oil_refining",
                     "thermal_power_plant", "vaccine_manufacturing"],
    }
    
    def __init__(self, rng: random.Random, dependency_graph: IndustryDependencyGraph):
        self.rng = rng
        self.graph = dependency_graph
        self.active_shocks: List[ShockEvent] = []
        self.shock_history: List[ShockEvent] = []
        self.tick_count: int = 0
    
    def tick(self, market: MarketDynamicsEngine = None) -> List[ShockEvent]:
        """Check for new shocks and evolve existing ones."""
        self.tick_count += 1
        new_shocks = []
        
        # Check for new shock occurrence
        for shock_type, config in self.SHOCK_CATALOG.items():
            if self.rng.random() < config["base_probability_per_tick"]:
                shock = self._create_shock(shock_type, config)
                self.active_shocks.append(shock)
                new_shocks.append(shock)
                
                # Apply market impact immediately
                if market and shock.market_impacts:
                    for attr, delta in shock.market_impacts.items():
                        current = getattr(market.state, attr, 0)
                        setattr(market.state, attr, current + delta * shock.severity)
        
        # Evolve active shocks (recovery)
        for shock in self.active_shocks:
            if self.tick_count > shock.start_tick + shock.duration_ticks:
                shock.active = False
            elif market and shock.market_impacts:
                # Gradual recovery
                for attr, delta in shock.market_impacts.items():
                    current = getattr(market.state, attr, 0)
                    target = 1.0 if "index" in attr else 0.0
                    recovery = (target - current) * shock.recovery_rate
                    setattr(market.state, attr, current + recovery)
        
        # Clean up resolved shocks
        resolved = [s for s in self.active_shocks if not s.active]
        self.shock_history.extend(resolved)
        self.active_shocks = [s for s in self.active_shocks if s.active]
        
        return new_shocks
    
    def _create_shock(self, shock_type: str, config: Dict) -> ShockEvent:
        """Create a new shock event."""
        sev_lo, sev_hi = config["severity_range"]
        dur_lo, dur_hi = config["duration_range"]
        
        severity = self.rng.uniform(sev_lo, sev_hi)
        duration = self.rng.randint(dur_lo, dur_hi)
        
        # Determine affected industries
        affected_key = config["affected_industries"]
        if affected_key == "all":
            affected = list(self.graph.downstream_map.keys()) + list(self.graph.upstream_map.keys())
            affected = list(set(affected))
        elif affected_key == "regional":
            affected = list(self.INDUSTRY_VULNERABILITY.get("outdoor", []))
        elif isinstance(affected_key, list):
            affected = affected_key
        else:
            affected = self.INDUSTRY_VULNERABILITY.get(affected_key, [])
        
        return ShockEvent(
            shock_type=shock_type,
            severity=round(severity, 3),
            origin_region=None,
            origin_industry=None,
            start_tick=self.tick_count,
            duration_ticks=duration,
            affected_industries=affected,
            market_impacts=config.get("market_impacts", {}),
            recovery_rate=config["recovery_rate"],
        )
    
    def force_shock(self, shock_type: str, severity: float = None,
                    market: MarketDynamicsEngine = None) -> ShockEvent:
        """Force a specific shock (for testing or scenario generation)."""
        config = self.SHOCK_CATALOG[shock_type]
        shock = self._create_shock(shock_type, config)
        if severity is not None:
            shock.severity = severity
        
        self.active_shocks.append(shock)
        
        if market and shock.market_impacts:
            for attr, delta in shock.market_impacts.items():
                current = getattr(market.state, attr, 0)
                setattr(market.state, attr, current + delta * shock.severity)
        
        return shock
    
    def get_impact_on_industry(self, industry_id: str) -> Dict:
        """Get the combined impact of all active shocks on one industry."""
        if not self.active_shocks:
            return {"total_impact": 0.0, "active_shocks": 0}
        
        total_impact = 0.0
        affecting_shocks = []
        
        for shock in self.active_shocks:
            if industry_id in shock.affected_industries:
                impact = shock.severity * (1.0 - (self.tick_count - shock.start_tick) / max(1, shock.duration_ticks) * 0.5)
                total_impact += max(0, impact)
                affecting_shocks.append(shock.shock_type)
        
        # Also check indirect impact through dependency graph
        for shock in self.active_shocks:
            for affected in shock.affected_industries:
                links = self.graph.get_downstream_dependents(affected)
                for link in links:
                    if link.target_industry == industry_id:
                        indirect = shock.severity * link.strength * 0.3
                        total_impact += indirect
        
        return {
            "total_impact": round(min(1.0, total_impact), 3),
            "active_shocks": len(affecting_shocks),
            "shock_types": affecting_shocks,
            "production_modifier": round(max(0.1, 1.0 - total_impact * 0.5), 3),
        }
    
    def get_state(self) -> Dict:
        """Get shock engine state for SEATR record."""
        return {
            "active_shocks": [
                {"type": s.shock_type, "severity": s.severity,
                 "ticks_remaining": s.start_tick + s.duration_ticks - self.tick_count}
                for s in self.active_shocks
            ],
            "shock_count_active": len(self.active_shocks),
            "shock_count_historical": len(self.shock_history),
            "ecosystem_stress": round(sum(s.severity for s in self.active_shocks), 3),
        }
