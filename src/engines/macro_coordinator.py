from typing import Any
from core.random.deterministic_rng import DeterministicRNG
from core.world_state import WorldState

# Import macro engines
from .macro_engines import (
    ResourceScarcityEngine,
    TechnologyDiffusionEngine,
    SupplyChainEngine,
    InfrastructureEngine,
    InnovationResistanceEngine,
    IndustryEngine,
    CompanyEngine,
    FactoryEngine
)

def init_macro_state(world_state: WorldState) -> None:
    """
    Initializes macro-world structures within world_state.hidden_state.
    Provides starting conditions for scarcity, technology, industries, companies, and factories.
    """
    hidden = world_state.hidden_state
    
    hidden["macro_tick"] = 0
    
    # Scarcity factors
    hidden["scarcity_factors"] = {
        "metals": 0.15,
        "lubricants": 0.08,
        "energy": 0.12
    }
    
    # Tech diffusion
    hidden["technology_diffusion"] = {
        "global_tech_level": 0.05,
        "global_adoption_rate": 0.01
    }
    
    # Supply Chain
    hidden["supply_chain_state"] = {
        "supply_chain_stress": 0.15,
        "components_delay": 0.05
    }
    
    # Infrastructure condition
    hidden["infrastructure_state"] = {
        "infrastructure_integrity": 0.95,
        "bottleneck_index": 0.05
    }
    
    # Innovation Resistance
    hidden["innovation_resistance_state"] = {
        "global_resistance": 0.20
    }
    
    # Industries
    hidden["industries"] = {
        "heavy_manufacturing": {
            "demand_index": 1.0,
            "input_cost_index": 1.0,
            "regulatory_pressure": 0.1
        },
        "precision_engineering": {
            "demand_index": 1.0,
            "input_cost_index": 1.0,
            "regulatory_pressure": 0.05
        }
    }
    
    # Companies
    hidden["companies"] = {
        "apex_corp": {
            "industry_id": "heavy_manufacturing",
            "cash_reserves": 500000.0,
            "company_debt": 0.0,
            "market_share": 0.6,
            "maintenance_culture": 0.5,
            "allocated_maintenance_budget": 5000.0
        },
        "vertex_optics": {
            "industry_id": "precision_engineering",
            "cash_reserves": 300000.0,
            "company_debt": 0.0,
            "market_share": 0.4,
            "maintenance_culture": 0.6,
            "allocated_maintenance_budget": 3500.0
        }
    }
    
    # Factories
    hidden["factories"] = {
        "factory_0": {
            "company_id": "apex_corp",
            "capacity": 1000.0,
            "production_rate": 800.0,
            "efficiency": 0.95,
            "tech_level": 0.05,
            "machines": [
                {
                    "machine_id": "machine_0",  # Synchronized with micro-tick primary machine
                    "bearing_wear": 0.0,
                    "microfracture_density": 0.05,
                    "lubricant_contamination": 0.02
                },
                {
                    "machine_id": "machine_1",  # Additional machine
                    "bearing_wear": 0.02,
                    "microfracture_density": 0.05,
                    "lubricant_contamination": 0.03
                }
            ]
        },
        "factory_1": {
            "company_id": "vertex_optics",
            "capacity": 800.0,
            "production_rate": 600.0,
            "efficiency": 0.93,
            "tech_level": 0.08,
            "machines": [
                {
                    "machine_id": "machine_0",
                    "bearing_wear": 0.01,
                    "microfracture_density": 0.04,
                    "lubricant_contamination": 0.02
                },
                {
                    "machine_id": "machine_1",
                    "bearing_wear": 0.03,
                    "microfracture_density": 0.06,
                    "lubricant_contamination": 0.04
                }
            ]
        }
    }


class MacroCoordinator:
    """
    Coordinates and sequences the execution of the macro-world engines.
    Limits execution frequency to configurable micro-tick intervals.
    """
    def __init__(self, interval: int = 100):
        self.interval = interval
        self.scarcity_engine = ResourceScarcityEngine()
        self.tech_diffusion_engine = TechnologyDiffusionEngine()
        self.supply_chain_engine = SupplyChainEngine()
        self.infrastructure_engine = InfrastructureEngine()
        self.innovation_resistance_engine = InnovationResistanceEngine()
        self.industry_engine = IndustryEngine()
        self.company_engine = CompanyEngine()
        self.factory_engine = FactoryEngine()

    def tick(self, world_state: WorldState, rng: DeterministicRNG) -> None:
        hidden = world_state.hidden_state
        
        # 1. Initialize macro states dynamically if not present
        if "macro_tick" not in hidden:
            init_macro_state(world_state)
            
        # 2. Check if the current micro-tick matches the macro interval boundary
        if world_state.world_tick % self.interval != 0:
            return

        hidden["macro_tick"] = hidden.get("macro_tick", 0) + 1

        # 3. Sequenced execution of macro engines
        self.scarcity_engine.process(world_state, rng)
        self.tech_diffusion_engine.process(world_state, rng)
        self.supply_chain_engine.process(world_state, rng)
        self.infrastructure_engine.process(world_state, rng)
        self.innovation_resistance_engine.process(world_state, rng)
        self.industry_engine.process(world_state, rng)
        self.company_engine.process(world_state, rng)
        self.factory_engine.process(world_state, rng)

