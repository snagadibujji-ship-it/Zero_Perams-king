"""
Seasonal Patterns — Global Industry Calendar
==============================================
Industries worldwide have seasonal rhythms:
- India: Monsoon (Jun-Sep), Diwali shutdown (Oct-Nov), Kharif/Rabi crops
- Europe: August shutdown (Italy/France), Christmas closure (Dec 23-Jan 2)
- China: CNY shutdown (Jan-Feb, 2-4 weeks), factory sprint before shutdown
- Japan: Golden Week (Apr-May), Obon (Aug), New Year
- Middle East: Ramadan reduced hours, summer heat restrictions (Jun-Aug, 45°C+)
- USA: Thanksgiving-Christmas slowdown, summer construction peak
- Brazil: Carnaval (Feb), winter slowdown (Jun-Jul)

Sources:
- Stellantis Italy: 3-week August shutdown standard for auto plants
- China CNY: factories close 2-4 weeks, workers don't return for a month
- India sugar: crushing season Oct-Mar only (553 mills)
- India construction: monsoon stops outdoor work Jun-Sep
- Gulf states: outdoor work banned 12:30-3pm in summer (48°C+)
- Europe heatwave 2026: AC demand surge 70%+ from China
"""
import random
from typing import Optional, Dict, List


# ═══════════════════════════════════════════════════════════════════
# SEASONAL PROFILES — Month activity multipliers by region + industry
# [Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec]
# 1.0 = normal, 0.0 = completely shut, 2.0 = peak rush
# ═══════════════════════════════════════════════════════════════════

SEASONAL_PROFILES: Dict[str, List[float]] = {
    # === AGRICULTURE (by crop type) ===
    # India rice (Kharif): sow Jun-Jul, grow Jul-Sep, harvest Oct-Nov
    "rice_kharif": [0.3, 0.3, 0.5, 0.5, 0.8, 1.5, 2.0, 1.8, 1.5, 1.8, 1.0, 0.3],
    # India wheat (Rabi): sow Oct-Nov, grow Dec-Feb, harvest Mar-Apr
    "wheat_rabi": [1.2, 1.3, 1.8, 1.5, 0.3, 0.2, 0.2, 0.3, 0.5, 1.0, 1.2, 1.0],
    # India sugarcane: crushing Oct-Mar, plant shut Apr-Sep
    "sugar_crushing": [1.5, 1.5, 1.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.5, 1.8],
    # Tropical fruit/horticulture: peaks in summer
    "horticulture_tropical": [0.8, 0.9, 1.2, 1.5, 1.8, 1.5, 1.0, 0.8, 0.8, 0.9, 0.8, 0.7],
    # Fishing (India): monsoon trawling ban Jun-Aug
    "fishing_india": [1.2, 1.3, 1.2, 1.0, 0.8, 0.2, 0.1, 0.2, 0.8, 1.2, 1.3, 1.3],
    
    # === CONSTRUCTION ===
    # India/SE Asia: monsoon halts outdoor work
    "construction_monsoon": [1.3, 1.3, 1.3, 1.2, 1.0, 0.5, 0.3, 0.3, 0.5, 1.0, 1.2, 1.2],
    # Gulf/Middle East: summer heat stops outdoor work midday
    "construction_gulf": [1.3, 1.3, 1.3, 1.2, 0.8, 0.5, 0.4, 0.4, 0.6, 1.0, 1.3, 1.3],
    # USA/Europe: winter slowdown for outdoor
    "construction_cold": [0.5, 0.5, 0.8, 1.0, 1.3, 1.5, 1.5, 1.5, 1.3, 1.0, 0.7, 0.4],
    
    # === MANUFACTURING (by region) ===
    # Europe auto: August shutdown (3-4 weeks), Christmas (1 week)
    "manufacturing_europe": [0.9, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.2, 1.0, 1.0, 1.0, 0.7],
    # China: CNY shutdown (late Jan-mid Feb), pre-CNY rush in Dec
    "manufacturing_china": [0.3, 0.4, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.2, 1.3, 1.5],
    # Japan: Golden Week (late Apr-early May), Obon (mid Aug), New Year
    "manufacturing_japan": [0.7, 1.0, 1.0, 0.8, 0.8, 1.0, 1.0, 0.7, 1.0, 1.0, 1.0, 0.8],
    # India manufacturing: Diwali shutdown (Oct/Nov, 5-7 days)
    "manufacturing_india": [1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.9, 1.0, 1.0, 0.8, 0.9, 1.0],
    
    # === RETAIL & SERVICES ===
    # India retail: Diwali/Navratri peak (Oct-Nov), wedding season (Nov-Feb)
    "retail_india": [1.2, 1.3, 0.9, 0.8, 0.8, 0.7, 0.7, 0.8, 0.9, 1.5, 2.0, 1.5],
    # USA retail: Black Friday through Christmas
    "retail_usa": [0.7, 0.7, 0.8, 0.8, 0.9, 0.9, 0.9, 1.0, 1.0, 1.2, 1.8, 2.0],
    # Gulf retail: Ramadan shopping + Eid (varies, ~30 days)
    "retail_gulf": [1.0, 1.0, 1.5, 1.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
    
    # === TOURISM & HOSPITALITY ===
    # India tourism: winter peak (Oct-Feb), monsoon low
    "tourism_india": [1.5, 1.3, 1.0, 0.7, 0.6, 0.4, 0.3, 0.4, 0.6, 1.2, 1.5, 1.8],
    # Europe tourism: summer peak
    "tourism_europe": [0.5, 0.5, 0.7, 0.9, 1.2, 1.5, 1.8, 2.0, 1.5, 1.0, 0.6, 0.7],
    # Gulf tourism: winter peak (Nov-Mar), summer dead
    "tourism_gulf": [1.5, 1.5, 1.3, 1.0, 0.6, 0.3, 0.2, 0.3, 0.5, 1.0, 1.3, 1.5],
    
    # === ENERGY & UTILITIES ===
    # Power demand: summer peak (AC), winter peak (heating)
    "power_demand": [1.3, 1.1, 1.0, 1.0, 1.3, 1.5, 1.8, 1.8, 1.3, 1.0, 1.0, 1.3],
    # Solar farm: summer peak generation
    "solar_generation": [0.6, 0.7, 1.0, 1.2, 1.5, 1.8, 1.8, 1.6, 1.3, 1.0, 0.7, 0.5],
    
    # === FOOD & BEVERAGE ===
    # Ice cream/beverages: summer surge
    "summer_products": [0.5, 0.7, 1.2, 1.8, 2.0, 1.8, 1.5, 1.3, 1.0, 0.7, 0.5, 0.4],
    # Hot beverages/soups: winter surge
    "winter_products": [1.8, 1.5, 1.0, 0.7, 0.4, 0.3, 0.3, 0.4, 0.7, 1.2, 1.5, 1.8],
    
    # === TEXTILES & GARMENTS ===
    # Pre-festival rush (India): Aug-Nov for Diwali/Christmas orders
    "textile_india": [0.8, 0.7, 0.7, 0.8, 0.8, 0.9, 1.0, 1.3, 1.5, 1.5, 1.3, 1.0],
    # Fashion industry (global): pre-season production 3 months ahead
    "fashion_global": [1.2, 1.0, 1.0, 1.2, 1.0, 1.0, 1.2, 1.0, 1.0, 1.2, 1.0, 0.8],
    
    # === CONTINUOUS (24/7 never stops) ===
    "continuous": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
    
    # === AC/COOLING SERVICES ===
    "cooling_services": [0.4, 0.5, 1.2, 1.8, 2.0, 2.0, 1.5, 1.3, 1.0, 0.6, 0.4, 0.3],
    
    # === EDUCATION ===
    "education": [1.0, 1.0, 1.0, 0.3, 0.3, 0.8, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5],
}


# ═══════════════════════════════════════════════════════════════════
# INDUSTRY → SEASONAL PROFILE MAPPING
# ═══════════════════════════════════════════════════════════════════

INDUSTRY_SEASON_MAP: Dict[str, str] = {
    # Agriculture
    "rice_farming": "rice_kharif", "rice_milling": "rice_kharif",
    "wheat_farming": "wheat_rabi",
    "sugar_milling": "sugar_crushing", "sugarcane_farming": "sugar_crushing",
    "banana_farming": "horticulture_tropical", "mango_farming": "horticulture_tropical",
    "aloe_vera_farming": "horticulture_tropical",
    "shrimp_farming": "fishing_india",
    
    # Construction
    "road_construction": "construction_monsoon",
    "building_construction": "construction_monsoon",
    "bridge_construction": "construction_monsoon",
    "airport_construction": "construction_monsoon",
    
    # Manufacturing (use country from registry at runtime)
    "automobile_assembly": "manufacturing_europe",
    "semiconductor_fab": "manufacturing_japan",
    
    # Retail
    "supermarket_retail": "retail_india",
    
    # Tourism
    "hotel_resort": "tourism_india", "hotel_operations": "tourism_india",
    
    # Energy
    "thermal_power_plant": "power_demand",
    "solar_farm": "solar_generation",
    
    # Food
    "ice_cream_plant": "summer_products",
    
    # Textiles
    "cotton_spinning": "textile_india", "garment_factory": "textile_india",
    "denim_mill": "textile_india",
    
    # Education
    "coaching_center": "education",
    
    # Continuous (never stops)
    "oil_refining": "continuous", "steel_rolling": "continuous",
    "hospital": "continuous", "data_center": "continuous",
    "coal_mining": "continuous", "cement_manufacturing": "continuous",
    "software_company": "continuous", "ai_research_lab": "continuous",
    "call_center": "continuous",
}

# Subsector-level fallbacks — COVERS ALL 500 INDUSTRIES
SUBSECTOR_SEASON_MAP: Dict[str, str] = {
    # Agriculture & primary (weather dependent)
    "agriculture": "rice_kharif",
    "horticulture": "horticulture_tropical",
    "fisheries": "fishing_india",
    "livestock": "rice_kharif",
    "forestry": "construction_monsoon",
    
    # Construction & outdoor (weather stops work)
    "civil": "construction_monsoon",
    "construction": "construction_monsoon",
    "building_material": "construction_monsoon",
    "quarrying": "construction_monsoon",
    "stone": "construction_monsoon",
    "environmental": "construction_monsoon",
    "wood": "construction_monsoon",
    
    # Heavy process (continuous 24/7, never stops)
    "mining": "continuous",
    "oil_gas": "continuous",
    "oil": "continuous",
    "gas": "continuous",
    "coal": "continuous",
    "petrochemical": "continuous",
    "metallurgy": "continuous",
    "cement": "continuous",
    "chemical": "continuous",
    "heavy_engineering": "continuous",
    "mechanical": "continuous",
    "paper_pulp": "continuous",
    "waste": "continuous",
    "recycling": "continuous",
    "maintenance": "continuous",
    "defense": "continuous",
    
    # Power & energy
    "power_generation": "power_demand",
    "energy": "power_demand",
    "renewable": "solar_generation",
    "utility": "power_demand",
    "water": "continuous",
    
    # IT / Knowledge / Finance (no seasonal pattern)
    "software": "continuous",
    "it_services": "continuous",
    "ai_data": "continuous",
    "telecom": "continuous",
    "robotics": "continuous",
    "space": "continuous",
    "aerospace": "continuous",
    "banking": "continuous",
    "finance": "continuous",
    "insurance": "continuous",
    "consulting": "continuous",
    "safety": "continuous",
    "media": "continuous",
    
    # Healthcare (never stops)
    "healthcare": "continuous",
    "medical": "continuous",
    "medical_tech": "continuous",
    "biotech": "continuous",
    "pharmaceutical": "continuous",
    "wellness": "continuous",
    "personal_care": "continuous",
    
    # Manufacturing (mild seasonal — Diwali/maintenance shutdowns)
    "food_processing": "continuous",
    "food_beverage": "summer_products",
    "textile": "textile_india",
    "textile_garment": "textile_india",
    "leather": "textile_india",
    "footwear": "textile_india",
    "fmcg": "retail_india",
    "electrical": "manufacturing_india",
    "electronics": "manufacturing_india",
    "precision": "manufacturing_india",
    "advanced_materials": "manufacturing_india",
    "machinery": "manufacturing_india",
    "automobile": "manufacturing_europe",
    "appliance": "manufacturing_india",
    "rubber": "manufacturing_india",
    "plastic": "manufacturing_india",
    "printing": "retail_india",
    "furniture": "retail_india",
    "tobacco": "continuous",
    "manufacturing": "manufacturing_india",
    
    # Retail & services (festival/holiday peaks)
    "retail": "retail_india",
    "hospitality": "tourism_india",
    "tourism": "tourism_india",
    "entertainment": "tourism_europe",
    "services": "retail_india",
    "facility_management": "continuous",
    "storage": "continuous",
    "shipping": "continuous",
    "logistics": "continuous",
    "security": "continuous",
    "education": "education",
    
    # Misc (default to mild retail seasonal pattern)
    "misc": "retail_india",
}


# ═══════════════════════════════════════════════════════════════════
# SEASONAL EVENT MESSAGES — By region and situation
# ═══════════════════════════════════════════════════════════════════

SEASONAL_MESSAGES = {
    "peak_season": [
        "peak season rush. everyone doing overtime this month",
        "demand is at yearly high. running at max capacity",
        "seasonal peak — no leave approved until next month. sorry team",
        "working double shifts. seasonal orders flooding in",
        "this is our busiest time of year. let's push through it",
        "order book is full for next 6 weeks. production planning meeting at 3",
    ],
    "off_season": [
        "off season. skeleton crew only. most workers on seasonal leave",
        "plant shut for annual maintenance. only engineering team here",
        "slow period — using downtime for equipment overhaul",
        "production stopped for the season. stock sufficient till restart",
        "off season training week. everyone attending upskilling program",
        "maintenance window while plant is down. accessing everything we normally can't",
    ],
    "monsoon_impact": [
        "heavy rain since morning. outdoor work suspended for safety",
        "waterlogging on site access road. half the team couldn't make it",
        "monsoon alert — covering all outdoor materials with tarpaulin",
        "rain stopped work at 11am. standing water everywhere. pumps running",
        "road to site flooded. asking workers to stay home today. safety first",
        "lightning warning. all crane operations suspended until clear",
    ],
    "heat_restriction": [
        "outdoor work banned 12:30-3pm today. temperature at 47°C",
        "heat advisory in effect. extra water stations set up. mandatory shade breaks",
        "summer heat unbearable. AC struggling to keep indoor temp below 32°C",
        "3 workers showing heat exhaustion symptoms. sent to rest area. hydrating",
        "shifting heavy outdoor work to 5am-11am only this month",
    ],
    "cold_shutdown": [
        "below freezing today. pipes at risk. heat tracing verified",
        "snow on access road. gritters deployed at 4am. slight delay for morning shift",
        "winter shutdown begins next week. draining all outdoor water lines",
        "heating system running full. fuel consumption up 40% this month",
    ],
    "harvest_rush": [
        "harvest season started. need all available hands in the field",
        "cutting begun since sunrise. working till dark. no breaks today",
        "rush to complete harvest before predicted rainfall on Thursday",
        "trucks lined up at farm gate. loading and dispatching to mandi continuously",
        "yield looking good this season. spirits high among workers",
    ],
    "festival_shutdown": [
        "plant shutting for Diwali. maintenance team staying for annual PM work",
        "CNY shutdown begins. all workers returning to hometowns tonight",
        "Eid holiday — reduced operations. only essential staff reporting",
        "Christmas-New Year closure. skeleton crew for emergencies only",
        "Golden Week holiday. plant idle. security on site only",
        "Songkran holiday. factory closed Apr 13-15. back on the 16th",
    ],
    "pre_shutdown_rush": [
        "rushing to finish orders before holiday shutdown. overtime all week",
        "final dispatches going out today. warehouse working till midnight",
        "complete all pending work by EOD. plant closes tomorrow for seasonal break",
        "double checking everything before we shut down. no one wants a call during holiday",
    ],
    "europe_august": [
        "Ferragosto shutdown begins. see you all in September",
        "August vacation — factory closed for 3 weeks. annual maintenance during shutdown",
        "summer break. line stopped. tooling overhaul and floor painting happening this month",
        "Italian suppliers all closed in August. we're running on buffer stock",
    ],
    "china_cny": [
        "factory closing for Spring Festival. workers getting train tickets home",
        "pre-CNY rush: finishing all pending orders. shipping cutoff is Friday",
        "CNY countdown: 3 days left. final QC checks on all packed goods",
        "post-CNY: only 60% of workers returned so far. running at reduced capacity",
        "still waiting for workers to come back after Chinese New Year. production at 40%",
    ],
    "japan_holiday": [
        "Golden Week starts tomorrow. plant stops for 5 days. enjoy the break everyone",
        "Obon holiday schedule posted. skeleton crew Aug 13-16. volunteers get extra pay",
        "new year shutdown Dec 28 - Jan 3. all equipment winterized and locked out",
        "post-Golden Week restart: all machines need warm-up and quality verification before production",
    ],
    "ramadan": [
        "Ramadan schedule starts today. working hours reduced to 6hrs. no eating on floor",
        "iftar break at 6:30pm. all outdoor work stops 30 minutes before",
        "reduced hours during Ramadan but production targets adjusted accordingly",
        "Eid holiday confirmed for 3 days. skeleton staff for essential operations only",
        "many workers fasting. extra water stations removed from production floor. rest area available",
    ],
    "brazil_seasonal": [
        "Carnaval week — factory on minimum staff Tuesday-Wednesday. back to normal Thursday",
        "winter months (Jun-Jul) — demand slower. using time for line improvements",
        "safra (harvest season) starting. trucks arriving constantly. receiving at full capacity",
        "end of year festas approaching. overtime to clear backlog before December shutdown",
    ],
    # Industry-specific seasonal messages
    "sugar_season": [
        "crushing season started! first batch of cane arriving from farms. mills fired up",
        "sugar recovery rate today: 10.2%. good for early season. will improve as cane matures",
        "36 trucks of cane in queue. crushing 24/7. no stopping till March",
        "crushing ending in 2 weeks. last batches being processed. season total looking good",
        "off-season started. boiler tubes and mill rollers going for annual overhaul",
        "plant completely shut. only maintenance crew working. major repairs underway",
    ],
    "fishing_season": [
        "monsoon trawling ban in effect. boats anchored at harbor. net mending time",
        "ban period — using time to repair hull, repaint boat, service engine",
        "fishing ban lifted today! all boats heading out at 4am tomorrow. excited",
        "peak catch season. boats returning fully loaded. market prices good",
        "rough seas advisory — smaller boats staying in port today. only deep-sea trawlers going",
    ],
    "construction_rain": [
        "site flooded from overnight rain. pumping out standing water before work starts",
        "concrete pour cancelled today — rain predicted after 2pm. can't risk quality",
        "monsoon break — using indoor time for fabrication, cutting, and welding in shed",
        "3 weeks without rain! making up for lost time. pouring every day now",
        "waterproofing work on hold till dry spell. membrane can't be applied in humidity >80%",
    ],
    "textile_festival": [
        "festival orders flooding in. running 3 shifts to meet Diwali delivery deadlines",
        "wedding season approaching — bridal fabric production at 150% capacity",
        "export orders for Christmas must ship by Oct 15. no exceptions. overtime approved",
        "slow season after festivals. maintenance and machinery upgrades happening now",
    ],
    "power_summer": [
        "summer peak load. running all units at full capacity. grid demand at 180GW today",
        "AC demand pushing evening peak. load dispatch asking us to maximize generation",
        "coal consumption up 30% vs winter. ensuring daily rakes arrive on schedule",
        "monsoon helping — hydro generation picking up. thermal units can breathe a little",
    ],
    "retail_festival": [
        "Diwali rush starting. extended store hours 9am-11pm this week",
        "stock position: most festival items selling fast. reorders placed for top 50 SKUs",
        "Christmas decoration aisle fully stocked. promotional display up since Monday",
        "post-festival clearance sale. 40% off on remaining seasonal stock",
        "wedding season: jewelry and gift counters extremely busy. extra staff deployed",
    ],
    "tourism_peak": [
        "full occupancy tonight. not a single room available. turning away walk-ins",
        "peak season — restaurant serving 300+ covers daily. kitchen exhausted but motivated",
        "holiday season: adventure activities fully booked 2 weeks in advance",
        "off-season started. time for renovations and deep maintenance of all rooms",
        "monsoon getaway packages launched. surprisingly good bookings for rainy season",
    ],
}


# ═══════════════════════════════════════════════════════════════════
# LOOKUP FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_seasonal_modifier(industry_id: str, subsector: str, month: int) -> float:
    """Get production intensity for this industry in this month (0.0-2.0)."""
    # Direct industry match first
    profile_key = INDUSTRY_SEASON_MAP.get(industry_id)
    if not profile_key:
        # Subsector fallback
        profile_key = SUBSECTOR_SEASON_MAP.get(subsector, "continuous")
    
    profile = SEASONAL_PROFILES.get(profile_key, SEASONAL_PROFILES["continuous"])
    return profile[month - 1]


def get_seasonal_message(industry_id: str, month: int, rng: random.Random,
                         country: str = "IN", subsector: str = "") -> Optional[str]:
    """Get a seasonal context message if season significantly affects operations.
    
    Uses industry-specific messages when available, falls back to generic.
    Only fires ~3% of the time when at seasonal extremes.
    """
    modifier = get_seasonal_modifier(industry_id, subsector, month)
    
    # Peak season (modifier >= 1.8)
    if modifier >= 1.8 and rng.random() < 0.03:
        # Industry-specific peak messages
        if industry_id in ("sugar_milling", "sugarcane_farming"):
            return rng.choice(SEASONAL_MESSAGES["sugar_season"])
        elif subsector in ("agriculture", "horticulture"):
            return rng.choice(SEASONAL_MESSAGES["harvest_rush"])
        elif subsector in ("retail",):
            return rng.choice(SEASONAL_MESSAGES["retail_festival"])
        elif subsector in ("hospitality", "tourism"):
            return rng.choice(SEASONAL_MESSAGES["tourism_peak"])
        elif subsector in ("textile", "textile_garment", "leather", "footwear"):
            return rng.choice(SEASONAL_MESSAGES["textile_festival"])
        elif subsector in ("power_generation", "energy", "utility"):
            return rng.choice(SEASONAL_MESSAGES["power_summer"])
        return rng.choice(SEASONAL_MESSAGES["peak_season"])
    
    # Off season / shutdown (modifier <= 0.3)
    elif modifier <= 0.3 and rng.random() < 0.03:
        # Region + industry specific shutdown messages
        if country in ("IT", "FR", "DE", "ES") and month == 8:
            return rng.choice(SEASONAL_MESSAGES["europe_august"])
        elif country in ("CN", "TW") and month in (1, 2):
            return rng.choice(SEASONAL_MESSAGES["china_cny"])
        elif country in ("JP",) and month in (4, 5):
            return rng.choice(SEASONAL_MESSAGES["japan_holiday"])
        elif country in ("JP",) and month == 8:
            return rng.choice(SEASONAL_MESSAGES["japan_holiday"])
        elif month in (10, 11) and country == "IN":
            return rng.choice(SEASONAL_MESSAGES["festival_shutdown"])
        elif country in ("BR", "AR") and month == 2:
            return rng.choice(SEASONAL_MESSAGES["brazil_seasonal"])
        elif subsector in ("fisheries",):
            return rng.choice(SEASONAL_MESSAGES["fishing_season"])
        elif industry_id in ("sugar_milling",):
            return rng.choice(SEASONAL_MESSAGES["sugar_season"])
        return rng.choice(SEASONAL_MESSAGES["off_season"])
    
    # Monsoon months (Jun-Sep) in relevant countries
    elif month in (6, 7, 8, 9) and modifier <= 0.5 and rng.random() < 0.02:
        if country in ("IN", "TH", "VN", "ID", "PH", "BD", "MM", "NP"):
            if subsector in ("civil", "construction"):
                return rng.choice(SEASONAL_MESSAGES["construction_rain"])
            return rng.choice(SEASONAL_MESSAGES["monsoon_impact"])
    
    # Summer heat (May-Aug) in Gulf/hot regions
    elif month in (5, 6, 7, 8) and country in ("SA", "AE", "QA", "KW", "OM", "IQ", "BH"):
        if rng.random() < 0.02:
            return rng.choice(SEASONAL_MESSAGES["heat_restriction"])
    
    # Ramadan (approximate — varies yearly, ~30 days)
    # Using fixed months for simulation (Mar-Apr as common Ramadan period)
    elif month in (3, 4) and country in ("SA", "AE", "QA", "KW", "OM", "EG", "MY", "ID", "PK"):
        if rng.random() < 0.02:
            return rng.choice(SEASONAL_MESSAGES["ramadan"])
    
    # Cold weather (Dec-Feb) in cold regions
    elif month in (12, 1, 2) and country in ("NO", "SE", "FI", "RU", "CA", "IS"):
        if modifier < 0.7 and rng.random() < 0.02:
            return rng.choice(SEASONAL_MESSAGES["cold_shutdown"])
    
    # Pre-shutdown rush (producing extra before a known shutdown)
    elif modifier >= 1.3:
        next_month = (month % 12) + 1
        profile_key = INDUSTRY_SEASON_MAP.get(industry_id, SUBSECTOR_SEASON_MAP.get(subsector, "continuous"))
        profile = SEASONAL_PROFILES.get(profile_key, SEASONAL_PROFILES["continuous"])
        next_modifier = profile[next_month - 1]
        if next_modifier <= 0.3 and rng.random() < 0.02:
            return rng.choice(SEASONAL_MESSAGES["pre_shutdown_rush"])
    
    return None
