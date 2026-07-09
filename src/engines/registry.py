"""
Industry Registry — 500+ industries across 9 sectors.
Each industry has: fictional company name, era, assets, roles, events.
NO real company names used — all fictional to avoid legal issues.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


@dataclass
class IndustryConfig:
    """Configuration for one industry type."""
    id: str                    # "oil_refining", "textile_spinning"
    sector: str                # "A_primary", "B_processing", etc.
    subsector: str             # "mining", "food_processing", etc.
    label: str                 # Human-readable name
    birth_year: int            # When this industry first existed
    peak_era: str              # When it was most prominent
    scale_range: Tuple[str, str]  # ("small", "global")
    typical_assets: List[str]  # Asset types used
    typical_roles: List[str]   # Job roles in this industry
    typical_products: List[str]  # What it produces
    hazards: List[str]         # Industry-specific risks
    raw_materials: List[str]   # What it consumes
    key_processes: List[str]   # Core operations
    fictional_companies: List[str]  # 3-5 fictional company names
    countries: List[str]       # Where this industry is common



# ============================================================
# SECTOR A: PRIMARY INDUSTRIES (extract/grow raw materials)
# ============================================================

INDUSTRIES: Dict[str, IndustryConfig] = {}

def _reg(cfg: IndustryConfig):
    INDUSTRIES[cfg.id] = cfg

# --- Agriculture ---
_reg(IndustryConfig(
    id="rice_farming", sector="A_primary", subsector="agriculture",
    label="Rice Farming & Paddy Cultivation",
    birth_year=1700, peak_era="mass_production",
    scale_range=("cottage", "large"),
    typical_assets=["tractor", "harvester", "irrigation_pump", "grain_dryer", "thresher", "storage_silo"],
    typical_roles=["farmer", "field_worker", "tractor_driver", "irrigation_operator", "supervisor", "agronomist"],
    typical_products=["paddy_rice", "rice_bran", "husk", "straw"],
    hazards=["heat_stroke", "snake_bite", "pesticide_exposure", "machinery_entanglement"],
    raw_materials=["seed", "water", "fertilizer", "pesticide", "diesel"],
    key_processes=["plowing", "sowing", "transplanting", "irrigation", "harvesting", "drying", "milling"],
    fictional_companies=["Kaveri Agri Works", "Golden Grain Cultivators", "Padmavathi Farms"],
    countries=["IN", "TH", "VN", "CN", "BD", "MM", "PH", "ID"],
))


_reg(IndustryConfig(
    id="wheat_farming", sector="A_primary", subsector="agriculture",
    label="Wheat & Grain Cultivation",
    birth_year=1700, peak_era="mass_production",
    scale_range=("cottage", "global"),
    typical_assets=["combine_harvester", "seed_drill", "tractor", "grain_elevator", "irrigation_system"],
    typical_roles=["farmer", "harvester_operator", "grain_handler", "agronomist", "mechanic"],
    typical_products=["wheat", "flour", "bran", "chaff"],
    hazards=["grain_dust_explosion", "machinery_injury", "heat_exhaustion"],
    raw_materials=["seed", "fertilizer", "water", "diesel", "herbicide"],
    key_processes=["tilling", "seeding", "spraying", "harvesting", "storage", "transport"],
    fictional_companies=["Punjab Golden Fields", "Heartland Harvest Co", "Nile Valley Grains"],
    countries=["IN", "US", "RU", "AU", "CA", "UA", "FR", "AR"],
))

_reg(IndustryConfig(
    id="sugarcane_farming", sector="A_primary", subsector="agriculture",
    label="Sugarcane Plantation & Harvesting",
    birth_year=1700, peak_era="second_industrial",
    scale_range=("small", "large"),
    typical_assets=["cane_harvester", "tractor_trailer", "irrigation_canal", "weighbridge"],
    typical_roles=["cane_cutter", "tractor_driver", "field_supervisor", "weighbridge_operator"],
    typical_products=["sugarcane", "bagasse", "molasses"],
    hazards=["cuts_from_machete", "snake_bite", "dehydration", "fire_in_field"],
    raw_materials=["seed_cane", "fertilizer", "water"],
    key_processes=["planting", "ratoon_management", "irrigation", "cutting", "transport_to_mill"],
    fictional_companies=["Deccan Cane Growers", "Tropical Sugar Estates", "Rio Verde Plantations"],
    countries=["IN", "BR", "TH", "AU", "CU", "PH", "MX"],
))


_reg(IndustryConfig(
    id="poultry_farming", sector="A_primary", subsector="livestock",
    label="Poultry Farm & Hatchery",
    birth_year=1850, peak_era="automation",
    scale_range=("cottage", "global"),
    typical_assets=["incubator", "feed_mixer", "water_system", "egg_collector", "ventilation_fan", "generator"],
    typical_roles=["farm_owner", "poultry_attendant", "veterinarian", "feed_mixer_operator", "egg_grader"],
    typical_products=["eggs", "broiler_chicken", "feathers", "manure"],
    hazards=["bird_flu", "ammonia_exposure", "electrical_fire", "disease_outbreak"],
    raw_materials=["feed_corn", "soybean_meal", "vitamins", "vaccines", "bedding_material"],
    key_processes=["breeding", "incubation", "brooding", "feeding", "vaccination", "collection", "processing"],
    fictional_companies=["Sunrise Poultry Farms", "Golden Egg Hatcheries", "Venkata Poultry"],
    countries=["IN", "US", "BR", "CN", "TH", "ID", "MX", "NG"],
))

_reg(IndustryConfig(
    id="dairy_farming", sector="A_primary", subsector="livestock",
    label="Dairy Farm & Milk Collection",
    birth_year=1700, peak_era="automation",
    scale_range=("cottage", "global"),
    typical_assets=["milking_machine", "bulk_cooler", "pasteurizer", "tanker_truck", "feed_silo"],
    typical_roles=["dairy_farmer", "milker", "veterinarian", "tanker_driver", "quality_tester"],
    typical_products=["raw_milk", "cream", "butter", "ghee", "curd"],
    hazards=["animal_kick", "mastitis_handling", "slippery_floor", "cold_exposure"],
    raw_materials=["cattle_feed", "hay", "silage", "water", "veterinary_medicine"],
    key_processes=["feeding", "milking", "cooling", "testing", "collection", "transport"],
    fictional_companies=["Godavari Dairy Collective", "Alpine Fresh Dairies", "Nandini Milk Union"],
    countries=["IN", "NZ", "US", "DE", "FR", "AU", "NL", "PK"],
))

_reg(IndustryConfig(
    id="shrimp_farming", sector="A_primary", subsector="fisheries",
    label="Shrimp Aquaculture & Hatchery",
    birth_year=1970, peak_era="digital",
    scale_range=("small", "large"),
    typical_assets=["aerator", "water_pump", "feed_dispenser", "water_quality_sensor", "harvest_net"],
    typical_roles=["pond_manager", "hatchery_technician", "feed_operator", "water_tester", "harvest_crew"],
    typical_products=["vannamei_shrimp", "tiger_prawn", "shrimp_feed"],
    hazards=["disease_outbreak", "water_quality_crash", "electrical_hazard", "drowning"],
    raw_materials=["shrimp_seed", "feed_pellets", "probiotics", "lime", "diesel"],
    key_processes=["pond_preparation", "stocking", "feeding", "water_management", "harvesting", "packing"],
    fictional_companies=["Coastal Aqua Ventures", "Bay of Bengal Shrimp", "Mekong Delta Aquaculture"],
    countries=["IN", "TH", "VN", "EC", "ID", "CN", "BD"],
))


_reg(IndustryConfig(
    id="coal_mining", sector="A_primary", subsector="mining",
    label="Coal Mining (Open Cast & Underground)",
    birth_year=1750, peak_era="second_industrial",
    scale_range=("medium", "global"),
    typical_assets=["excavator", "dumper_truck", "conveyor_belt", "crusher", "dragline", "ventilation_fan"],
    typical_roles=["miner", "blaster", "excavator_operator", "safety_officer", "geologist", "foreman"],
    typical_products=["thermal_coal", "coking_coal", "fly_ash"],
    hazards=["roof_collapse", "gas_explosion", "dust_inhalation", "flooding", "fire"],
    raw_materials=["explosives", "diesel", "timber_supports", "drill_bits"],
    key_processes=["drilling", "blasting", "loading", "hauling", "crushing", "washing", "transport"],
    fictional_companies=["Singareni Deep Works", "Black Diamond Collieries", "Kuznetsk Extractors"],
    countries=["IN", "CN", "AU", "US", "ID", "RU", "ZA", "PL"],
))

_reg(IndustryConfig(
    id="iron_ore_mining", sector="A_primary", subsector="mining",
    label="Iron Ore Mining & Beneficiation",
    birth_year=1800, peak_era="mass_production",
    scale_range=("medium", "global"),
    typical_assets=["drill_rig", "haul_truck", "ball_mill", "magnetic_separator", "thickener", "tailings_dam"],
    typical_roles=["drill_operator", "truck_driver", "plant_operator", "geologist", "environmental_officer"],
    typical_products=["iron_ore_fines", "iron_ore_lumps", "pellets", "concentrate"],
    hazards=["landslide", "dust_storm", "heavy_equipment_collision", "tailings_dam_failure"],
    raw_materials=["diesel", "explosives", "grinding_media", "water", "flocculant"],
    key_processes=["exploration", "drilling", "blasting", "hauling", "crushing", "grinding", "separation"],
    fictional_companies=["Bellary Iron Works", "Pilbara Red Earth", "Carajas Mineracao"],
    countries=["IN", "AU", "BR", "CN", "RU", "ZA", "UA"],
))

_reg(IndustryConfig(
    id="offshore_oil_drilling", sector="A_primary", subsector="oil_gas",
    label="Offshore Oil & Gas Drilling",
    birth_year=1900, peak_era="automation",
    scale_range=("large", "global"),
    typical_assets=["drilling_rig", "blowout_preventer", "mud_pump", "crane", "flare_stack", "helideck"],
    typical_roles=["driller", "roughneck", "mud_engineer", "tool_pusher", "safety_officer", "helicopter_pilot"],
    typical_products=["crude_oil", "natural_gas", "condensate"],
    hazards=["blowout", "h2s_gas", "fire_explosion", "man_overboard", "helicopter_crash"],
    raw_materials=["drilling_mud", "casing_pipe", "cement", "diesel", "chemicals"],
    key_processes=["spudding", "drilling", "casing", "cementing", "completion", "production", "flaring"],
    fictional_companies=["Krishna Basin Offshore", "Nordic Deepwater", "Gulf Horizon Drillers"],
    countries=["IN", "US", "NO", "BR", "AE", "NG", "GB", "MX"],
))


_reg(IndustryConfig(
    id="timber_logging", sector="A_primary", subsector="forestry",
    label="Timber Logging & Sawmill",
    birth_year=1700, peak_era="second_industrial",
    scale_range=("cottage", "large"),
    typical_assets=["chainsaw", "skidder", "log_truck", "sawmill_blade", "debarker", "kiln_dryer"],
    typical_roles=["logger", "chainsaw_operator", "truck_driver", "sawmill_worker", "forester"],
    typical_products=["timber_logs", "lumber", "plywood", "sawdust", "wood_chips"],
    hazards=["falling_tree", "chainsaw_injury", "log_roll", "machinery_entanglement"],
    raw_materials=["standing_timber", "diesel", "chain_oil", "saw_blades"],
    key_processes=["felling", "bucking", "skidding", "loading", "sawing", "drying", "grading"],
    fictional_companies=["Western Ghats Timber", "Boreal Forest Products", "Amazon Sustainable Woods"],
    countries=["IN", "CA", "BR", "RU", "SE", "FI", "ID", "MY"],
))

# ============================================================
# SECTOR B: PROCESSING INDUSTRIES
# ============================================================

_reg(IndustryConfig(
    id="rice_milling", sector="B_processing", subsector="food_processing",
    label="Rice Mill & Processing",
    birth_year=1800, peak_era="automation",
    scale_range=("cottage", "large"),
    typical_assets=["paddy_separator", "husker", "polisher", "grader", "packing_machine", "boiler"],
    typical_roles=["mill_owner", "machine_operator", "sorter", "packer", "quality_checker", "boiler_attendant"],
    typical_products=["white_rice", "brown_rice", "broken_rice", "rice_bran_oil", "husk_fuel"],
    hazards=["dust_explosion", "belt_entanglement", "boiler_burst", "hearing_damage"],
    raw_materials=["paddy_rice", "water", "steam", "packaging_material"],
    key_processes=["cleaning", "husking", "whitening", "polishing", "grading", "packing"],
    fictional_companies=["Eluru Rice Industries", "Delta Grain Processors", "Mekong Mills"],
    countries=["IN", "TH", "VN", "MM", "BD", "PH", "CN"],
))

_reg(IndustryConfig(
    id="sugar_milling", sector="B_processing", subsector="food_processing",
    label="Sugar Factory & Refinery",
    birth_year=1750, peak_era="mass_production",
    scale_range=("medium", "large"),
    typical_assets=["cane_crusher", "boiler", "evaporator", "centrifuge", "crystallizer", "turbine"],
    typical_roles=["crusher_operator", "boiler_engineer", "chemist", "centrifuge_operator", "packing_worker"],
    typical_products=["raw_sugar", "refined_sugar", "molasses", "bagasse", "ethanol"],
    hazards=["boiler_explosion", "hot_syrup_burn", "centrifuge_failure", "confined_space"],
    raw_materials=["sugarcane", "lime", "sulphur", "chemicals", "water"],
    key_processes=["crushing", "juice_extraction", "clarification", "evaporation", "crystallization", "drying"],
    fictional_companies=["Nizam Sugar Works", "Tropical Sweeteners", "Sao Paulo Acucar"],
    countries=["IN", "BR", "TH", "AU", "CU", "PK", "MX"],
))


_reg(IndustryConfig(
    id="cotton_spinning", sector="B_processing", subsector="textile",
    label="Cotton Spinning Mill",
    birth_year=1760, peak_era="second_industrial",
    scale_range=("small", "large"),
    typical_assets=["carding_machine", "draw_frame", "ring_frame", "winding_machine", "humidifier"],
    typical_roles=["spinner", "doffer", "fitter", "supervisor", "quality_inspector", "humidifier_operator"],
    typical_products=["cotton_yarn", "waste_cotton", "combed_sliver"],
    hazards=["cotton_dust_byssinosis", "machine_nip", "fire", "noise_damage"],
    raw_materials=["raw_cotton", "lubricants", "bobbins", "electricity"],
    key_processes=["blowroom", "carding", "drawing", "roving", "spinning", "winding", "packing"],
    fictional_companies=["Coimbatore Spinners", "Lancashire Cotton Works", "Dhaka Textile Mills"],
    countries=["IN", "BD", "CN", "PK", "TR", "EG", "VN"],
))

_reg(IndustryConfig(
    id="leather_tanning", sector="B_processing", subsector="leather",
    label="Leather Tannery & Processing",
    birth_year=1700, peak_era="second_industrial",
    scale_range=("cottage", "large"),
    typical_assets=["drum", "splitting_machine", "drying_rack", "shaving_machine", "effluent_plant"],
    typical_roles=["tanner", "drum_operator", "cutter", "finisher", "effluent_plant_operator", "grader"],
    typical_products=["finished_leather", "leather_offcuts", "gelatin", "fat_liquor"],
    hazards=["chemical_burns", "chromium_exposure", "slip_fall", "knife_injury"],
    raw_materials=["raw_hides", "chrome_salts", "vegetable_tannins", "dyes", "fat_liquors"],
    key_processes=["soaking", "liming", "tanning", "splitting", "shaving", "dyeing", "finishing"],
    fictional_companies=["Ambur Leather Works", "Kanpur Hide Processors", "Fez Tanneries"],
    countries=["IN", "IT", "BR", "PK", "BD", "MA", "ET"],
))

_reg(IndustryConfig(
    id="steel_rolling", sector="B_processing", subsector="metallurgy",
    label="Steel Rolling Mill & Casting",
    birth_year=1850, peak_era="mass_production",
    scale_range=("medium", "global"),
    typical_assets=["blast_furnace", "rolling_mill", "reheating_furnace", "crane", "cooling_bed", "shear"],
    typical_roles=["furnace_operator", "roller", "crane_operator", "quality_inspector", "maintenance_fitter"],
    typical_products=["tmt_bars", "steel_coils", "billets", "channels", "angles"],
    hazards=["molten_metal_splash", "radiation_heat", "crane_accident", "roll_breakage"],
    raw_materials=["iron_ore", "scrap_steel", "coke", "limestone", "ferroalloys"],
    key_processes=["melting", "casting", "reheating", "rolling", "cooling", "cutting", "bundling"],
    fictional_companies=["Visakha Steel Rolling", "Ural Metal Works", "Great Lakes Steelmakers"],
    countries=["IN", "CN", "JP", "US", "DE", "RU", "KR", "BR"],
))

_reg(IndustryConfig(
    id="cement_manufacturing", sector="B_processing", subsector="cement",
    label="Cement Plant & Grinding Unit",
    birth_year=1850, peak_era="mass_production",
    scale_range=("medium", "global"),
    typical_assets=["rotary_kiln", "ball_mill", "preheater_tower", "clinker_cooler", "bag_filter", "packer"],
    typical_roles=["kiln_operator", "mill_operator", "lab_chemist", "packer", "electrician", "safety_officer"],
    typical_products=["opc_cement", "ppc_cement", "clinker", "fly_ash_cement"],
    hazards=["kiln_fire", "dust_inhalation", "falling_from_height", "rotating_equipment"],
    raw_materials=["limestone", "clay", "gypsum", "coal", "fly_ash", "iron_ore"],
    key_processes=["quarrying", "crushing", "grinding", "preheating", "calcination", "clinker_cooling", "finish_grinding"],
    fictional_companies=["Nagarjuna Cements", "Atlas Portland Works", "Sahara Building Materials"],
    countries=["IN", "CN", "TR", "ID", "EG", "VN", "BR", "SA"],
))


_reg(IndustryConfig(
    id="oil_refining", sector="B_processing", subsector="petrochemical",
    label="Oil Refinery & Petroleum Processing",
    birth_year=1860, peak_era="mass_production",
    scale_range=("large", "global"),
    typical_assets=["distillation_column", "heat_exchanger", "pump", "compressor", "reactor", "flare_stack", "storage_tank"],
    typical_roles=["process_operator", "panel_operator", "instrument_technician", "shift_engineer", "safety_officer"],
    typical_products=["petrol", "diesel", "lpg", "jet_fuel", "bitumen", "naphtha"],
    hazards=["fire_explosion", "h2s_gas", "chemical_exposure", "confined_space", "high_pressure"],
    raw_materials=["crude_oil", "catalysts", "hydrogen", "chemicals", "steam"],
    key_processes=["distillation", "cracking", "reforming", "hydrotreating", "blending", "storage"],
    fictional_companies=["Godavari Petroleum Refiners", "Caspian Energy Processing", "Rio Plata Refinerias"],
    countries=["IN", "SA", "US", "CN", "RU", "AE", "KR", "JP"],
))

# ============================================================
# SECTOR C: MANUFACTURING INDUSTRIES
# ============================================================

_reg(IndustryConfig(
    id="automobile_assembly", sector="C_manufacturing", subsector="automobile",
    label="Automobile Assembly Plant",
    birth_year=1900, peak_era="mass_production",
    scale_range=("large", "global"),
    typical_assets=["robot_arm", "conveyor", "paint_booth", "press_machine", "testing_rig", "agv"],
    typical_roles=["assembly_worker", "robot_programmer", "quality_inspector", "line_supervisor", "logistics_coordinator"],
    typical_products=["passenger_car", "suv", "pickup_truck", "spare_parts"],
    hazards=["robot_collision", "paint_fumes", "press_crush", "repetitive_strain", "noise"],
    raw_materials=["steel_sheets", "plastic_parts", "glass", "wiring_harness", "tyres", "paint"],
    key_processes=["stamping", "welding", "painting", "assembly", "testing", "dispatch"],
    fictional_companies=["Bharath Motors Assembly", "Detroit River Automotive", "Shenzen EV Works"],
    countries=["IN", "JP", "DE", "US", "CN", "KR", "MX", "TH"],
))

_reg(IndustryConfig(
    id="electronics_pcb", sector="C_manufacturing", subsector="electronics",
    label="PCB Assembly & Electronics Manufacturing",
    birth_year=1960, peak_era="digital",
    scale_range=("small", "global"),
    typical_assets=["smt_machine", "reflow_oven", "wave_solder", "aoi_machine", "pick_and_place", "clean_room"],
    typical_roles=["smt_operator", "quality_inspector", "process_engineer", "test_technician", "material_handler"],
    typical_products=["pcb_assembly", "led_modules", "power_supply", "control_boards"],
    hazards=["solder_fume", "esd_damage", "repetitive_strain", "chemical_exposure"],
    raw_materials=["bare_pcb", "components", "solder_paste", "flux", "stencils"],
    key_processes=["solder_printing", "component_placement", "reflow", "inspection", "testing", "conformal_coating"],
    fictional_companies=["Hyderabad Circuit Works", "Shenzhen Microboard", "Silicon Valley PCB Assembly"],
    countries=["IN", "CN", "TW", "VN", "MY", "TH", "KR", "JP"],
))

_reg(IndustryConfig(
    id="pharmaceutical_tablet", sector="C_manufacturing", subsector="pharmaceutical",
    label="Pharmaceutical Tablet Manufacturing",
    birth_year=1900, peak_era="automation",
    scale_range=("medium", "global"),
    typical_assets=["granulator", "tablet_press", "coating_pan", "blister_packer", "hplc", "clean_room_hvac"],
    typical_roles=["production_pharmacist", "machine_operator", "qa_analyst", "packing_operator", "documentation_officer"],
    typical_products=["tablets", "capsules", "syrups", "ointments"],
    hazards=["dust_exposure", "cross_contamination", "chemical_handling", "clean_room_protocol"],
    raw_materials=["api_powder", "excipients", "coating_material", "packaging_foil", "purified_water"],
    key_processes=["dispensing", "granulation", "compression", "coating", "packing", "quality_testing"],
    fictional_companies=["Amaravathi Pharma Labs", "Geneva Therapeutics", "Lagos Pharmaceutical Works"],
    countries=["IN", "US", "CH", "DE", "CN", "BD", "IL", "IE"],
))



# ============================================================
# SECTOR D: INFRASTRUCTURE INDUSTRIES
# ============================================================

_reg(IndustryConfig(
    id="road_construction", sector="D_infrastructure", subsector="construction",
    label="Road & Highway Construction",
    birth_year=1800, peak_era="mass_production",
    scale_range=("small", "global"),
    typical_assets=["excavator", "road_roller", "asphalt_paver", "batching_plant", "dump_truck", "grader"],
    typical_roles=["site_engineer", "excavator_operator", "roller_operator", "surveyor", "foreman", "laborer"],
    typical_products=["asphalt_road", "concrete_road", "bridge", "culvert"],
    hazards=["vehicle_runover", "hot_asphalt_burn", "trench_collapse", "heavy_equipment"],
    raw_materials=["bitumen", "aggregate", "cement", "sand", "steel_rebar", "diesel"],
    key_processes=["surveying", "earthwork", "sub_base", "base_course", "paving", "compaction", "marking"],
    fictional_companies=["Deccan Infra Builders", "Trans-Continental Roads", "Sahel Highway Corp"],
    countries=["IN", "CN", "US", "AE", "NG", "BR", "DE", "AU"],
))

# ============================================================
# SECTOR E: ENERGY INDUSTRIES
# ============================================================

_reg(IndustryConfig(
    id="thermal_power_plant", sector="E_energy", subsector="power_generation",
    label="Coal-Fired Thermal Power Station",
    birth_year=1882, peak_era="mass_production",
    scale_range=("large", "global"),
    typical_assets=["boiler", "turbine", "generator", "condenser", "cooling_tower", "coal_conveyor", "transformer"],
    typical_roles=["boiler_operator", "turbine_engineer", "control_room_operator", "ash_handler", "electrician"],
    typical_products=["electricity_mw", "fly_ash", "bottom_ash", "steam"],
    hazards=["boiler_explosion", "steam_burn", "coal_dust_fire", "high_voltage", "confined_space"],
    raw_materials=["coal", "water", "chemicals", "lubricants", "hydrogen_gas"],
    key_processes=["coal_handling", "pulverizing", "combustion", "steam_generation", "turbine_drive", "power_export"],
    fictional_companies=["Simhadri Thermal Works", "Wyoming Power Generation", "Huainan Electric"],
    countries=["IN", "CN", "US", "DE", "AU", "ZA", "JP", "PL"],
))

_reg(IndustryConfig(
    id="solar_farm", sector="E_energy", subsector="renewable",
    label="Solar PV Farm & Installation",
    birth_year=1990, peak_era="ai_era",
    scale_range=("small", "global"),
    typical_assets=["solar_panel", "inverter", "tracker_mount", "transformer", "battery_storage", "weather_station"],
    typical_roles=["site_engineer", "panel_installer", "electrician", "drone_pilot", "cleaning_crew", "data_analyst"],
    typical_products=["solar_electricity", "renewable_energy_certificate"],
    hazards=["electrical_shock", "fall_from_height", "heat_stroke", "arc_flash"],
    raw_materials=["solar_modules", "mounting_structure", "cables", "inverters", "concrete"],
    key_processes=["site_survey", "foundation", "mounting", "stringing", "inverter_install", "commissioning", "monitoring"],
    fictional_companies=["Rajasthan Sun Power", "Atacama Solar Fields", "Sahara Renewable Energy"],
    countries=["IN", "CN", "US", "AE", "AU", "EG", "CL", "SA"],
))



# ============================================================
# SECTOR F: TECHNOLOGY INDUSTRIES
# ============================================================

_reg(IndustryConfig(
    id="software_company", sector="F_technology", subsector="software",
    label="Software Development Company",
    birth_year=1970, peak_era="digital",
    scale_range=("micro", "global"),
    typical_assets=["server_rack", "laptop", "monitor", "cloud_instance", "router", "ups"],
    typical_roles=["developer", "qa_tester", "product_manager", "scrum_master", "devops_engineer", "designer"],
    typical_products=["web_application", "mobile_app", "api_service", "saas_product"],
    hazards=["burnout", "ergonomic_injury", "data_breach", "deadline_stress"],
    raw_materials=["cloud_credits", "software_licenses", "api_keys", "hardware"],
    key_processes=["requirements", "design", "coding", "testing", "deployment", "monitoring", "support"],
    fictional_companies=["Hyderabad Code Labs", "Baltic Tech Solutions", "Santiago Digital Works"],
    countries=["IN", "US", "IL", "DE", "GB", "CA", "BR", "PL"],
))

_reg(IndustryConfig(
    id="data_center", sector="F_technology", subsector="it_services",
    label="Data Center Operations",
    birth_year=1990, peak_era="ai_era",
    scale_range=("medium", "global"),
    typical_assets=["server_rack", "ups_system", "cooling_unit", "fire_suppression", "generator", "network_switch"],
    typical_roles=["data_center_technician", "network_engineer", "security_guard", "cooling_specialist", "electrician"],
    typical_products=["compute_service", "storage_service", "colocation"],
    hazards=["electrical_shock", "overheating", "halon_exposure", "physical_security_breach"],
    raw_materials=["electricity", "cooling_water", "diesel_backup", "fiber_optic_cable", "server_hardware"],
    key_processes=["rack_install", "cabling", "power_distribution", "cooling", "monitoring", "patching", "decommission"],
    fictional_companies=["Chennai Cloud Campus", "Nordic Ice Data", "Dubai Digital Vault"],
    countries=["IN", "US", "IE", "SG", "NL", "JP", "AE", "SE"],
))

_reg(IndustryConfig(
    id="semiconductor_fab", sector="F_technology", subsector="semiconductor",
    label="Semiconductor Fabrication Plant",
    birth_year=1960, peak_era="ai_era",
    scale_range=("large", "global"),
    typical_assets=["lithography_machine", "etcher", "deposition_chamber", "clean_room", "wafer_handler", "metrology_tool"],
    typical_roles=["process_engineer", "equipment_technician", "clean_room_operator", "quality_engineer", "yield_analyst"],
    typical_products=["silicon_wafer", "integrated_circuit", "memory_chip", "processor"],
    hazards=["chemical_exposure", "radiation", "ergonomic_strain", "clean_room_protocol"],
    raw_materials=["silicon_wafer", "photoresist", "etchant_gas", "metals", "ultrapure_water"],
    key_processes=["wafer_prep", "oxidation", "lithography", "etching", "deposition", "ion_implant", "testing", "dicing"],
    fictional_companies=["Dravida Semiconductor", "Rhine Valley Chips", "Pacific Rim Foundry"],
    countries=["TW", "KR", "US", "JP", "CN", "DE", "IE", "SG"],
))



# ============================================================
# SECTOR G: CONSUMER INDUSTRIES
# ============================================================

_reg(IndustryConfig(
    id="supermarket_retail", sector="G_consumer", subsector="retail",
    label="Supermarket & Grocery Retail Chain",
    birth_year=1930, peak_era="digital",
    scale_range=("small", "global"),
    typical_assets=["pos_terminal", "cold_storage", "shelving_system", "cctv", "forklift", "delivery_van"],
    typical_roles=["store_manager", "cashier", "shelf_stocker", "butcher", "delivery_driver", "security_guard"],
    typical_products=["grocery_basket", "fresh_produce", "household_items"],
    hazards=["slip_fall", "lifting_injury", "robbery", "cold_room_lockout", "forklift_accident"],
    raw_materials=["products_from_suppliers", "packaging", "cleaning_supplies"],
    key_processes=["ordering", "receiving", "shelving", "pricing", "selling", "returns", "inventory"],
    fictional_companies=["Krishna Mart", "Fresh Valley Stores", "Nile Basket Supermarkets"],
    countries=["IN", "US", "GB", "DE", "BR", "NG", "AE", "AU"],
))

_reg(IndustryConfig(
    id="restaurant_kitchen", sector="G_consumer", subsector="hospitality",
    label="Restaurant & Commercial Kitchen",
    birth_year=1800, peak_era="digital",
    scale_range=("micro", "global"),
    typical_assets=["commercial_stove", "deep_fryer", "refrigerator", "dishwasher", "exhaust_hood", "pos_system"],
    typical_roles=["head_chef", "sous_chef", "line_cook", "waiter", "dishwasher", "manager", "delivery_partner"],
    typical_products=["prepared_meals", "takeaway_food", "catering_service"],
    hazards=["burn_injury", "knife_cut", "slip_on_grease", "fire", "food_poisoning_liability"],
    raw_materials=["vegetables", "meat", "spices", "cooking_oil", "gas_cylinder", "packaging"],
    key_processes=["menu_planning", "prep", "cooking", "plating", "serving", "cleaning", "inventory"],
    fictional_companies=["Spice Route Kitchen", "Golden Wok Restaurant", "Mediterranean Table"],
    countries=["IN", "US", "JP", "IT", "FR", "TH", "MX", "AE"],
))

# ============================================================
# SECTOR H: SERVICES INDUSTRIES
# ============================================================

_reg(IndustryConfig(
    id="hospital", sector="H_services", subsector="healthcare",
    label="Multi-Specialty Hospital",
    birth_year=1850, peak_era="digital",
    scale_range=("small", "global"),
    typical_assets=["ventilator", "ct_scanner", "operation_table", "autoclave", "oxygen_plant", "ambulance"],
    typical_roles=["doctor", "nurse", "surgeon", "technician", "pharmacist", "ward_boy", "receptionist"],
    typical_products=["patient_care", "surgery", "diagnostics", "rehabilitation"],
    hazards=["needle_stick", "infection_exposure", "radiation", "chemical_spill", "patient_violence"],
    raw_materials=["medicines", "surgical_supplies", "oxygen", "blood_products", "linen"],
    key_processes=["admission", "diagnosis", "treatment", "surgery", "recovery", "discharge", "billing"],
    fictional_companies=["Godavari General Hospital", "Alpine Medical Centre", "Lagos Teaching Hospital"],
    countries=["IN", "US", "GB", "DE", "NG", "BR", "TH", "AE"],
))

_reg(IndustryConfig(
    id="logistics_warehouse", sector="H_services", subsector="logistics",
    label="Logistics Warehouse & Distribution",
    birth_year=1900, peak_era="digital",
    scale_range=("small", "global"),
    typical_assets=["forklift", "pallet_rack", "conveyor", "barcode_scanner", "dock_leveler", "truck"],
    typical_roles=["warehouse_manager", "forklift_driver", "picker_packer", "dispatcher", "inventory_clerk"],
    typical_products=["fulfilled_orders", "cross_dock_service", "cold_chain_storage"],
    hazards=["forklift_accident", "falling_pallets", "dock_fall", "repetitive_strain"],
    raw_materials=["pallets", "shrink_wrap", "labels", "fuel"],
    key_processes=["receiving", "putaway", "picking", "packing", "shipping", "returns", "cycle_counting"],
    fictional_companies=["Vizag Cargo Hub", "Great Plains Logistics", "Silk Road Warehousing"],
    countries=["IN", "US", "CN", "AE", "DE", "SG", "NL", "BR"],
))



# ============================================================
# SECTOR I: ADVANCED INDUSTRIES
# ============================================================

_reg(IndustryConfig(
    id="aerospace_assembly", sector="I_advanced", subsector="aerospace",
    label="Aerospace Component Manufacturing",
    birth_year=1920, peak_era="ai_era",
    scale_range=("large", "global"),
    typical_assets=["cnc_5axis", "composite_layup", "autoclave", "ndt_scanner", "clean_room", "coordinate_measure"],
    typical_roles=["aerospace_engineer", "cnc_programmer", "ndt_inspector", "assembly_tech", "quality_auditor"],
    typical_products=["turbine_blade", "fuselage_section", "landing_gear", "avionics_unit"],
    hazards=["composite_dust", "autoclave_pressure", "chemical_exposure", "precision_stress"],
    raw_materials=["titanium_alloy", "carbon_fiber", "inconel", "adhesives", "sealants"],
    key_processes=["machining", "layup", "curing", "bonding", "ndt_inspection", "assembly", "testing"],
    fictional_companies=["Deccan Aero Components", "Nordic Sky Manufacturing", "Sao Paulo Aeronautica"],
    countries=["IN", "US", "FR", "DE", "GB", "BR", "CA", "JP"],
))

_reg(IndustryConfig(
    id="ai_research_lab", sector="I_advanced", subsector="ai_data",
    label="AI Research & Model Training Lab",
    birth_year=2010, peak_era="ai_era",
    scale_range=("micro", "global"),
    typical_assets=["gpu_cluster", "high_bandwidth_network", "cooling_system", "data_storage", "workstation"],
    typical_roles=["research_scientist", "ml_engineer", "data_annotator", "infrastructure_engineer", "ethics_reviewer"],
    typical_products=["trained_model", "research_paper", "api_endpoint", "dataset"],
    hazards=["burnout", "gpu_overheating", "data_leak", "bias_amplification"],
    raw_materials=["training_data", "compute_credits", "electricity", "annotation_labels"],
    key_processes=["data_collection", "preprocessing", "training", "evaluation", "fine_tuning", "deployment", "monitoring"],
    fictional_companies=["Hyderabad Neural Works", "Zurich Intelligence Lab", "Deep Pacific Research"],
    countries=["US", "CN", "GB", "CA", "IN", "IL", "FR", "KR"],
))

_reg(IndustryConfig(
    id="vaccine_manufacturing", sector="I_advanced", subsector="biotech",
    label="Vaccine & Biologics Manufacturing",
    birth_year=1900, peak_era="ai_era",
    scale_range=("medium", "global"),
    typical_assets=["bioreactor", "centrifuge", "freeze_dryer", "fill_finish_line", "cold_room", "clean_room"],
    typical_roles=["microbiologist", "production_pharmacist", "qa_specialist", "cold_chain_manager", "regulatory_affairs"],
    typical_products=["vaccine_vial", "monoclonal_antibody", "blood_product", "gene_therapy"],
    hazards=["biological_exposure", "needle_stick", "cold_chain_failure", "contamination"],
    raw_materials=["cell_culture_media", "virus_seed", "adjuvants", "vials", "stoppers"],
    key_processes=["cell_culture", "fermentation", "purification", "formulation", "fill_finish", "lyophilization", "qc_release"],
    fictional_companies=["Genome Valley Biologics", "Baltic Vaccines", "Cape Town Bio Works"],
    countries=["IN", "US", "DE", "GB", "CN", "KR", "CU", "BR"],
))


# ============================================================
# TOTAL COUNT
# ============================================================

def get_all_industries():
    return INDUSTRIES

def get_industries_by_sector(sector: str):
    return {k: v for k, v in INDUSTRIES.items() if v.sector == sector}

def get_industry(industry_id: str) -> IndustryConfig:
    return INDUSTRIES[industry_id]

# Import Phase 2 expansions
try:
    import world_engine.registry_phase2  # noqa: F401
except ImportError:
    pass

# Import Phase 3 expansions
try:
    import world_engine.registry_phase3  # noqa: F401
except ImportError:
    pass

# Import Phase 3 bulk expansion
try:
    import world_engine.registry_phase3_bulk  # noqa: F401
except ImportError:
    pass

# Import Phase 3 more expansion
try:
    import world_engine.registry_phase3_more  # noqa: F401
except ImportError:
    pass

# Import Phase 4 expansion
try:
    import world_engine.registry_phase4  # noqa: F401
except ImportError:
    pass

TOTAL_INDUSTRY_COUNT = len(INDUSTRIES)
