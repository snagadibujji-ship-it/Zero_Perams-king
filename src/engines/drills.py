"""
Industry Drills & Safety Training Events
==========================================
Every industry has mandatory drills and training requirements.
This module injects them at REALISTIC frequencies based on
actual regulations (India Factories Act, OSHA, DGMS, NBC).

Frequencies are based on:
- India: Fire drill every 3 months (Factories Act + NBC 2016)
- Mining: Rescue drill monthly (DGMS Coal Mines Regulations)
- Chemical/HAZMAT: Emergency drill quarterly (MSIHC Rules 1989)
- Hospital: Code Blue mock weekly, fire drill quarterly
- Construction: Toolbox talk DAILY (start of every shift)
- Data center: Failover test monthly
- Food: Recall procedure drill quarterly
- Oil & Gas: Emergency shutdown drill quarterly
- All industries: First aid training annually

In a generation run of 1000 events (~5 days of operations):
- Daily drills (toolbox talks): appear ~5 times
- Weekly drills (code blue): appear ~1 time
- Monthly drills (mine rescue): appear ~0.15 times
- Quarterly drills (fire): appear ~0.05 times
"""
import random
from typing import Optional, Dict, List


# ═══════════════════════════════════════════════════════════════════
# DRILL DEFINITIONS — What each industry actually does
# ═══════════════════════════════════════════════════════════════════

DRILL_PROFILES: Dict[str, Dict] = {
    # Mining: Most drills (high-risk environment)
    "mining": {
        "drills": [
            {"name": "pre_shift_gas_check", "frequency": "every_shift",
             "messages": [
                 "pre-shift gas examination starting. all methanometers calibrated. entering sections now",
                 "gas check complete: CH4 0.3%, CO nil, O2 20.9%. all sections cleared for work",
                 "methane reading slightly elevated at face: 0.8%. increasing ventilation before clearing",
             ]},
            {"name": "mine_rescue_drill", "frequency": "monthly",
             "messages": [
                 "mine rescue drill today. rescue team assembling with proto gear at lamp room",
                 "rescue drill: simulated roof fall in panel 4. team deployed with stretcher and oxygen",
                 "monthly mine rescue drill complete. time: 18 minutes to reach simulated casualty. debrief at 3pm",
             ]},
            {"name": "fire_drill", "frequency": "quarterly",
             "messages": [
                 "quarterly fire drill today. all surface and underground personnel to practice evacuation routes",
                 "fire drill complete. evacuation time 11 minutes. 3 people missed assembly point — retraining needed",
             ]},
            {"name": "safety_training", "frequency": "weekly",
             "messages": [
                 "weekly safety topic: roof support and bolting patterns. attendance mandatory",
                 "safety class today: proper use of self-rescuer apparatus. every miner must attend",
                 "gas detection equipment training for new batch of deputies. 2 hours in training room",
             ]},
        ],
    },
    
    # Oil & Gas: High consequence drills
    "oil_gas": {
        "drills": [
            {"name": "emergency_shutdown_drill", "frequency": "quarterly",
             "messages": [
                 "ESD drill scheduled today at 1400hrs. all operators to positions. this is a DRILL",
                 "emergency shutdown drill complete. valve closure times within spec. one delay on XV-201 — maintenance to check",
                 "quarterly emergency response drill: simulated H2S release at unit 5. muster point B drill",
             ]},
            {"name": "fire_fighting_drill", "frequency": "quarterly",
             "messages": [
                 "fire drill today: foam system test on tank farm. fire crew to don full gear",
                 "fire response drill complete. foam application time: 3 min 20 sec. acceptable",
                 "fixed fire monitor test on crude tanks. all 4 monitors operational. water curtain checked",
             ]},
            {"name": "toolbox_talk", "frequency": "daily",
             "messages": [
                 "morning toolbox talk: permit to work procedures and hot work precautions",
                 "pre-job safety briefing: confined space entry checklist reviewed with all involved",
                 "toolbox talk: H2S awareness and wind direction. everyone check personal gas monitors",
                 "daily safety topic: proper PPE for working with caustic. face shield + chemical gloves",
             ]},
            {"name": "muster_drill", "frequency": "monthly",
             "messages": [
                 "monthly muster drill: all personnel to assembly point A for headcount",
                 "alarm sounded. this is a DRILL. proceed to your designated muster point immediately",
                 "muster drill complete. headcount confirmed in 6 min 45 sec. target is under 5 min — improvement needed",
             ]},
        ],
    },
    
    # Construction: Daily toolbox talks are mandatory
    "construction": {
        "drills": [
            {"name": "toolbox_talk", "frequency": "daily",
             "messages": [
                 "morning toolbox talk: working at heights — always 100% tie-off above 2 meters",
                 "today's safety topic: excavation safety. no one enters trench without shoring",
                 "toolbox talk: crane signal hand signs. all riggers refresh before lift operation",
                 "safety briefing: hot work permit requirements. fire watch for 30 min after welding",
                 "pre-work briefing: scaffolding inspection — green tag = safe, red tag = do NOT use",
                 "daily safety moment: housekeeping — clear walkways, stack materials properly",
                 "toolbox talk: electrical safety near live lines. minimum approach distance 3 meters",
             ]},
            {"name": "fire_drill", "frequency": "quarterly",
             "messages": [
                 "quarterly fire drill. all workers to assembly point near main gate. take headcount",
                 "fire drill complete. evacuation time 5 min 30 sec for 140 workers. acceptable",
             ]},
            {"name": "first_aid_training", "frequency": "monthly",
             "messages": [
                 "first aid refresher training today at site office. CPR and wound management",
                 "emergency first responder training: how to handle fall from height casualty",
             ]},
        ],
    },
    
    # Hospital: Code Blue drills are weekly
    "healthcare": {
        "drills": [
            {"name": "code_blue_drill", "frequency": "weekly",
             "messages": [
                 "code blue mock drill at 2pm in ward 3. crash cart team to respond. THIS IS A DRILL",
                 "mock code blue complete. response time: 2 min 15 sec. defibrillator deployed correctly",
                 "weekly code blue practice: new residents practicing ACLS protocol on mannequin",
             ]},
            {"name": "fire_drill", "frequency": "quarterly",
             "messages": [
                 "fire drill today at 3pm. patient evacuation procedures to be practiced on 2nd floor",
                 "fire drill complete. horizontal evacuation time: 4 min. vertical evac not tested today",
                 "quarterly fire safety drill. all staff know extinguisher locations? check now",
             ]},
            {"name": "disaster_drill", "frequency": "biannual",
             "messages": [
                 "mass casualty drill next Thursday. simulating bus accident with 30 victims. ER, OT, blood bank all involved",
                 "disaster management drill debrief: triage process needs improvement. too many 'red' tagged as 'yellow'",
             ]},
            {"name": "infection_control_training", "frequency": "monthly",
             "messages": [
                 "infection control training: hand hygiene 5 moments. practical demonstration at all nursing stations",
                 "PPE donning and doffing practice for isolation ward staff. monthly refresher",
                 "biomedical waste segregation training. color coding: yellow, red, blue, white. no mixing",
             ]},
        ],
    },
    
    # Chemical/Pharma: HAZMAT drills
    "chemical": {
        "drills": [
            {"name": "chemical_spill_drill", "frequency": "quarterly",
             "messages": [
                 "chemical spill drill today: simulated HCl leak in reactor area. SCBA teams deploy",
                 "spill response drill complete. containment time: 8 minutes. decontamination shower tested",
                 "quarterly HAZMAT drill: ammonia release scenario. wind sock indicates east. evacuate west",
             ]},
            {"name": "fire_drill", "frequency": "quarterly",
             "messages": [
                 "fire drill: foam system activation test on solvent storage area",
                 "fire evacuation drill. all personnel including contractors to muster point C",
             ]},
            {"name": "safety_training", "frequency": "monthly",
             "messages": [
                 "MSDS training for new chemicals received this month. all operators must attend",
                 "process safety management refresher: HAZOP findings review with all shift engineers",
                 "safety induction for new contractor batch. 4 hours covering all hazards on site",
             ]},
        ],
    },
    
    # Food Processing: Recall and hygiene drills
    "food_processing": {
        "drills": [
            {"name": "mock_recall_drill", "frequency": "quarterly",
             "messages": [
                 "mock recall drill today: tracing batch 2847 from raw material to finished goods in 2 hours",
                 "recall drill complete. full traceability achieved in 1 hr 45 min. target was 2 hours. passed",
                 "simulated contamination recall: identifying all affected SKUs and distribution points",
             ]},
            {"name": "hygiene_audit", "frequency": "monthly",
             "messages": [
                 "internal hygiene audit today. swab testing on all contact surfaces. results in 48 hours",
                 "GMP training refresher: personal hygiene, hand washing technique, gowning procedure",
                 "pest control verification walk: checking all bait stations and fly catchers",
             ]},
            {"name": "fire_drill", "frequency": "quarterly",
             "messages": [
                 "fire drill at 2pm. production lines will stop for 15 minutes",
                 "fire evacuation drill complete. all 85 workers at assembly point in 4 min 20 sec",
             ]},
        ],
    },
    
    # IT/Software: Incident response and failover
    "it_digital": {
        "drills": [
            {"name": "incident_response_drill", "frequency": "quarterly",
             "messages": [
                 "tabletop exercise today: simulated data breach scenario. all leads join at 2pm",
                 "incident response drill: practiced runbook for database failover. RTO achieved: 12 min",
                 "quarterly disaster recovery test: failing over to DR site. monitoring latency and data consistency",
             ]},
            {"name": "failover_test", "frequency": "monthly",
             "messages": [
                 "monthly failover test tonight at 2am. primary → secondary switchover for 15 min",
                 "DR drill complete. all services recovered within RTO. one hiccup on cache warming",
                 "backup restore test: recovered last night's snapshot in 22 minutes. meets SLA",
             ]},
            {"name": "security_training", "frequency": "quarterly",
             "messages": [
                 "mandatory security awareness training due this week. phishing simulation coming",
                 "penetration test results shared. 3 findings: 1 critical, 2 medium. patching today",
                 "all-hands: security team presenting lessons from last quarter's incidents",
             ]},
        ],
    },
    
    # Retail/Hospitality: Fire + emergency drills
    "retail_hospitality": {
        "drills": [
            {"name": "fire_drill", "frequency": "quarterly",
             "messages": [
                 "fire drill at 9am before store opening. staff practice evacuation and customer guidance",
                 "fire evacuation drill complete. PA system worked. emergency exits confirmed clear",
             ]},
            {"name": "first_aid_training", "frequency": "biannual",
             "messages": [
                 "first aid training for floor staff: choking response, CPR basics, AED use",
                 "emergency response training: what to do if customer collapses. call sequence practiced",
             ]},
            {"name": "robbery_drill", "frequency": "annual",
             "messages": [
                 "security briefing: reviewed robbery response protocol. do NOT resist. hit silent alarm",
                 "cash handling security training: safe procedures, time-lock awareness, camera positions",
             ]},
        ],
    },
    
    # Agriculture: Minimal formal drills but safety awareness
    "agriculture": {
        "drills": [
            {"name": "pesticide_safety_training", "frequency": "seasonal",
             "messages": [
                 "agricultural extension officer visit: demonstrating safe pesticide handling and PPE use",
                 "seasonal training: proper mixing of chemicals. dilution ratios and wind direction checking",
                 "first aid training: snakebite response, heat stroke management for field workers",
             ]},
            {"name": "equipment_training", "frequency": "annual",
             "messages": [
                 "tractor operation safety training for new drivers. rollover prevention and PTO safety",
                 "harvest machinery orientation: combine harvester safety zones and emergency stop locations",
             ]},
        ],
    },
    
    # Logistics/Warehouse: Forklift safety dominant
    "logistics": {
        "drills": [
            {"name": "fire_drill", "frequency": "quarterly",
             "messages": [
                 "fire evacuation drill today. warehouse team practice exit routes. sprinkler zone awareness",
                 "fire drill complete. noted: exit 3 was blocked by pallets. cleared immediately",
             ]},
            {"name": "forklift_safety", "frequency": "monthly",
             "messages": [
                 "forklift operator refresher training: pedestrian awareness, load stability, horn use at intersections",
                 "new forklift drivers: practical assessment today. must pass before solo operation",
                 "safety topic: racking inspection awareness. damaged uprights report procedure",
             ]},
            {"name": "emergency_training", "frequency": "quarterly",
             "messages": [
                 "spill response training: chemical drums handling and containment procedure",
                 "emergency first aid refresher: crush injuries, forklift incidents, chemical exposure",
             ]},
        ],
    },
}

# Map subsectors to drill profile
SUBSECTOR_DRILL_MAP = {
    "mining": "mining", "coal": "mining", "quarrying": "mining",
    "oil_gas": "oil_gas", "petrochemical": "oil_gas", "gas": "oil_gas", "oil": "oil_gas",
    "civil": "construction", "construction": "construction", "building_material": "construction",
    "healthcare": "healthcare", "medical": "healthcare", "wellness": "healthcare",
    "chemical": "chemical", "pharmaceutical": "chemical", "biotech": "chemical",
    "food_processing": "food_processing", "food_beverage": "food_processing",
    "software": "it_digital", "it_services": "it_digital", "ai_data": "it_digital",
    "telecom": "it_digital", "media": "it_digital",
    "retail": "retail_hospitality", "hospitality": "retail_hospitality",
    "entertainment": "retail_hospitality", "tourism": "retail_hospitality",
    "agriculture": "agriculture", "horticulture": "agriculture",
    "livestock": "agriculture", "fisheries": "agriculture",
    "logistics": "logistics", "storage": "logistics", "shipping": "logistics",
    # Heavy industry uses chemical drills (similar hazards)
    "metallurgy": "chemical", "cement": "chemical", "energy": "oil_gas",
    "power_generation": "oil_gas", "renewable": "it_digital",
    "textile": "food_processing", "electrical": "food_processing",
    "precision": "food_processing", "advanced_materials": "chemical",
    "space": "chemical", "aerospace": "chemical",
}

# Frequency to probability per event (approximate)
# Based on: 1000 events ≈ 5 working days for a 24/7 plant
FREQUENCY_TO_PROB = {
    "every_shift": 0.01,     # ~10 per 1000 events (3 shifts × 5 days ≈ 15)
    "daily": 0.005,          # ~5 per 1000 events
    "weekly": 0.0015,        # ~1.5 per 1000 events
    "monthly": 0.0003,       # ~0.3 per 1000 events
    "quarterly": 0.0001,     # ~0.1 per 1000 events
    "biannual": 0.00005,     # very rare
    "annual": 0.00002,       # almost never in short runs
    "seasonal": 0.0002,      # ~0.2 per 1000 events
}


def should_inject_drill(subsector: str, rng: random.Random) -> Optional[str]:
    """Check if a drill/training event should be injected now.
    
    Returns a drill message string if one should be injected, None otherwise.
    Called once per event generation cycle.
    """
    profile_key = SUBSECTOR_DRILL_MAP.get(subsector)
    if not profile_key or profile_key not in DRILL_PROFILES:
        return None
    
    profile = DRILL_PROFILES[profile_key]
    
    for drill in profile["drills"]:
        prob = FREQUENCY_TO_PROB.get(drill["frequency"], 0.0001)
        if rng.random() < prob:
            return rng.choice(drill["messages"])
    
    return None
