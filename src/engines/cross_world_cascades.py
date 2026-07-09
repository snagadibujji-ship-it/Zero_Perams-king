"""Cross-World Cascade Engine — events ripple across all 20 worlds.

When something happens in one world, it affects others:
- Energy blackout → Construction delays, Hospital backup generators, Real Estate value drop
- Pandemic → Healthcare surge, E-Commerce boom, Transport shutdown, Insurance claims
- Cyber attack → Defense escalation, Finance freeze, Insurance claims, Media coverage
"""
import random
from typing import Dict, List, Tuple

# Define 60+ cascade rules
# (trigger_world, trigger_event, affected_world, effect, probability, delay_hours)
CASCADE_RULES: List[Tuple[str, str, str, str, float, int]] = [
    # === NATURAL DISASTERS ===
    ("energy", "blackout_cascade", "healthcare", "backup_generator_activated", 0.95, 0),
    ("energy", "blackout_cascade", "construction", "site_shutdown_no_power", 0.8, 1),
    ("energy", "blackout_cascade", "realestate", "property_value_dip", 0.3, 72),
    ("energy", "blackout_cascade", "finance", "trading_halt", 0.6, 0),
    ("energy", "blackout_cascade", "transport", "signal_failure_trains", 0.7, 0),
    ("energy", "blackout_cascade", "ecommerce", "warehouse_operations_halted", 0.5, 2),
    ("agriculture", "earthquake_damage", "insurance", "mass_claims_filed", 0.9, 24),
    ("agriculture", "earthquake_damage", "construction", "emergency_rebuild_demand", 0.7, 48),
    ("agriculture", "earthquake_damage", "transport", "road_network_disrupted", 0.8, 0),
    ("agriculture", "earthquake_damage", "realestate", "structural_assessment_required", 0.85, 12),
    ("agriculture", "flood_event", "insurance", "flood_claims_surge", 0.95, 6),
    ("agriculture", "flood_event", "energy", "substation_flood_damage", 0.4, 0),
    ("agriculture", "flood_event", "transport", "route_closures", 0.75, 0),

    # === CYBER ATTACKS ===
    ("defense", "cyber_attack_detected", "finance", "emergency_transaction_freeze", 0.8, 0),
    ("defense", "cyber_attack_detected", "healthcare", "patient_data_lockdown", 0.6, 1),
    ("defense", "cyber_attack_detected", "media", "breaking_news_coverage", 0.9, 0),
    ("defense", "cyber_attack_detected", "insurance", "cyber_liability_claims", 0.7, 24),
    ("defense", "cyber_attack_detected", "energy", "grid_security_escalation", 0.75, 0),
    ("finance", "data_breach", "media", "public_disclosure_coverage", 0.85, 2),
    ("finance", "data_breach", "insurance", "cyber_insurance_claim", 0.9, 12),
    ("finance", "data_breach", "defense", "threat_level_raised", 0.5, 0),
    ("healthcare", "ransomware_attack", "defense", "incident_response_deployed", 0.7, 0),
    ("healthcare", "ransomware_attack", "media", "patient_safety_alert_broadcast", 0.8, 1),
    ("healthcare", "ransomware_attack", "insurance", "liability_review_triggered", 0.75, 48),

    # === PANDEMICS ===
    ("healthcare", "pandemic_declared", "ecommerce", "demand_surge_essentials", 0.95, 24),
    ("healthcare", "pandemic_declared", "transport", "capacity_restrictions", 0.9, 48),
    ("healthcare", "pandemic_declared", "education", "remote_learning_mandate", 0.85, 72),
    ("healthcare", "pandemic_declared", "insurance", "health_claims_spike", 0.9, 168),
    ("healthcare", "pandemic_declared", "biotech", "vaccine_research_funding", 0.95, 24),
    ("healthcare", "pandemic_declared", "finance", "market_volatility_spike", 0.8, 0),
    ("healthcare", "pandemic_declared", "construction", "project_delays_labor_shortage", 0.7, 168),
    ("healthcare", "pandemic_declared", "media", "24hr_pandemic_coverage", 0.95, 0),

    # === MARKET CRASHES ===
    ("finance", "market_crash", "realestate", "mortgage_rate_spike", 0.75, 48),
    ("finance", "market_crash", "construction", "project_funding_frozen", 0.7, 72),
    ("finance", "market_crash", "insurance", "portfolio_loss_claims", 0.6, 24),
    ("finance", "market_crash", "ecommerce", "consumer_spending_drop", 0.65, 168),
    ("finance", "market_crash", "energy", "capex_budget_cuts", 0.5, 168),
    ("finance", "market_crash", "biotech", "funding_round_cancelled", 0.6, 48),

    # === REGULATORY CHANGES ===
    ("biotech", "new_regulation_passed", "finance", "compliance_cost_increase", 0.8, 720),
    ("biotech", "new_regulation_passed", "healthcare", "treatment_protocol_update", 0.7, 720),
    ("energy", "emissions_regulation", "finance", "carbon_credit_price_surge", 0.7, 168),
    ("energy", "emissions_regulation", "construction", "green_building_mandate", 0.6, 720),
    ("energy", "emissions_regulation", "transport", "fleet_electrification_push", 0.5, 720),
    ("defense", "export_control_update", "robotics", "component_supply_restricted", 0.6, 168),
    ("defense", "export_control_update", "space", "launch_approval_delayed", 0.4, 336),
    ("media", "data_privacy_law", "ecommerce", "consent_mechanism_overhaul", 0.8, 720),
    ("media", "data_privacy_law", "finance", "customer_data_audit", 0.7, 336),

    # === SUPPLY CHAIN DISRUPTION ===
    ("transport", "port_strike", "construction", "material_delivery_delayed", 0.85, 48),
    ("transport", "port_strike", "robotics", "component_shortage", 0.7, 72),
    ("transport", "port_strike", "agriculture", "export_backlog", 0.8, 24),
    ("transport", "port_strike", "ecommerce", "fulfillment_delays", 0.9, 24),
    ("transport", "port_strike", "energy", "fuel_supply_constrained", 0.5, 72),
    ("robotics", "chip_shortage", "construction", "automation_equipment_delayed", 0.6, 168),
    ("robotics", "chip_shortage", "defense", "weapons_system_production_slowed", 0.5, 336),
    ("robotics", "chip_shortage", "ecommerce", "warehouse_robot_shortage", 0.4, 168),

    # === SPACE EVENTS ===
    ("space", "satellite_failure", "defense", "surveillance_gap_detected", 0.8, 0),
    ("space", "satellite_failure", "media", "broadcast_signal_lost", 0.6, 0),
    ("space", "satellite_failure", "insurance", "space_asset_claim", 0.9, 24),
    ("space", "satellite_failure", "agriculture", "gps_guidance_disrupted", 0.5, 0),
    ("space", "satellite_failure", "transport", "navigation_degraded", 0.6, 0),
    ("space", "solar_storm", "energy", "grid_transformer_damage", 0.4, 2),
    ("space", "solar_storm", "defense", "communications_degraded", 0.7, 0),
    ("space", "solar_storm", "media", "satellite_broadcast_interrupted", 0.5, 0),

    # === WAR / CONFLICT ===
    ("defense", "armed_conflict_escalation", "energy", "oil_price_spike", 0.9, 0),
    ("defense", "armed_conflict_escalation", "finance", "safe_haven_rush", 0.85, 0),
    ("defense", "armed_conflict_escalation", "insurance", "war_risk_premium_increase", 0.8, 24),
    ("defense", "armed_conflict_escalation", "transport", "airspace_closure", 0.7, 0),
    ("defense", "armed_conflict_escalation", "media", "war_correspondent_deployed", 0.95, 0),
    ("defense", "armed_conflict_escalation", "realestate", "conflict_zone_value_collapse", 0.6, 168),

    # === CLIMATE EVENTS ===
    ("agriculture", "severe_drought", "energy", "hydropower_output_reduced", 0.7, 168),
    ("agriculture", "severe_drought", "insurance", "crop_failure_claims", 0.9, 336),
    ("agriculture", "severe_drought", "realestate", "farmland_value_decline", 0.5, 720),
    ("agriculture", "severe_drought", "transport", "river_navigation_halted", 0.4, 168),
    ("agriculture", "severe_drought", "ecommerce", "food_price_inflation", 0.6, 336),
    ("energy", "hurricane_landfall", "construction", "emergency_repair_mobilization", 0.9, 24),
    ("energy", "hurricane_landfall", "insurance", "catastrophe_claims_wave", 0.95, 12),
    ("energy", "hurricane_landfall", "transport", "port_closure", 0.85, 0),
    ("energy", "hurricane_landfall", "realestate", "coastal_property_damage", 0.8, 0),

    # === TECHNOLOGY DISRUPTION ===
    ("coding", "ai_breakthrough", "media", "tech_hype_cycle_coverage", 0.8, 0),
    ("coding", "ai_breakthrough", "robotics", "autonomous_capability_leap", 0.6, 336),
    ("coding", "ai_breakthrough", "education", "curriculum_overhaul_pressure", 0.7, 720),
    ("coding", "ai_breakthrough", "finance", "tech_stock_rally", 0.75, 24),
    ("coding", "ai_breakthrough", "defense", "ai_weapons_concern", 0.5, 168),
    ("robotics", "autonomous_vehicle_accident", "media", "public_safety_coverage", 0.9, 0),
    ("robotics", "autonomous_vehicle_accident", "insurance", "liability_precedent_case", 0.8, 72),
    ("robotics", "autonomous_vehicle_accident", "transport", "autonomous_fleet_grounded", 0.6, 24),
    ("robotics", "autonomous_vehicle_accident", "coding", "safety_audit_triggered", 0.7, 48),

    # === EDUCATION / SOCIAL ===
    ("education", "major_research_publication", "biotech", "new_research_direction", 0.4, 720),
    ("education", "major_research_publication", "coding", "open_source_implementation", 0.5, 336),
    ("education", "labor_shortage_warning", "construction", "wage_inflation", 0.6, 336),
    ("education", "labor_shortage_warning", "robotics", "automation_investment_increase", 0.5, 336),

    # === INSURANCE FEEDBACK LOOPS ===
    ("insurance", "premium_hike_announced", "realestate", "operating_cost_increase", 0.7, 168),
    ("insurance", "premium_hike_announced", "construction", "project_budget_overrun", 0.5, 168),
    ("insurance", "premium_hike_announced", "transport", "fleet_insurance_renegotiation", 0.6, 336),

    # === ECOMMERCE DISRUPTIONS ===
    ("ecommerce", "platform_outage", "media", "consumer_outrage_coverage", 0.7, 0),
    ("ecommerce", "platform_outage", "finance", "stock_price_drop", 0.6, 0),
    ("ecommerce", "platform_outage", "transport", "delivery_schedule_disrupted", 0.5, 2),

    # === REALESTATE TRIGGERS ===
    ("realestate", "housing_bubble_burst", "finance", "mortgage_default_wave", 0.8, 168),
    ("realestate", "housing_bubble_burst", "construction", "new_project_cancellations", 0.85, 72),
    ("realestate", "housing_bubble_burst", "insurance", "foreclosure_claims", 0.6, 336),

    # === MEDIA TRIGGERS ===
    ("media", "whistleblower_leak", "defense", "security_review_initiated", 0.6, 24),
    ("media", "whistleblower_leak", "finance", "stock_sell_off", 0.5, 0),
    ("media", "whistleblower_leak", "biotech", "clinical_trial_scrutiny", 0.4, 72),

    # === GAMING WORLD ===
    ("gaming", "esports_gambling_scandal", "finance", "betting_platform_investigation", 0.6, 24),
    ("gaming", "esports_gambling_scandal", "media", "scandal_coverage_viral", 0.8, 0),
    ("gaming", "esports_gambling_scandal", "insurance", "fraud_claim_review", 0.4, 72),
    ("coding", "ai_breakthrough", "gaming", "procedural_generation_revolution", 0.5, 336),
    ("finance", "market_crash", "gaming", "microtransaction_revenue_drop", 0.4, 168),
    ("energy", "blackout_cascade", "gaming", "server_farm_offline", 0.6, 0),

    # === GOVERNMENT WORLD ===
    ("government", "sanctions_imposed", "finance", "asset_freeze_compliance", 0.85, 24),
    ("government", "sanctions_imposed", "energy", "import_restriction_enforced", 0.7, 48),
    ("government", "sanctions_imposed", "defense", "arms_embargo_activated", 0.8, 24),
    ("government", "sanctions_imposed", "transport", "trade_route_rerouting", 0.6, 72),
    ("government", "infrastructure_bill_passed", "construction", "public_works_boom", 0.9, 336),
    ("government", "infrastructure_bill_passed", "transport", "transit_expansion_funded", 0.8, 336),
    ("government", "infrastructure_bill_passed", "energy", "grid_modernization_funded", 0.7, 336),
    ("defense", "armed_conflict_escalation", "government", "emergency_powers_invoked", 0.8, 0),
    ("healthcare", "pandemic_declared", "government", "public_health_emergency_declared", 0.95, 12),
    ("finance", "market_crash", "government", "stimulus_package_debated", 0.7, 168),

    # === SCIENCE WORLD ===
    ("science", "fusion_breakthrough", "energy", "investment_pivot_to_fusion", 0.6, 720),
    ("science", "fusion_breakthrough", "finance", "clean_energy_stock_surge", 0.7, 24),
    ("science", "fusion_breakthrough", "media", "scientific_milestone_coverage", 0.9, 0),
    ("science", "fusion_breakthrough", "defense", "strategic_energy_reassessment", 0.4, 336),
    ("science", "climate_report_published", "government", "emissions_policy_review", 0.7, 168),
    ("science", "climate_report_published", "agriculture", "farming_practice_adaptation", 0.5, 720),
    ("science", "climate_report_published", "insurance", "risk_model_recalibration", 0.6, 336),
    ("education", "major_research_publication", "science", "peer_replication_attempts", 0.6, 336),
    ("biotech", "new_regulation_passed", "science", "research_compliance_burden", 0.5, 168),

    # === CIVILIZATION WORLD ===
    ("government", "mass_migration_event", "realestate", "housing_demand_spike", 0.8, 168),
    ("government", "mass_migration_event", "healthcare", "public_health_capacity_strain", 0.7, 72),
    ("government", "mass_migration_event", "education", "enrollment_surge", 0.6, 336),
    ("government", "mass_migration_event", "construction", "emergency_housing_demand", 0.7, 168),
    ("government", "social_unrest", "media", "protest_coverage_24hr", 0.9, 0),
    ("government", "social_unrest", "finance", "investor_confidence_drop", 0.5, 24),
    ("government", "social_unrest", "insurance", "property_damage_claims", 0.6, 48),
    ("government", "social_unrest", "transport", "transit_service_suspended", 0.5, 0),
    ("defense", "armed_conflict_escalation", "government", "refugee_crisis_triggered", 0.7, 168),
    ("agriculture", "severe_drought", "government", "food_insecurity_unrest", 0.5, 720),

    # === CONSTRUCTION TRIGGERS ===
    ("construction", "major_collapse_incident", "insurance", "structural_liability_claims", 0.95, 12),
    ("construction", "major_collapse_incident", "media", "disaster_scene_coverage", 0.9, 0),
    ("construction", "major_collapse_incident", "government", "safety_regulation_review", 0.7, 72),
    ("construction", "major_collapse_incident", "realestate", "neighboring_property_devaluation", 0.5, 168),
    ("construction", "megaproject_completion", "realestate", "surrounding_land_value_increase", 0.7, 168),
    ("construction", "megaproject_completion", "transport", "traffic_pattern_shift", 0.6, 336),

    # === CYBERSECURITY TRIGGERS (new world 21) ===
    ("cybersecurity", "major_breach", "finance", "emergency_account_freeze", 0.85, 0),
    ("cybersecurity", "major_breach", "healthcare", "patient_data_lockdown", 0.7, 1),
    ("cybersecurity", "major_breach", "ecommerce", "payment_system_shutdown", 0.75, 0),
    ("cybersecurity", "major_breach", "media", "breaking_news_data_breach", 0.95, 1),
    ("cybersecurity", "major_breach", "insurance", "cyber_liability_claims_surge", 0.9, 24),
    ("cybersecurity", "major_breach", "legal", "class_action_notification", 0.7, 72),
    ("cybersecurity", "major_breach", "government", "regulatory_investigation_launched", 0.6, 48),
    ("cybersecurity", "ransomware_attack", "manufacturing", "production_line_shutdown", 0.6, 0),
    ("cybersecurity", "ransomware_attack", "supplychain", "logistics_system_offline", 0.5, 2),
    ("cybersecurity", "ransomware_attack", "telecom", "network_management_degraded", 0.4, 0),

    # === SUPPLY CHAIN TRIGGERS (new world 22) ===
    ("supplychain", "critical_shortage", "manufacturing", "production_slowdown", 0.85, 24),
    ("supplychain", "critical_shortage", "ecommerce", "out_of_stock_surge", 0.8, 48),
    ("supplychain", "critical_shortage", "healthcare", "medical_supply_rationing", 0.5, 72),
    ("supplychain", "port_disruption", "maritime", "vessel_queue_buildup", 0.9, 0),
    ("supplychain", "port_disruption", "construction", "material_delivery_halted", 0.7, 48),
    ("supplychain", "port_disruption", "mining", "export_shipment_delayed", 0.6, 24),
    ("supplychain", "supplier_bankruptcy", "manufacturing", "alternate_sourcing_emergency", 0.8, 72),
    ("supplychain", "supplier_bankruptcy", "finance", "credit_exposure_writedown", 0.5, 168),

    # === MANUFACTURING TRIGGERS (new world 23) ===
    ("manufacturing", "product_recall", "legal", "liability_litigation_filed", 0.8, 72),
    ("manufacturing", "product_recall", "insurance", "product_liability_claim", 0.9, 48),
    ("manufacturing", "product_recall", "media", "consumer_safety_alert", 0.85, 12),
    ("manufacturing", "product_recall", "supplychain", "reverse_logistics_activated", 0.7, 24),
    ("manufacturing", "explosion_incident", "insurance", "industrial_accident_claim", 0.95, 12),
    ("manufacturing", "explosion_incident", "mining", "safety_review_triggered", 0.4, 168),

    # === AVIATION TRIGGERS (new world 25) ===
    ("aviation", "major_incident", "insurance", "aviation_hull_loss_claim", 0.95, 0),
    ("aviation", "major_incident", "media", "aviation_disaster_coverage", 0.99, 0),
    ("aviation", "major_incident", "legal", "wrongful_death_litigation", 0.8, 168),
    ("aviation", "major_incident", "government", "safety_investigation_ordered", 0.95, 0),
    ("aviation", "airspace_closure", "transport", "ground_transport_surge", 0.7, 2),
    ("aviation", "airspace_closure", "hospitality", "hotel_demand_spike", 0.6, 4),

    # === TELECOM TRIGGERS (new world 26) ===
    ("telecom", "major_outage", "finance", "trading_connectivity_lost", 0.6, 0),
    ("telecom", "major_outage", "ecommerce", "transaction_failures", 0.7, 0),
    ("telecom", "major_outage", "healthcare", "telemedicine_disrupted", 0.5, 0),
    ("telecom", "major_outage", "cybersecurity", "monitoring_blind_spots", 0.6, 0),

    # === MARITIME TRIGGERS (new world 27) ===
    ("maritime", "canal_blockage", "supplychain", "global_supply_disruption", 0.95, 0),
    ("maritime", "canal_blockage", "manufacturing", "component_shortage_wave", 0.7, 168),
    ("maritime", "canal_blockage", "ecommerce", "delivery_delays_global", 0.8, 72),
    ("maritime", "oil_spill", "insurance", "marine_pollution_claim", 0.95, 24),
    ("maritime", "oil_spill", "legal", "environmental_litigation", 0.8, 72),
    ("maritime", "oil_spill", "energy", "fuel_supply_disruption", 0.5, 48),

    # === PHARMA TRIGGERS (new world 28) ===
    ("pharma", "drug_shortage", "healthcare", "treatment_protocol_change", 0.8, 48),
    ("pharma", "drug_shortage", "insurance", "formulary_adjustment_costs", 0.5, 168),
    ("pharma", "clinical_trial_failure", "finance", "stock_price_crash", 0.7, 0),
    ("pharma", "clinical_trial_failure", "biotech", "partnership_terminated", 0.4, 72),
    ("pharma", "fda_warning_letter", "legal", "shareholder_lawsuit", 0.5, 168),
    ("pharma", "fda_warning_letter", "media", "pharma_safety_reporting", 0.7, 24),

    # === MINING TRIGGERS (new world 29) ===
    ("mining", "tailings_dam_failure", "insurance", "catastrophic_loss_claim", 0.99, 0),
    ("mining", "tailings_dam_failure", "legal", "criminal_prosecution_filed", 0.7, 168),
    ("mining", "tailings_dam_failure", "media", "environmental_disaster_coverage", 0.99, 0),
    ("mining", "tailings_dam_failure", "government", "mining_moratorium_declared", 0.6, 336),
    ("mining", "commodity_price_crash", "finance", "mining_stocks_plunge", 0.8, 0),
    ("mining", "commodity_price_crash", "construction", "material_cost_reduction", 0.5, 168),

    # === HOSPITALITY TRIGGERS (new world 30) ===
    ("hospitality", "food_safety_outbreak", "healthcare", "mass_patient_intake", 0.7, 12),
    ("hospitality", "food_safety_outbreak", "legal", "negligence_lawsuit_filed", 0.6, 168),
    ("hospitality", "food_safety_outbreak", "media", "health_scare_reporting", 0.8, 6),
    ("hospitality", "major_event", "transport", "traffic_congestion_surge", 0.7, 0),
    ("hospitality", "major_event", "telecom", "network_congestion_local", 0.5, 0),

    # === LEGAL TRIGGERS (new world 24) ===
    ("legal", "landmark_ruling", "finance", "compliance_cost_revision", 0.6, 168),
    ("legal", "landmark_ruling", "biotech", "patent_landscape_shift", 0.4, 336),
    ("legal", "class_action_certified", "insurance", "reserve_increase_required", 0.8, 48),
    ("legal", "class_action_certified", "media", "corporate_accountability_coverage", 0.7, 24),
]


# All 30 worlds for validation
ALL_WORLDS = [
    "agriculture", "aviation", "biotech", "coding", "construction",
    "cybersecurity", "defense", "ecommerce", "education", "energy",
    "finance", "gaming", "government", "healthcare", "hospitality",
    "industries", "insurance", "legal", "manufacturing", "maritime",
    "media", "mining", "pharma", "realestate", "robotics",
    "science", "space", "supplychain", "telecom", "transport",
]


class CrossWorldCascade:
    """Engine that determines how events in one world trigger cascading effects in other worlds."""

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.pending_cascades: List[Dict] = []  # events waiting to trigger
        self.cascade_history: List[Dict] = []  # log of triggered cascades
        self._rules = list(CASCADE_RULES)

    def get_all_rules(self) -> List[Tuple[str, str, str, str, float, int]]:
        """Return all cascade rules."""
        return self._rules

    def get_rules_for_world(self, world: str) -> List[Tuple[str, str, str, str, float, int]]:
        """Return all rules triggered by events in a specific world."""
        return [r for r in self._rules if r[0] == world]

    def get_rules_affecting_world(self, world: str) -> List[Tuple[str, str, str, str, float, int]]:
        """Return all rules that could affect a specific world."""
        return [r for r in self._rules if r[2] == world]

    def check_cascades(self, record: Dict, source_world: str) -> List[Dict]:
        """Given a record from source_world, return any cascade effects that fire.

        Checks each rule matching the source world and event type. Each matching rule
        fires probabilistically based on the rule's probability field.

        Args:
            record: The event record containing at minimum an 'event_type' key.
            source_world: The world that generated the event.

        Returns:
            List of cascade effect dicts with keys:
                - source_world, source_event, target_world, effect, delay_hours, triggered_by
        """
        event_type = record.get("event_type", "")
        cascades_triggered: List[Dict] = []

        matching_rules = [
            r for r in self._rules
            if r[0] == source_world and r[1] == event_type
        ]

        for rule in matching_rules:
            trigger_world, trigger_event, affected_world, effect, probability, delay_hours = rule
            if self.rng.random() < probability:
                cascade_event = {
                    "source_world": trigger_world,
                    "source_event": trigger_event,
                    "target_world": affected_world,
                    "effect": effect,
                    "delay_hours": delay_hours,
                    "probability": probability,
                    "triggered_by": record.get("record_id", "unknown"),
                }
                cascades_triggered.append(cascade_event)

                if delay_hours > 0:
                    self.pending_cascades.append(cascade_event)

        self.cascade_history.extend(cascades_triggered)
        return cascades_triggered

    def inject_cascade_context(self, record: Dict, source_world: str) -> Dict:
        """Add cascade awareness to records.

        Enriches the record with information about what cascades it could trigger
        and what cascades from other worlds might be affecting it.

        Args:
            record: The event record to enrich.
            source_world: The world this record belongs to.

        Returns:
            The record with added 'cascade_context' field.
        """
        outbound_rules = self.get_rules_for_world(source_world)
        inbound_rules = self.get_rules_affecting_world(source_world)

        # Find pending cascades that target this world
        active_inbound = [
            c for c in self.pending_cascades
            if c["target_world"] == source_world
        ]

        record["cascade_context"] = {
            "potential_outbound_cascades": len(outbound_rules),
            "potential_inbound_cascades": len(inbound_rules),
            "active_inbound_effects": [
                {"effect": c["effect"], "from": c["source_world"]}
                for c in active_inbound
            ],
            "worlds_this_can_affect": list(set(r[2] for r in outbound_rules)),
            "worlds_that_affect_this": list(set(r[0] for r in inbound_rules)),
        }

        return record

    def get_cascade_chain(self, source_world: str, event_type: str, max_depth: int = 3) -> List[Dict]:
        """Simulate a full cascade chain — cascades triggering further cascades.

        Args:
            source_world: The originating world.
            event_type: The triggering event type.
            max_depth: Maximum cascade depth to prevent infinite loops.

        Returns:
            List of all cascade effects across all depths.
        """
        all_effects: List[Dict] = []
        current_events = [{"source_world": source_world, "event_type": event_type, "record_id": "chain_root"}]

        for depth in range(max_depth):
            next_events = []
            for event in current_events:
                effects = self.check_cascades(event, event["source_world"])
                for eff in effects:
                    eff["cascade_depth"] = depth + 1
                    all_effects.append(eff)
                    # The effect becomes a new event in the target world
                    next_events.append({
                        "source_world": eff["target_world"],
                        "event_type": eff["effect"],
                        "record_id": f"cascade_depth_{depth+1}",
                    })
            current_events = next_events
            if not current_events:
                break

        return all_effects

    def get_world_connectivity(self) -> Dict[str, Dict[str, int]]:
        """Return a connectivity matrix showing how many rules connect each pair of worlds."""
        connectivity: Dict[str, Dict[str, int]] = {}
        for rule in self._rules:
            src, _, tgt = rule[0], rule[1], rule[2]
            if src not in connectivity:
                connectivity[src] = {}
            connectivity[src][tgt] = connectivity[src].get(tgt, 0) + 1
        return connectivity

    def get_statistics(self) -> Dict:
        """Return statistics about the cascade rule set."""
        trigger_worlds = set(r[0] for r in self._rules)
        affected_worlds = set(r[2] for r in self._rules)
        all_events = set(r[1] for r in self._rules)

        return {
            "total_rules": len(self._rules),
            "unique_trigger_worlds": len(trigger_worlds),
            "unique_affected_worlds": len(affected_worlds),
            "unique_event_types": len(all_events),
            "trigger_worlds": sorted(trigger_worlds),
            "affected_worlds": sorted(affected_worlds),
            "avg_probability": sum(r[4] for r in self._rules) / len(self._rules),
            "cascades_triggered_total": len(self.cascade_history),
            "pending_cascades": len(self.pending_cascades),
        }

    def clear_pending(self) -> int:
        """Clear all pending cascades and return how many were cleared."""
        count = len(self.pending_cascades)
        self.pending_cascades = []
        return count
