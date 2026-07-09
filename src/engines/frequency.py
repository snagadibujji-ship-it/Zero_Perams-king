"""
Realistic Frequency Engine
===========================
In real life, most of what happens in a factory is BORING routine.
Fires don't happen every day. People don't get hired every day.
This module makes event probabilities match reality.

Real-world frequency distribution (per 1000 working days):
- Daily operations (shift start/end, production, checks): 850-900/1000
- Casual human chat (tea break, greetings): 700/1000
- Minor maintenance (lubrication, filter): 150/1000
- Learning/training moments: 30/1000
- Supply chain events: 50/1000
- Quality issues (minor): 40/1000
- Business updates: 20/1000
- HR events (leave, attendance): 15/1000
- Near misses: 5/1000
- Equipment breakdown: 3/1000
- Customer complaint: 2/1000
- New hire: 1/1000 (once per 3 months roughly)
- Promotion: 0.5/1000
- Fire/explosion: 0.01/1000 (once per 100,000 days = once per 274 years)
- Fatality: 0.001/1000
- Acquisition/merger: 0.001/1000

This means in 1000 lines of output:
~400 = daily operations (machine running, production, routine)
~200 = human interaction (chat, greetings, breaks)
~150 = routine maintenance & checks
~80 = supply chain & logistics (deliveries, orders)
~50 = quality & standards (inspections, calibration)
~40 = learning moments (on-job training, tips shared)
~30 = minor issues (small mistake caught, rework)
~20 = business/financial updates
~15 = workforce admin (leave, attendance)
~10 = technology & system updates
~5 = safety observations (not accidents!)
~2 = near miss / minor incident
~1 = breakdown / serious issue
~0.1 = fire / crisis / major event
"""

# Frequency per 10,000 events (realistic probability)
# Higher = more common. Must sum to ~10,000.
EVENT_FREQUENCY = {
    # === VERY COMMON (happen multiple times per day) ===
    "daily_ops": 3500,           # 35% of all events
    "human_relations": 2000,      # 20% — people talk A LOT
    "routine_monitoring": 1500,   # 15% — sensors, gauges, readings

    # === COMMON (happen daily or almost daily) ===
    "maintenance_routine": 800,   # 8% — lubrication, cleaning, minor
    "supply_logistics": 600,      # 6% — deliveries arrive, orders placed
    "quality_routine": 400,       # 4% — inspections, sampling

    # === WEEKLY/REGULAR ===
    "learning_training": 300,     # 3% — tips, mentoring, observation
    "business_update": 200,       # 2% — targets, production numbers
    "workforce_admin": 150,       # 1.5% — leaves, attendance, shifts
    "technology_routine": 100,    # 1% — software updates, calibration

    # === MONTHLY / OCCASIONAL ===
    "customer_interaction": 80,   # 0.8%
    "leadership_communication": 60,  # 0.6%
    "holidays_culture": 50,       # 0.5%
    "environment_routine": 40,    # 0.4%
    "competition_market": 30,     # 0.3%
    "regulation_compliance": 25,  # 0.25%

    # === RARE (few times per year) ===
    "mistakes_minor": 20,         # 0.2% — caught early, fixed
    "innovation_idea": 15,        # 0.15%
    "expansion_growth": 10,       # 0.1%
    "salary_finance": 8,          # 0.08% (monthly pay, occasional bonus)
    "workforce_change": 5,        # 0.05% (hire/fire/promote — very rare per person)

    # === VERY RARE (once per year or less) ===
    "safety_incident": 3,         # 0.03%
    "breakdown_major": 2,         # 0.02%
    "crisis_event": 0.5,          # 0.005% — fire, flood, pandemic
    "merger_acquisition": 0.3,    # 0.003%
    "evolution_milestone": 0.2,   # 0.002% — generation change, tech revolution
}


# Map old categories to new frequency-based categories
# This allows backward compatibility while fixing realism
CATEGORY_MAPPING = {
    "daily_ops": "daily_ops",
    "routine_monitoring": "daily_ops",  # sensor readings, gauge checks
    "human_relations": "human_relations",
    "maintenance_routine": "maintenance",
    "maintenance": "maintenance",
    "supply_logistics": "supply_chain",
    "supply_chain": "supply_chain",
    "logistics": "supply_chain",
    "quality_routine": "quality",
    "quality": "quality",
    "learning_training": "learning_training",
    "business_update": "business",
    "business": "business",
    "workforce_admin": "workforce",
    "workforce": "workforce",
    "workforce_change": "workforce",
    "technology_routine": "technology_change",
    "technology_change": "technology_change",
    "customer_interaction": "customer_sales",
    "customer_sales": "customer_sales",
    "leadership_communication": "leadership",
    "leadership": "leadership",
    "holidays_culture": "holidays_breaks",
    "holidays_breaks": "holidays_breaks",
    "culture": "holidays_breaks",
    "environment_routine": "environment",
    "environment": "environment",
    "competition_market": "competition",
    "competition": "competition",
    "regulation_compliance": "regulation",
    "regulation": "regulation",
    "mistakes_minor": "mistakes_failures",
    "mistakes_failures": "mistakes_failures",
    "innovation_idea": "innovation",
    "innovation": "innovation",
    "expansion_growth": "expansion",
    "expansion": "expansion",
    "salary_finance": "salary_finance",
    "safety_incident": "safety_accidents",
    "safety_accidents": "safety_accidents",
    "breakdown_major": "maintenance",
    "crisis_event": "crisis",
    "crisis": "crisis",
    "merger_acquisition": "mergers_acquisitions",
    "mergers_acquisitions": "mergers_acquisitions",
    "evolution_milestone": "evolution",
    "evolution": "evolution",
}


def pick_event_category(rng, industry_id: str = None) -> str:
    """Pick an event category based on realistic frequency.
    
    Uses the v2 category list (40 categories) with proper mapping.
    NOW: Accepts industry_id to apply industry-specific weight overrides.
    """
    # Start with base frequencies
    weights_dict = dict(EVENT_FREQUENCY)
    
    # Apply industry-specific overrides
    if industry_id:
        overrides = INDUSTRY_EVENT_WEIGHTS.get(industry_id)
        if overrides:
            for cat, multiplier in overrides.items():
                if cat in weights_dict:
                    weights_dict[cat] = weights_dict[cat] * multiplier
    
    categories = list(weights_dict.keys())
    weights = list(weights_dict.values())
    
    # Pick from frequency-weighted distribution
    chosen = rng.choices(categories, weights=weights, k=1)[0]
    
    # Map to actual v2 category — some frequency keys expand to multiple categories
    expansion_map = {
        "daily_ops": ["daily_ops", "daily_ops", "daily_ops", "routine_monitoring", 
                      "documentation", "equipment_sounds", "shift_handover"],
        "human_relations": ["human_relations", "human_relations", "canteen_food", 
                           "personal_life", "gossip_rumors", "commute_arrival"],
        "routine_monitoring": ["routine_monitoring", "weather_environment", "routine_monitoring"],
        "maintenance_routine": ["maintenance", "maintenance"],
        "supply_logistics": ["supply_chain", "transport_fleet", "supply_chain"],
        "quality_routine": ["quality", "quality"],
        "learning_training": ["learning_training", "learning_training"],
        "business_update": ["business", "business"],
        "workforce_admin": ["workforce", "workforce"],
        "technology_routine": ["technology_change", "technology_change"],
        "customer_interaction": ["customer_sales", "visitor_external"],
        "leadership_communication": ["leadership", "leadership"],
        "holidays_culture": ["holidays_breaks", "health_wellness"],
        "environment_routine": ["environment", "waste_byproduct"],
        "competition_market": ["competition", "competition"],
        "regulation_compliance": ["regulation", "regulation"],
        "mistakes_minor": ["mistakes_failures", "mistakes_failures"],
        "innovation_idea": ["innovation", "innovation"],
        "expansion_growth": ["expansion", "expansion"],
        "salary_finance": ["salary_finance", "salary_finance"],
        "workforce_change": ["workforce", "union_labor"],
        "safety_incident": ["safety_accidents", "safety_accidents"],
        "breakdown_major": ["maintenance", "maintenance"],
        "crisis_event": ["crisis", "crisis"],
        "merger_acquisition": ["mergers_acquisitions", "mergers_acquisitions"],
        "evolution_milestone": ["evolution", "evolution"],
    }
    
    # Expand to actual category
    if chosen in expansion_map:
        actual = rng.choice(expansion_map[chosen])
    else:
        actual = CATEGORY_MAPPING.get(chosen, "daily_ops")
    
    # Also randomly inject night_shift_special and animal_pest (very low chance)
    if rng.random() < 0.005:
        actual = "night_shift_special"
    elif rng.random() < 0.003:
        actual = "animal_pest"
    elif rng.random() < 0.002:
        actual = "vendor_interaction"
    
    return actual


# Subtype rarity within each category
# Some subtypes within a category are more common than others
SUBTYPE_RARITY = {
    # In daily_ops, shift_start happens every day but tool_changeover is less common
    "shift_start": 100,
    "shift_end": 100,
    "production_run": 150,
    "quality_check": 80,
    "machine_startup": 60,
    "machine_shutdown": 60,
    "material_loading": 50,
    "output_packing": 50,
    "cleaning": 40,
    "routine_inspection": 30,
    "handover_briefing": 30,
    "target_review": 20,
    "tool_changeover": 15,
    "batch_mixing": 15,
    "calibration": 10,
    "inventory_count": 5,  # Not daily
    
    # In human_relations
    "morning_greeting": 200,
    "tea_break_chat": 150,
    "lunch_together": 100,
    "helping_colleague": 80,
    "joke_shared": 60,
    "phone_call_family": 40,
    "sports_discussion": 30,
    "weekend_story": 20,
    "food_sharing": 15,
    "birthday_celebration": 2,  # Once a month maybe
    "farewell_party": 0.5,     # Very rare
    "argument": 5,              # Uncommon
    "reconciliation": 3,
    "condolence": 0.5,
    
    # In safety
    "safety_observation": 50,   # Common (proactive reporting)
    "toolbox_talk": 30,
    "ppe_violation": 20,
    "near_miss": 10,
    "hazard_report": 8,
    "minor_injury": 3,
    "first_aid_given": 2,
    "emergency_drill": 1,       # Quarterly
    "serious_injury": 0.1,      # Very rare
    "fatality": 0.001,          # Almost never
    "fire_incident": 0.05,
    
    # In crisis
    "power_grid_failure": 1,
    "water_shortage": 0.5,
    "labor_strike": 0.3,
    "economic_recession": 0.1,
    "fire_outbreak": 0.05,
    "flood_damage": 0.02,
    "explosion": 0.01,
    "pandemic_lockdown": 0.005,
    "earthquake": 0.003,
    "factory_collapse": 0.001,
    
    # In workforce
    "attendance_issue": 20,
    "leave_request": 15,
    "overtime_request": 10,
    "shift_swap": 8,
    "performance_review": 2,    # Quarterly
    "new_hire_joining": 1,      # Monthly
    "promotion": 0.5,           # Yearly per person
    "resignation": 0.5,
    "transfer": 0.3,
    "retirement": 0.1,
    "termination": 0.05,
}


def pick_subtype_weighted(rng, subtypes: list) -> str:
    """Pick a subtype with realistic rarity weighting.
    
    If a subtype has a defined rarity, use it.
    Otherwise, assign a default middle weight.
    """
    weights = []
    for st in subtypes:
        weights.append(SUBTYPE_RARITY.get(st, 10.0))  # Default = medium rarity
    
    return rng.choices(subtypes, weights=weights, k=1)[0]



# ═══════════════════════════════════════════════════════════════════
# INDUSTRY-SPECIFIC EVENT WEIGHT MULTIPLIERS
# A multiplier of 2.0 = twice as likely; 0.3 = 70% less likely
# These make each industry generate DIFFERENT event distributions
# ═══════════════════════════════════════════════════════════════════

INDUSTRY_EVENT_WEIGHTS = {
    # Agriculture: more weather, supply, less technology
    "rice_farming": {
        "environment_routine": 4.0, "supply_logistics": 2.0, "technology_routine": 0.3,
        "customer_interaction": 0.5, "regulation_compliance": 0.5,
        "breakdown_major": 1.5, "holidays_culture": 1.5,
    },
    "wheat_farming": {
        "environment_routine": 4.0, "supply_logistics": 2.0, "technology_routine": 0.3,
        "customer_interaction": 0.5, "breakdown_major": 1.5,
    },
    "sugarcane_farming": {
        "environment_routine": 3.5, "supply_logistics": 2.0, "technology_routine": 0.3,
        "breakdown_major": 1.5, "safety_incident": 2.0,  # Machete/fire risk
    },
    # Oil & Gas: more maintenance, safety, regulation, less human/food
    "oil_refining": {
        "maintenance_routine": 2.5, "safety_incident": 3.0, "regulation_compliance": 3.0,
        "environment_routine": 2.0, "breakdown_major": 2.0, "crisis_event": 2.0,
        "human_relations": 0.6, "holidays_culture": 0.3, "canteen_food": 0.4,
    },
    "offshore_oil_drilling": {
        "maintenance_routine": 2.5, "safety_incident": 4.0, "regulation_compliance": 3.0,
        "environment_routine": 3.0, "breakdown_major": 2.5, "crisis_event": 3.0,
        "human_relations": 0.5, "holidays_culture": 0.2,
    },
    # Automotive: more supply chain, quality, less environment
    "automobile_assembly": {
        "supply_logistics": 3.0, "quality_routine": 3.0, "technology_routine": 2.0,
        "breakdown_major": 1.5, "customer_interaction": 1.5,
        "environment_routine": 0.3, "holidays_culture": 0.5,
    },
    # Healthcare: more workforce, safety, less maintenance
    "hospital": {
        "workforce_admin": 3.0, "safety_incident": 2.5, "customer_interaction": 2.5,
        "regulation_compliance": 2.5, "learning_training": 2.0,
        "maintenance_routine": 0.5, "supply_logistics": 1.5,
        "environment_routine": 0.3, "breakdown_major": 0.5,
    },
    # Steel: more maintenance, energy/environment, less customer
    "steel_rolling": {
        "maintenance_routine": 3.0, "breakdown_major": 2.5, "environment_routine": 2.0,
        "safety_incident": 2.0, "supply_logistics": 1.5,
        "customer_interaction": 0.3, "human_relations": 0.7,
    },
    # Cement: similar to steel
    "cement_manufacturing": {
        "maintenance_routine": 2.5, "breakdown_major": 2.0, "environment_routine": 2.5,
        "supply_logistics": 1.5, "safety_incident": 1.5,
        "customer_interaction": 0.4, "technology_routine": 0.5,
    },
    # Electronics: more quality, technology, less environment/safety
    "electronics_pcb": {
        "quality_routine": 4.0, "technology_routine": 3.0, "supply_logistics": 2.0,
        "environment_routine": 0.3, "safety_incident": 0.3,
        "maintenance_routine": 0.7,
    },
    # Software: more technology, less maintenance/safety/environment
    "software_company": {
        "technology_routine": 5.0, "customer_interaction": 2.0, "learning_training": 2.0,
        "workforce_admin": 1.5, "business_update": 2.0,
        "maintenance_routine": 0.2, "safety_incident": 0.1, "environment_routine": 0.1,
        "supply_logistics": 0.2, "breakdown_major": 0.3,
    },
    # Construction: more safety, environment, less technology
    "road_construction": {
        "safety_incident": 3.0, "environment_routine": 3.0, "supply_logistics": 2.0,
        "workforce_admin": 2.0, "breakdown_major": 1.5,
        "technology_routine": 0.3, "customer_interaction": 0.3,
        "quality_routine": 1.5,
    },
    # Retail: more customer, less maintenance/safety
    "supermarket_retail": {
        "customer_interaction": 4.0, "supply_logistics": 2.5, "workforce_admin": 2.0,
        "holidays_culture": 2.0, "competition_market": 2.0,
        "maintenance_routine": 0.3, "safety_incident": 0.3, "environment_routine": 0.3,
    },
    # Restaurant: more human, food, customer
    "restaurant_kitchen": {
        "human_relations": 2.0, "customer_interaction": 3.0, "safety_incident": 1.5,
        "supply_logistics": 2.0, "workforce_admin": 2.0,
        "technology_routine": 0.3, "environment_routine": 0.3,
        "maintenance_routine": 0.5,
    },
    # Data center: more technology, less human/environment
    "data_center": {
        "technology_routine": 5.0, "maintenance_routine": 2.0, "breakdown_major": 2.0,
        "regulation_compliance": 2.0, "crisis_event": 1.5,
        "human_relations": 0.4, "environment_routine": 0.3,
        "customer_interaction": 0.5, "safety_incident": 0.5,
    },
    # Mining: more safety, environment, breakdown
    "coal_mining": {
        "safety_incident": 4.0, "environment_routine": 3.0, "breakdown_major": 3.0,
        "maintenance_routine": 2.0, "supply_logistics": 1.5,
        "technology_routine": 0.5, "customer_interaction": 0.3,
    },
    "iron_ore_mining": {
        "safety_incident": 3.5, "environment_routine": 3.0, "breakdown_major": 2.5,
        "maintenance_routine": 2.0, "supply_logistics": 1.5,
        "technology_routine": 0.5, "customer_interaction": 0.3,
    },
}



# ─── ADDITIONAL EVENT WEIGHT PROFILES (expanding to 40+) ────────

# Livestock
for _lid in ["poultry_farming", "dairy_farming", "shrimp_farming"]:
    INDUSTRY_EVENT_WEIGHTS[_lid] = {
        "environment_routine": 3.0, "supply_logistics": 1.5, "safety_incident": 1.5,
        "breakdown_major": 1.5, "technology_routine": 0.4, "customer_interaction": 0.5,
    }

# Food processing
for _fid in ["rice_milling", "sugar_milling"]:
    INDUSTRY_EVENT_WEIGHTS[_fid] = {
        "quality_routine": 3.0, "maintenance_routine": 2.0, "supply_logistics": 2.0,
        "safety_incident": 1.5, "environment_routine": 1.5, "technology_routine": 0.5,
    }

# Power generation
INDUSTRY_EVENT_WEIGHTS["thermal_power_plant"] = {
    "maintenance_routine": 3.0, "breakdown_major": 2.5, "environment_routine": 2.0,
    "safety_incident": 2.0, "regulation_compliance": 2.5,
    "customer_interaction": 0.2, "human_relations": 0.6, "technology_routine": 1.5,
}
INDUSTRY_EVENT_WEIGHTS["solar_farm"] = {
    "environment_routine": 3.0, "maintenance_routine": 1.5, "technology_routine": 2.5,
    "safety_incident": 0.5, "customer_interaction": 0.3, "human_relations": 0.5,
}

# Pharma
INDUSTRY_EVENT_WEIGHTS["pharmaceutical_tablet"] = {
    "quality_routine": 4.0, "regulation_compliance": 3.5, "maintenance_routine": 1.5,
    "supply_logistics": 1.5, "learning_training": 2.0,
    "environment_routine": 0.2, "safety_incident": 0.5, "breakdown_major": 0.5,
}
INDUSTRY_EVENT_WEIGHTS["vaccine_manufacturing"] = INDUSTRY_EVENT_WEIGHTS["pharmaceutical_tablet"].copy()

# Textiles
INDUSTRY_EVENT_WEIGHTS["cotton_spinning"] = {
    "maintenance_routine": 2.0, "quality_routine": 2.0, "workforce_admin": 1.5,
    "environment_routine": 1.5, "supply_logistics": 1.5,
    "safety_incident": 1.0, "technology_routine": 0.5,
}
INDUSTRY_EVENT_WEIGHTS["leather_tanning"] = {
    "environment_routine": 2.5, "safety_incident": 2.0, "quality_routine": 2.0,
    "regulation_compliance": 2.0, "maintenance_routine": 1.5,
    "technology_routine": 0.5, "customer_interaction": 0.5,
}

# Aerospace
INDUSTRY_EVENT_WEIGHTS["aerospace_assembly"] = {
    "quality_routine": 5.0, "regulation_compliance": 3.0, "maintenance_routine": 2.0,
    "supply_logistics": 2.0, "learning_training": 2.0, "technology_routine": 2.0,
    "safety_incident": 1.0, "environment_routine": 0.2, "breakdown_major": 0.5,
}

# Semiconductor
INDUSTRY_EVENT_WEIGHTS["semiconductor_fab"] = {
    "quality_routine": 5.0, "technology_routine": 4.0, "maintenance_routine": 2.5,
    "supply_logistics": 2.0, "regulation_compliance": 1.5,
    "environment_routine": 0.2, "safety_incident": 0.3, "human_relations": 0.5,
}

# Timber
INDUSTRY_EVENT_WEIGHTS["timber_logging"] = {
    "safety_incident": 3.0, "environment_routine": 3.0, "breakdown_major": 2.0,
    "maintenance_routine": 1.5, "supply_logistics": 1.5,
    "technology_routine": 0.3, "customer_interaction": 0.3,
}

# Hospital (already done above but adding AI lab and others)
INDUSTRY_EVENT_WEIGHTS["ai_research_lab"] = {
    "technology_routine": 6.0, "learning_training": 3.0, "business_update": 2.0,
    "workforce_admin": 1.5, "customer_interaction": 1.5,
    "maintenance_routine": 0.3, "safety_incident": 0.1, "environment_routine": 0.1,
}

# Additional coverage for completeness
INDUSTRY_EVENT_WEIGHTS["logistics_warehouse"] = {
    "supply_logistics": 3.0, "workforce_admin": 2.0, "safety_incident": 1.5,
    "customer_interaction": 2.0, "technology_routine": 1.5,
    "environment_routine": 0.3, "regulation_compliance": 0.5,
}



# ═══════════════════════════════════════════════════════════════════
# FAMILY-BASED EVENT WEIGHTS — Cover ALL 500 industries by subsector
# Applied via loop at bottom. Direct entries above take precedence.
# ═══════════════════════════════════════════════════════════════════

_WEIGHT_FAMILIES = {
    # Heavy process industries: high maintenance, safety, environment
    "heavy_process": {
        "maintenance_routine": 2.5, "breakdown_major": 2.0, "environment_routine": 2.0,
        "safety_incident": 2.0, "regulation_compliance": 1.5, "supply_logistics": 1.5,
        "customer_interaction": 0.3, "holidays_culture": 0.5, "technology_routine": 0.8,
    },
    # Light manufacturing: quality focus, moderate maintenance
    "light_manufacturing": {
        "quality_routine": 2.5, "maintenance_routine": 1.8, "supply_logistics": 1.5,
        "workforce_admin": 1.3, "technology_routine": 1.0,
        "environment_routine": 0.5, "crisis_event": 0.5, "customer_interaction": 0.8,
    },
    # Food & beverage: hygiene/quality critical, supply chain important
    "food_bev": {
        "quality_routine": 3.0, "supply_logistics": 2.0, "regulation_compliance": 2.0,
        "safety_incident": 1.5, "workforce_admin": 1.5, "customer_interaction": 1.5,
        "environment_routine": 1.0, "technology_routine": 0.5, "breakdown_major": 0.8,
    },
    # Agriculture & farming: weather dominant, seasonal, low tech
    "agriculture": {
        "environment_routine": 4.0, "supply_logistics": 2.0, "breakdown_major": 1.5,
        "holidays_culture": 1.5, "workforce_admin": 1.5,
        "technology_routine": 0.3, "customer_interaction": 0.5, "regulation_compliance": 0.5,
    },
    # Construction & civil: safety critical, weather dependent, supply chain
    "construction": {
        "safety_incident": 3.5, "environment_routine": 2.5, "supply_logistics": 2.0,
        "workforce_admin": 2.0, "breakdown_major": 1.5, "quality_routine": 1.5,
        "technology_routine": 0.3, "customer_interaction": 0.4, "regulation_compliance": 1.5,
    },
    # Mining & extraction: safety dominant, heavy maintenance, environment
    "mining": {
        "safety_incident": 4.0, "environment_routine": 3.0, "breakdown_major": 2.5,
        "maintenance_routine": 2.0, "regulation_compliance": 2.0, "supply_logistics": 1.5,
        "technology_routine": 0.5, "customer_interaction": 0.3, "human_relations": 0.7,
    },
    # Oil & gas & petrochemical: safety, regulation, maintenance heavy
    "oil_gas": {
        "maintenance_routine": 2.5, "safety_incident": 3.5, "regulation_compliance": 3.0,
        "environment_routine": 2.0, "breakdown_major": 2.0, "crisis_event": 2.0,
        "human_relations": 0.6, "holidays_culture": 0.3, "customer_interaction": 0.4,
    },
    # Power generation & energy: maintenance, safety, regulation
    "power_energy": {
        "maintenance_routine": 3.0, "breakdown_major": 2.5, "environment_routine": 2.0,
        "safety_incident": 2.0, "regulation_compliance": 2.5, "technology_routine": 1.5,
        "customer_interaction": 0.2, "human_relations": 0.6, "supply_logistics": 1.5,
    },
    # IT / Software / Digital: technology dominant, low physical risk
    "it_digital": {
        "technology_routine": 5.0, "customer_interaction": 2.0, "learning_training": 2.0,
        "workforce_admin": 1.5, "business_update": 2.0,
        "maintenance_routine": 0.3, "safety_incident": 0.1, "environment_routine": 0.1,
        "supply_logistics": 0.3, "breakdown_major": 0.3,
    },
    # Healthcare & medical: workforce heavy, safety, customer (patient) interaction
    "healthcare": {
        "workforce_admin": 3.0, "safety_incident": 2.5, "customer_interaction": 2.5,
        "regulation_compliance": 2.5, "learning_training": 2.0, "supply_logistics": 1.5,
        "maintenance_routine": 0.5, "environment_routine": 0.3, "breakdown_major": 0.5,
    },
    # Retail & hospitality: customer dominant, workforce, low maintenance
    "retail_hospitality": {
        "customer_interaction": 4.0, "supply_logistics": 2.5, "workforce_admin": 2.0,
        "holidays_culture": 2.0, "competition_market": 2.0,
        "maintenance_routine": 0.3, "safety_incident": 0.4, "environment_routine": 0.3,
        "technology_routine": 1.0, "regulation_compliance": 1.0,
    },
    # Education & training: learning focus, low physical risk
    "education": {
        "learning_training": 4.0, "customer_interaction": 2.0, "workforce_admin": 2.0,
        "holidays_culture": 2.5, "regulation_compliance": 1.5,
        "maintenance_routine": 0.3, "safety_incident": 0.2, "environment_routine": 0.2,
        "breakdown_major": 0.2, "supply_logistics": 0.5,
    },
    # Logistics & transport: supply chain dominant, safety moderate
    "logistics": {
        "supply_logistics": 4.0, "workforce_admin": 2.0, "safety_incident": 1.5,
        "customer_interaction": 2.0, "technology_routine": 1.5, "breakdown_major": 1.5,
        "maintenance_routine": 1.5, "environment_routine": 0.5, "regulation_compliance": 1.0,
    },
    # Entertainment & media: creative, customer focused, technology
    "entertainment": {
        "customer_interaction": 3.0, "technology_routine": 2.0, "workforce_admin": 2.0,
        "holidays_culture": 2.5, "competition_market": 2.0, "business_update": 1.5,
        "maintenance_routine": 0.5, "safety_incident": 0.3, "environment_routine": 0.2,
    },
    # Pharma & biotech: quality/regulation dominant, strict compliance
    "pharma_biotech": {
        "quality_routine": 4.5, "regulation_compliance": 4.0, "maintenance_routine": 1.5,
        "supply_logistics": 1.5, "learning_training": 2.0, "safety_incident": 1.0,
        "environment_routine": 0.5, "customer_interaction": 0.5, "breakdown_major": 0.5,
    },
    # Textile & garment: quality, labor intensive, moderate maintenance
    "textile": {
        "quality_routine": 2.5, "maintenance_routine": 2.0, "workforce_admin": 2.0,
        "supply_logistics": 1.5, "environment_routine": 1.5, "safety_incident": 1.0,
        "technology_routine": 0.5, "customer_interaction": 0.8, "regulation_compliance": 1.0,
    },
    # Renewable energy: environment/tech focus, low safety risk
    "renewable": {
        "environment_routine": 3.0, "maintenance_routine": 1.5, "technology_routine": 2.5,
        "regulation_compliance": 1.5, "breakdown_major": 1.0,
        "safety_incident": 0.5, "customer_interaction": 0.3, "human_relations": 0.5,
        "supply_logistics": 0.8,
    },
    # Space & aerospace: extreme quality, regulation, technology
    "space_aerospace": {
        "quality_routine": 5.0, "regulation_compliance": 3.5, "technology_routine": 3.0,
        "maintenance_routine": 2.0, "supply_logistics": 2.0, "learning_training": 2.0,
        "safety_incident": 1.0, "environment_routine": 0.2, "breakdown_major": 0.5,
    },
    # Personal care & wellness: customer service, hygiene
    "personal_care": {
        "customer_interaction": 3.5, "quality_routine": 2.0, "workforce_admin": 1.5,
        "regulation_compliance": 1.5, "supply_logistics": 1.5, "holidays_culture": 1.5,
        "safety_incident": 0.5, "maintenance_routine": 0.5, "environment_routine": 0.3,
    },
}

# Mapping: subsector → family weight profile name
_SUBSECTOR_TO_FAMILY = {
    "metallurgy": "heavy_process", "cement": "heavy_process",
    "chemical": "heavy_process", "petrochemical": "oil_gas",
    "oil_gas": "oil_gas", "gas": "oil_gas", "oil": "oil_gas",
    "coal": "mining", "mining": "mining", "quarrying": "mining", "stone": "mining",
    "power_generation": "power_energy", "energy": "power_energy",
    "renewable": "renewable",
    "food_processing": "food_bev", "food_beverage": "food_bev",
    "fmcg": "food_bev", "tobacco": "food_bev",
    "agriculture": "agriculture", "horticulture": "agriculture",
    "fisheries": "agriculture", "livestock": "agriculture",
    "forestry": "agriculture", "environmental": "agriculture",
    "civil": "construction", "construction": "construction",
    "building_material": "construction",
    "textile": "textile", "textile_garment": "textile",
    "leather": "textile", "footwear": "textile",
    "software": "it_digital", "it_services": "it_digital",
    "ai_data": "it_digital", "telecom": "it_digital",
    "media": "entertainment", "robotics": "it_digital",
    "space": "space_aerospace", "aerospace": "space_aerospace",
    "healthcare": "healthcare", "medical": "healthcare",
    "medical_tech": "healthcare", "biotech": "pharma_biotech",
    "pharmaceutical": "pharma_biotech", "wellness": "personal_care",
    "personal_care": "personal_care",
    "retail": "retail_hospitality", "hospitality": "retail_hospitality",
    "tourism": "retail_hospitality", "entertainment": "entertainment",
    "services": "retail_hospitality", "facility_management": "retail_hospitality",
    "storage": "logistics", "shipping": "logistics", "logistics": "logistics",
    "education": "education",
    "banking": "it_digital", "finance": "it_digital",
    "insurance": "it_digital", "consulting": "it_digital",
    "security": "retail_hospitality",
    "electrical": "light_manufacturing", "electronics": "light_manufacturing",
    "precision": "light_manufacturing", "advanced_materials": "light_manufacturing",
    "machinery": "heavy_process", "heavy_engineering": "heavy_process",
    "automobile": "light_manufacturing", "appliance": "light_manufacturing",
    "rubber": "light_manufacturing", "plastic": "light_manufacturing",
    "paper_pulp": "heavy_process", "printing": "light_manufacturing",
    "furniture": "light_manufacturing", "wood": "light_manufacturing",
    "utility": "power_energy", "water": "power_energy",
    "waste": "heavy_process", "recycling": "heavy_process",
    "defense": "heavy_process", "safety": "it_digital",
    "maintenance": "heavy_process", "manufacturing": "light_manufacturing",
    "mechanical": "heavy_process",
    "misc": "retail_hospitality",
}


def _apply_family_weights():
    """Auto-assign event weights to all industries based on subsector family.
    
    Only assigns if the industry doesn't already have a direct entry.
    Called once at module load time.
    """
    try:
        from world_engine.registry import INDUSTRIES
    except ImportError:
        return
    
    for iid, industry in INDUSTRIES.items():
        if iid in INDUSTRY_EVENT_WEIGHTS:
            continue  # Already has direct weights
        
        family_name = _SUBSECTOR_TO_FAMILY.get(industry.subsector)
        if family_name and family_name in _WEIGHT_FAMILIES:
            INDUSTRY_EVENT_WEIGHTS[iid] = _WEIGHT_FAMILIES[family_name].copy()


# Apply family weights at module load
_apply_family_weights()
