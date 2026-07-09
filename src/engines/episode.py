"""
Episode Generator — Produces coherent blocks of
industrial life events for one industry at a time.
"""
import random
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from world_engine.registry import IndustryConfig, INDUSTRIES
from world_engine.events import EVENT_CATEGORIES, MOODS, OUTCOMES
from world_engine.events import TIME_PATTERNS
from world_engine.era import get_era_for_year, ERAS
from world_engine.frequency import pick_event_category, pick_subtype_weighted
from world_engine.languages import WORKPLACE_PHRASES
from world_engine.realism import (
    apply_full_realism, get_time_interval, PersonContinuityEngine, MoodEngine
)
from world_engine.story_engine import StoryEngine, NightFilter
from world_engine.memory_engine import MemoryEngine, is_active_hour
from world_engine.digital_twin import StateTracker

# Industry-specific message templates (researched, real-world accurate)
try:
    from world_engine.industry_messages import get_industry_message
except ImportError:
    get_industry_message = lambda *args, **kwargs: None

# Drill & training event injection
try:
    from world_engine.drills import should_inject_drill
except ImportError:
    should_inject_drill = lambda *args, **kwargs: None

# Industry-specific jargon and communication style
try:
    from world_engine.industry_jargon import apply_jargon, get_industry_response
except ImportError:
    apply_jargon = lambda msg, *args, **kwargs: msg
    get_industry_response = lambda *args, **kwargs: None

# Seasonal patterns
try:
    from world_engine.seasonal import get_seasonal_message
except ImportError:
    get_seasonal_message = lambda *args, **kwargs: None

# Worker personality system
try:
    from world_engine.worker_personality import (
        get_worker_personality, modify_message_by_personality,
        clear_personality_cache, inject_hidden_behavior,
        apply_communication_style
    )
except ImportError:
    get_worker_personality = lambda *args, **kwargs: None
    modify_message_by_personality = lambda msg, *args, **kwargs: msg
    clear_personality_cache = lambda: None
    inject_hidden_behavior = lambda *args, **kwargs: None
    apply_communication_style = lambda msg, *args, **kwargs: msg

# Integration: import behavior engine for causal chain execution
try:
    from world_engine.industry_behavior import get_industry_behavior, get_active_causal_chain
except ImportError:
    def get_industry_behavior(x):
        return None
    def get_active_causal_chain(b, s, r):
        return None



# Multilingual message fragments (83+ languages represented)
# These are realistic workplace phrases
MSG_FRAGMENTS = {
    "en": [
        "check the pressure readings on tank 3",
        "morning shift starting, all clear",
        "need to replace the gasket before lunch",
        "who took the torque wrench from bay 2?",
        "supervisor wants the report by end of day",
        "production target is 500 units today",
        "the new guy is learning fast",
        "oil temperature looks high, keep an eye",
        "break time, anyone want tea?",
        "safety meeting at 10am don't forget",
        "night shift handover: pump B making noise",
        "delivery truck arrived gate 3",
        "quality rejected batch 47, recheck specs",
        "happy birthday boss, cake in canteen",
        "overtime approved for weekend",
    ],
    "te": [
        "tank 3 pressure chudandi, ekkuva undi",
        "morning shift start ayyindi, anni clear",
        "lunch loapala gasket marchcheyali",
        "bay 2 nunchi torque wrench evaru teesaru?",
        "supervisor report today loapala kavali annadu",
        "ee roju target 500 units",
        "kotha abbai baaga nerchukuntunaadu",
        "oil temperature ekkuva undi, chustu undandi",
        "break time, chai kaavala evariki?",
        "10 ki safety meeting, marchipokandi",
        "night shift handover: pump B sound vastondi",
        "delivery truck gate 3 lo vachindi",
        "quality batch 47 reject chesindi, specs check cheyyandi",
        "boss ki happy birthday, canteen lo cake undi",
        "weekend overtime approve ayyindi",
    ],
    "hi": [
        "tank 3 ka pressure check karo, zyada hai",
        "morning shift shuru, sab clear hai",
        "lunch se pehle gasket badalna hai",
        "bay 2 se torque wrench kisne liya?",
        "supervisor ne bola report aaj shaam tak chahiye",
        "aaj ka target 500 units hai",
        "naya ladka jaldi seekh raha hai",
        "oil temperature zyada dikh raha hai, dhyan rakho",
        "break time, chai chahiye kisko?",
        "10 baje safety meeting hai, bhoolna mat",
        "night shift handover: pump B mein awaaz aa rahi",
        "delivery truck gate 3 pe aaya",
        "quality ne batch 47 reject kiya, specs dubara check karo",
        "boss ko happy birthday, canteen mein cake hai",
        "weekend overtime approved hai",
    ],
    "ta": [
        "tank 3 pressure parunga, adhigama irukku",
        "morning shift start aachu, ellam clear",
        "lunch ku munna gasket maathanum",
        "bay 2 la irundhu torque wrench yaar eduthaanga?",
        "supervisor report inniki venumnu solraar",
        "inniki target 500 units",
        "pudhu paiyan seekirama kathukuraan",
        "oil temperature adhigama irukku, kavanama parunga",
        "break time, yaaaruku tea venum?",
        "10 maniku safety meeting, marakaadheenga",
        "night shift handover: pump B la sound varuthhu",
        "delivery truck gate 3 la vandhuruchu",
        "quality batch 47 reject panniruchu, specs parunga",
        "boss ku happy birthday, canteen la cake irukku",
        "weekend overtime approve aachu",
    ],
    "ar": [
        "افحص ضغط الخزان 3، مرتفع",
        "بداية وردية الصباح، كل شيء واضح",
        "لازم نغير الحشية قبل الغداء",
        "مين أخذ مفتاح العزم من المنطقة 2؟",
        "المشرف يبي التقرير قبل نهاية اليوم",
        "هدف اليوم 500 وحدة",
        "الموظف الجديد يتعلم بسرعة",
        "حرارة الزيت مرتفعة، خلوا بالكم",
        "وقت الاستراحة، أحد يبي شاي؟",
        "اجتماع السلامة الساعة 10، لا تنسون",
    ],
    "de": [
        "Tank 3 Druck pruefen, ist zu hoch",
        "Fruehschicht beginnt, alles klar",
        "Dichtung muss vor Mittag gewechselt werden",
        "Wer hat den Drehmomentschluessel aus Bucht 2 genommen?",
        "Vorarbeiter will den Bericht bis Feierabend",
        "Tagesziel sind 500 Stueck",
        "Der Neue lernt schnell",
        "Oeltemperatur sieht hoch aus, Auge drauf",
        "Pause, jemand Kaffee?",
        "Sicherheitsbesprechung um 10, nicht vergessen",
    ],
    "ja": [
        "タンク3の圧力を確認してください、高いです",
        "朝のシフト開始、全て正常",
        "昼前にガスケットを交換する必要があります",
        "ベイ2のトルクレンチを誰が持って行った？",
        "上司が今日中にレポートを欲しいと言っている",
        "今日の目標は500個",
        "新人の覚えが早い",
        "油温が高い、注意して",
        "休憩時間、お茶いる人？",
        "10時に安全ミーティング、忘れないで",
    ],
    "ko": [
        "탱크 3 압력 확인해주세요, 높습니다",
        "오전 근무 시작, 모두 정상",
        "점심 전에 가스켓 교체해야 합니다",
        "베이 2에서 토크 렌치 누가 가져갔어요?",
        "팀장님이 오늘 안에 보고서 달라고 했어요",
        "오늘 목표 500개",
        "신입이 빨리 배우고 있어요",
        "오일 온도 높아 보여요, 지켜봐 주세요",
        "쉬는 시간, 커피 마실 사람?",
        "10시에 안전 미팅, 잊지 마세요",
    ],
    "pt": [
        "verifica a pressao do tanque 3, ta alta",
        "turno da manha comecou, tudo certo",
        "precisa trocar a junta antes do almoco",
        "quem pegou a chave de torque do box 2?",
        "supervisor quer o relatorio ate o fim do dia",
        "meta de hoje e 500 pecas",
        "o novato ta aprendendo rapido",
        "temperatura do oleo ta alta, fica de olho",
        "hora do intervalo, alguem quer cafe?",
        "reuniao de seguranca as 10, nao esquece",
    ],
    "es": [
        "revisa la presion del tanque 3, esta alta",
        "turno de manana empezando, todo bien",
        "hay que cambiar la junta antes del almuerzo",
        "quien se llevo la llave de torque del area 2?",
        "el supervisor quiere el reporte antes de salir",
        "meta de hoy 500 unidades",
        "el nuevo aprende rapido",
        "temperatura del aceite esta alta, ojo",
        "hora de descanso, alguien quiere cafe?",
        "reunion de seguridad a las 10, no se olviden",
    ],
}



class EpisodeGenerator:
    """Generates one coherent episode (500-2000 lines) for one industry."""
    
    def __init__(self, industry: IndustryConfig, seed: int = 42,
                 year: int = 2024, episode_days: int = 5):
        self.industry = industry
        self.rng = random.Random(seed)
        self.year = year
        self.episode_days = episode_days
        self.era = get_era_for_year(year)
        self.company = self.rng.choice(industry.fictional_companies)
        self.country = self.rng.choice(industry.countries)
        self.day = 1
        self.hour = 6  # Start at 6 AM
        self.minute = 0
        self.current_date = datetime(year, self.rng.randint(1, 12), self.rng.randint(1, 28), 6, 0)
        self.workers = self._generate_workers()
        self.ongoing_issues = []
        self.mood_state = "routine"
        self.shift = "morning"
        self.person_engine = PersonContinuityEngine(self.workers, self.rng) if self.workers else None
        self.mood_engine = MoodEngine(self.rng)
        self.story_engine = StoryEngine(self.rng)
        self.memory_engine = MemoryEngine(self.rng)
        
        # Digital Twin StateTracker — persistent state across entire episode
        self.state_tracker = StateTracker(
            assets=industry.typical_assets[:5],
            rng=self.rng,
            country=self.country,
            month=self.current_date.month,
            industry_id=industry.id,
        )
        
        # Industry Behavior Engine — causal chains that execute during generation
        self.behavior = get_industry_behavior(industry.id)
        self.active_causal_effects: List[Dict] = []  # Currently active causal chain effects
        
        # ═══ CONVERSATION & THREADING STATE ═══
        self._event_counter = 0
        self._active_thread_id = None
        self._thread_position = 0
        self._thread_length = 0
        self._last_record_id = None
        self._recurrence_tracker: Dict[str, int] = {}  # subtype → count
        
        # Facility zones (generated per industry)
        self._facility_zones = self._generate_facility_zones()
        
        # ═══ ECOSYSTEM INTEGRATION ═══
        # Market, Regional, and Lifecycle engines now ACTIVE during generation
        from world_engine.ecosystem import (
            MarketDynamicsEngine, RegionalWorldModel, 
            EnterpriseLifecycleEngine, REGIONS,
            IndustryDependencyGraph, BlackSwanEngine
        )
        
        # Market state — affects costs, event probabilities, pressure
        self.market = MarketDynamicsEngine(self.rng)
        
        # Regional model — location-specific behavior modifiers
        region_id = self._pick_region(self.country)
        self.regional = RegionalWorldModel(region_id, self.rng)
        self.regional.set_month(self.current_date.month)
        
        # Enterprise lifecycle — age/stage affects maintenance, quality, risk
        lifecycle_stage = self.rng.choice(["startup", "growth", "maturity", "maturity", "maturity", "decline"])
        age = {"startup": 2, "growth": 5, "maturity": 15, "decline": 25}.get(lifecycle_stage, 10)
        self.lifecycle = EnterpriseLifecycleEngine(self.rng, lifecycle_stage, age)
        
        # Dependency Graph & Black Swan Integration
        self.dependency_graph = IndustryDependencyGraph()
        self.black_swan = BlackSwanEngine(self.rng, self.dependency_graph)
    
    def _generate_facility_zones(self) -> List[str]:
        """Generate realistic zones/areas for this facility."""
        generic_zones = ["zone A", "zone B", "zone C", "main building", "warehouse",
                        "control room", "utility area", "loading dock", "parking area"]
        industry_zones = {
            "oil_gas": ["unit 1", "unit 2", "unit 3", "tank farm", "flare area", "jetty", "lab", "control room"],
            "mining": ["face area", "surface", "winding room", "lamp room", "pit head", "washery", "conveyor gallery"],
            "healthcare": ["ward A", "ward B", "ICU", "OT complex", "ER", "lab", "pharmacy", "radiology"],
            "software": ["floor 3", "floor 4", "server room", "cafeteria", "meeting room 2", "open workspace"],
            "agriculture": ["field 1", "field 2", "field 3", "pump house", "storage shed", "threshing yard"],
            "food_processing": ["production hall", "packaging line", "cold room", "raw material store", "QC lab", "dispatch"],
            "construction": ["ground floor", "level 1", "level 2", "basement", "east wing", "crane zone", "rebar yard"],
            "retail": ["ground floor", "first floor", "back store", "loading bay", "billing counter", "cold section"],
        }
        subsector = self.industry.subsector
        for key, zones in industry_zones.items():
            if key in subsector or subsector in key:
                return zones
        return generic_zones
    
    def _pick_region(self, country: str) -> str:
        """Map country code to a regional profile."""
        country_region_map = {
            "IN": "IN_AP", "US": "US_TX", "DE": "DE_NRW", "JP": "JP_TK",
            "CN": "CN_GD", "SA": "SA_RYD", "AE": "AE_DXB", "NG": "NG_LG",
            "TH": "TH_BK", "BR": "BR_SP", "NO": "NO_OSL", "KR": "JP_TK",
            "AU": "US_TX", "GB": "DE_NRW", "FR": "DE_NRW", "RU": "NO_OSL",
        }
        return country_region_map.get(country, "IN_AP")
    
    def _generate_workers(self) -> List[Dict]:
        """Generate workforce for this episode with REALISTIC pyramid distribution."""
        n_workers = self.rng.randint(8, 40)
        workers = []
        for i in range(n_workers):
            role = self.rng.choice(self.industry.typical_roles)
            country = self.rng.choice(self.industry.countries)
            
            # REALISTIC experience pyramid:
            # 40% junior (0.5-3 years) — most workers are newer
            # 25% mid (3-8 years)
            # 20% senior (8-15 years)
            # 10% veteran (15-25 years)
            # 5% master (25-35 years) — very few
            exp_roll = self.rng.random()
            if exp_roll < 0.40:
                experience = round(self.rng.uniform(0.5, 3.0), 1)
            elif exp_roll < 0.65:
                experience = round(self.rng.uniform(3.0, 8.0), 1)
            elif exp_roll < 0.85:
                experience = round(self.rng.uniform(8.0, 15.0), 1)
            elif exp_roll < 0.95:
                experience = round(self.rng.uniform(15.0, 25.0), 1)
            else:
                experience = round(self.rng.uniform(25.0, 35.0), 1)
            
            # Assign languages based on country
            langs = ["en"]
            if country == "IN":
                langs = [self.rng.choice(["te", "hi", "ta", "kn", "ml"]), "en"]
            elif country in ("SA", "AE", "EG"):
                langs = ["ar", "en"]
            elif country == "DE":
                langs = ["de", "en"]
            elif country == "JP":
                langs = ["ja", "en"]
            elif country == "KR":
                langs = ["ko", "en"]
            elif country in ("BR", "PT"):
                langs = ["pt", "en"]
            elif country in ("MX", "ES", "AR"):
                langs = ["es", "en"]
            elif country in ("TH",):
                langs = ["th", "en"]
            elif country in ("VN",):
                langs = ["vi", "en"]
            elif country in ("ID",):
                langs = ["id", "en"]
            elif country in ("PH",):
                langs = ["tl", "en"]
            elif country in ("TR",):
                langs = ["tr", "en"]
            elif country in ("FR",):
                langs = ["fr", "en"]
            elif country in ("RU",):
                langs = ["ru", "en"]
            elif country in ("CN", "TW"):
                langs = ["zh", "en"]
            elif country in ("NG", "GH", "KE"):
                langs = ["sw", "en"] if country == "KE" else ["en"]
            
            workers.append({
                "id": f"W{i+1:03d}",
                "name_hash": hashlib.md5(f"{self.company}:{i}:{self.rng.getstate()[1][0]}".encode()).hexdigest()[:8],
                "role": role,
                "country": country,
                "languages": langs,
                "experience_years": experience,
                "personality": self.rng.choice(["quiet", "talkative", "leader", "joker", "serious", "newbie"]),
            })
        return workers
    
    def generate_episode(self, target_lines: int = 800) -> List[Dict]:
        """Generate a full episode."""
        records = []
        lines_generated = 0
        clear_personality_cache()  # Fresh personalities per episode
        
        # ═══ CACHED ECOSYSTEM STATE — only recalculate when engines tick ═══
        _cached_market_mods = None
        _cached_regional_mods = None
        _cached_lifecycle_mods = None
        _cached_shock_impact = None
        
        while lines_generated < target_lines:
            # ═══ ECOSYSTEM TICK — Market, Regional, Lifecycle, Black Swan advance ═══
            self.market.tick()
            _cached_market_mods = self.market.get_industry_cost_modifier(self.industry.id)
            
            if lines_generated % 50 == 0:  # Lifecycle evolves slowly
                self.lifecycle.tick()
                _cached_lifecycle_mods = self.lifecycle.get_modifiers()
            elif _cached_lifecycle_mods is None:
                _cached_lifecycle_mods = self.lifecycle.get_modifiers()
            
            self.regional.set_month(self.current_date.month)
            _cached_regional_mods = self.regional.get_modifiers(self.industry.id)
            
            new_shocks = self.black_swan.tick(market=self.market)
            _cached_shock_impact = self.black_swan.get_impact_on_industry(self.industry.id)
            # Use cached ecosystem modifiers
            market_mods = _cached_market_mods
            regional_mods = _cached_regional_mods
            lifecycle_mods = _cached_lifecycle_mods
            shock_impact = _cached_shock_impact
            
            # ═══ ECOSYSTEM-INFLUENCED EVENT SELECTION ═══
            # Market pressure can inject specific events
            market_override = self._check_market_pressure(market_mods)
            # Regional events (power outage, flood, etc.)
            regional_event = self.regional.generate_regional_event()
            
            # Check if a new shock needs announcement
            shock_announcement = None
            for shock in new_shocks:
                if self.industry.id in shock.affected_industries or shock_impact["total_impact"] > 0.05:
                    shock_announcement = shock
                    break
            
            # Check if an ongoing active shock forces a specific event type
            active_shock_override = None
            if shock_impact["total_impact"] > 0.1 and self.rng.random() < shock_impact["total_impact"] * 0.30:
                if self.black_swan.active_shocks:
                    relevant_shocks = [
                        s for s in self.black_swan.active_shocks
                        if (self.industry.id in s.affected_industries or 
                            any(link.target_industry == self.industry.id 
                                for aff in s.affected_industries 
                                for link in self.dependency_graph.get_downstream_dependents(aff)))
                    ]
                    if relevant_shocks:
                        chosen_shock = self.rng.choice(relevant_shocks)
                        effect_category_map = {
                            "labor_shortage": "workforce",
                            "infrastructure_damage": "maintenance",
                            "systems_down": "mistakes_failures",
                            "supply_chain_halt": "supply_chain",
                            "energy_crisis": "business",
                            "operational_halt": "crisis",
                            "market_disruption": "business",
                            "power_loss": "crisis",
                            "compliance_halt": "regulation",
                        }
                        primary_effect = self.black_swan.SHOCK_CATALOG[chosen_shock.shock_type]["primary_effect"]
                        active_shock_override = effect_category_map.get(primary_effect, "daily_ops")
            
            # Check if StoryEngine wants to override category
            hour = self.current_date.hour
            story_override = self.story_engine.should_override_category(hour)
            
            # Check if a causal chain wants to inject a specific event type
            causal_override = self._check_causal_chains()
            
            # Priority: shock_announcement > regional_event > causal > active_shock_override > market > story > normal
            subtype_override = None
            if shock_announcement:
                category_key = "crisis"
                subtype_map = {
                    "pandemic": "pandemic_lockdown",
                    "earthquake": "earthquake",
                    "cyberattack": "cyber_attack",
                    "port_shutdown": "supply_chain_collapse",
                    "fuel_shortage": "raw_material_crisis",
                    "flood": "flood_damage",
                    "trade_war": "supply_chain_collapse",
                    "grid_collapse": "power_grid_failure",
                    "regulatory_ban": "raw_material_crisis",
                }
                subtype_override = subtype_map.get(shock_announcement.shock_type, "supply_chain_collapse")
                self.mood_engine.trigger_mood_change("bad_news")
            elif regional_event:
                category_key = self._regional_event_to_category(regional_event)
            elif causal_override:
                category_key = causal_override
            elif active_shock_override:
                category_key = active_shock_override
            elif market_override:
                category_key = market_override
            elif story_override:
                category_key = story_override
            else:
                # Pick event category using REALISTIC frequency engine
                # NOW: industry-specific event weights
                category_key = pick_event_category(self.rng, industry_id=self.industry.id)
            
            # Night filter — reject inappropriate categories
            if not NightFilter.is_allowed(category_key, hour):
                category_key = NightFilter.get_night_replacement(self.rng)
                subtype_override = None
            
            if category_key not in EVENT_CATEGORIES:
                category_key = "daily_ops"
            category = EVENT_CATEGORIES[category_key]
            
            # Pick subtype
            if subtype_override and subtype_override in category["subtypes"]:
                subtype = subtype_override
            else:
                subtype = pick_subtype_weighted(self.rng, category["subtypes"])
            
            # Check if this event triggers a story chain
            self.story_engine.check_triggers(category_key, subtype, hour)
            
            # Record event in memory for future references
            self.memory_engine.record_event(category_key, subtype)
            
            # Skip event if industry is not active at this hour
            if not is_active_hour(hour, self.industry.subsector):
                self._advance_time()
                continue
            
            # Pick workers involved — use PersonContinuity engine
            if self.person_engine:
                primary_worker = self.person_engine.get_active_person()
                involved = [primary_worker]
                if self.person_engine.should_generate_response():
                    partner = self.person_engine.get_conversation_partner()
                    if partner:
                        involved.append(partner)
            else:
                n_involved = self.rng.randint(1, min(4, len(self.workers)))
                involved = self.rng.sample(self.workers, n_involved)
            
            # Generate the record
            record = self._generate_record(category_key, subtype, involved, lines_generated)
            records.append(record)
            lines_generated += 1
            
            # Advance time (variable intervals — realistic)
            self._advance_time()
        
        return records
    
    def _advance_time(self):
        """Advance time by realistic variable interval based on time of day."""
        hour = self.current_date.hour
        dt_minutes = get_time_interval(hour, self.rng, self.mood_state)
        
        # Fix: 24/7 industries should have more activity at night
        # Reduce night intervals for continuous operations
        from world_engine.memory_engine import SUBSECTOR_SCHEDULE
        schedule_type = SUBSECTOR_SCHEDULE.get(self.industry.subsector, "two_shift")
        if schedule_type == "24x7" and (hour >= 22 or hour < 6):
            # Night intervals too long by default — scale down for 24/7
            dt_minutes = dt_minutes * 0.4  # 60% faster events at night for 24/7
        
        self.current_date += timedelta(minutes=dt_minutes)
        self._last_event_gap = dt_minutes
        self.hour = self.current_date.hour
        
        # Update shift
        if 6 <= self.hour < 14:
            new_shift = "morning"
        elif 14 <= self.hour < 22:
            new_shift = "afternoon"
        else:
            new_shift = "night"
        if new_shift != self.shift:
            self.memory_engine.on_shift_change(new_shift)
        self.shift = new_shift
    
    def _check_market_pressure(self, market_mods: Dict) -> Optional[str]:
        """Market conditions can force specific event types.
        
        High energy prices → more cost/maintenance events
        Labor shortage → workforce/overtime events
        Shipping disruption → supply chain events
        Demand spike → business/overtime events
        """
        # Energy price pressure
        if market_mods.get("energy_cost_multiplier", 1.0) > 1.3:
            if self.rng.random() < 0.03:  # 3% chance per tick when energy is high
                return self.rng.choice(["business", "maintenance"])
        
        # Labor shortage
        if market_mods.get("labor_cost_multiplier", 1.0) > 1.2:
            if self.rng.random() < 0.02:
                return "workforce"
        
        # Logistics disruption
        if market_mods.get("logistics_cost_multiplier", 1.0) > 1.4:
            if self.rng.random() < 0.04:
                return "supply_chain"
        
        # Demand pressure
        if market_mods.get("demand_multiplier", 1.0) > 1.2:
            if self.rng.random() < 0.02:
                return self.rng.choice(["business", "workforce"])
        
        # Demand collapse
        if market_mods.get("demand_multiplier", 1.0) < 0.7:
            if self.rng.random() < 0.02:
                return "business"
        
        return None
    
    def _regional_event_to_category(self, event: Dict) -> str:
        """Convert a regional event to an event category."""
        event_type = event.get("type", "")
        mapping = {
            "power_outage": "crisis",
            "flood_event": "weather_environment",
            "heat_advisory": "weather_environment",
            "regulatory_inspection": "regulation",
        }
        return mapping.get(event_type, "weather_environment")
    
    def _check_causal_chains(self) -> Optional[str]:
        """Check if industry behavior causal chains should fire.
        
        Returns an event category override if a causal chain activates,
        or None to use normal event selection.
        """
        if not self.behavior:
            return None
        
        # Check if any active causal effects should produce events now
        for effect in self.active_causal_effects[:]:
            effect["delay_remaining"] -= 1
            if effect["delay_remaining"] <= 0:
                self.active_causal_effects.remove(effect)
                # This effect manifests — override the event category
                # Map causal step to an event category
                step_type = effect.get("cascade_type", "")
                category_map = {
                    "harvest_delay": "supply_chain",
                    "quality_degradation": "quality",
                    "spoilage": "quality",
                    "revenue_loss": "business",
                    "line_starvation": "supply_chain",
                    "line_stop": "crisis",
                    "overtime_authorized": "workforce",
                    "quality_risk": "quality",
                    "staff_fatigue": "workforce",
                    "medication_error_risk": "safety_accidents",
                    "adverse_event": "safety_accidents",
                    "inspection_triggered": "maintenance",
                    "production_curtailment": "business",
                    "shutdown_decision": "crisis",
                    "efficiency_decline": "maintenance",
                    "reline_planning": "maintenance",
                    "waterlogging": "weather_environment",
                    "crop_wilting": "daily_ops",
                }
                return category_map.get(step_type, None)
        
        # Check if a new causal chain should activate
        try:
            result = get_active_causal_chain(self.behavior, {}, self.rng)
        except (AttributeError, TypeError, KeyError):
            result = None
        if result:
            chain_name, step = result
            # Schedule the chain's next steps as future effects
            if hasattr(step, 'next_steps') and step.next_steps:
                for next_step_name in step.next_steps:
                    self.active_causal_effects.append({
                        "cascade_type": next_step_name,
                        "delay_remaining": getattr(step, 'delay_events', 5) + self.rng.randint(0, 3),
                        "source_chain": chain_name,
                        "probability": min(1.0, max(0.0, getattr(step, 'probability', 0.5))),
                    })
            # The triggering step itself creates an event now
            trigger_categories = {
                "monsoon_cascade": "weather_environment",
                "irrigation_failure": "maintenance",
                "labor_shortage": "workforce",
                "corrosion_cascade": "maintenance",
                "turnaround_cascade": "maintenance",
                "process_upset": "crisis",
                "supplier_cascade": "supply_chain",
                "paint_contamination": "quality",
                "patient_surge": "workforce",
                "equipment_critical": "maintenance",
                "thermal_degradation": "maintenance",
                "raw_material_quality": "supply_chain",
            }
            return trigger_categories.get(chain_name, None)
        
        return None
    
    def _generate_record(self, category_key: str, subtype: str,
                         involved: List[Dict], event_position: int = 0) -> Dict:
        """Generate one event record."""
        primary = involved[0]
        
        # Choose language for message
        lang = self._pick_language(primary)
        message = self._generate_message(lang, category_key, subtype, primary)
        specific_msg_used = getattr(self, '_last_msg_was_specific', False)
        
        # Variable message length (some short, some long — realistic)
        if self.rng.random() < 0.3:
            # Short message (like radio comms)
            pass  # Keep as is
        elif self.rng.random() < 0.5:
            # Medium — add context (ONLY if message is from generic template)
            # Don't append to industry-specific messages (they're already complete)
            if not specific_msg_used:
                context = self._add_context(category_key, subtype)
                message = f"{message}. {context}"
        else:
            # Long — full detail (ONLY if generic)
            if not specific_msg_used:
                detail = self._add_detail(category_key, subtype, primary)
                message = f"{message}. {detail}"
        
        # === APPLY WORKER PERSONALITY to message ===
        personality = get_worker_personality(
            primary["id"], primary["experience_years"], self.rng)
        if personality:
            # Hidden behaviors (very rare: subtle anomalies)
            hidden_msg = inject_hidden_behavior(personality, category_key, self.rng)
            if hidden_msg:
                message = hidden_msg
            else:
                message = modify_message_by_personality(
                    message, personality, category_key, self.rng)
            # Apply consistent communication style (emoji, formality, verbosity)
            message = apply_communication_style(
                message, personality, self.current_date.hour, self.rng)
        
        # === TICK THE STATE TRACKER (persistent world state advances) ===
        self.state_tracker.tick(
            event_category=category_key,
            event_subtype=subtype,
            message=message,
            current_hour=self.current_date.hour,
            current_shift=self.shift,
            dt_minutes=10.0,  # Approximate interval
        )
        
        # Fatigue-influenced errors: tired operators make more typos/mistakes
        fatigue_error_prob = self.state_tracker.fatigue_model.get_error_probability()
        
        # Get equipment health for urgency scoring
        _snap = self.state_tracker.get_state_snapshot()
        eq_health = _snap.get("digital_twin", {}).get("worst_equipment", {}).get("health", 0.9)
        
        # Cache snapshot for reuse (avoids calling 5x per event)
        self._cached_snapshot = _snap
        
        # === GENERATE RECORD WITH ALL 15 NEW FIELDS ===
        self._event_counter += 1
        record_id = f"{self.industry.id}_{self.company[:8]}_{self._event_counter:05d}"
        
        # Thread management: 25% of events start in conversation threads
        if self._active_thread_id and self._thread_position < self._thread_length:
            thread_id = self._active_thread_id
            reply_to = self._last_record_id
            self._thread_position += 1
            if self._thread_position >= self._thread_length:
                self._active_thread_id = None  # End thread
        elif self.rng.random() < 0.15:
            # Start new thread (15% chance)
            thread_id = f"thread_{self._event_counter:05d}"
            self._active_thread_id = thread_id
            self._thread_length = self.rng.randint(2, 4)
            self._thread_position = 1
            reply_to = None
        else:
            thread_id = None
            reply_to = None
            self._active_thread_id = None
        
        # Recurrence tracking
        self._recurrence_tracker[subtype] = self._recurrence_tracker.get(subtype, 0) + 1
        recurrence_count = self._recurrence_tracker[subtype]
        
        # Message type classification
        msg_lower = message.lower() if message else ""
        if "?" in message:
            message_type = "question"
        elif any(w in msg_lower for w in ["do ", "check ", "please ", "go ", "stop ", "start "]):
            message_type = "instruction"
        elif any(w in msg_lower for w in ["done", "complete", "fixed", "sorted", "noted"]):
            message_type = "response"
        elif any(w in msg_lower for w in ["🚨", "emergency", "alert", "alarm", "STOP", "evacuate"]):
            message_type = "alert"
        elif any(w in msg_lower for w in ["update", "status", "report", "reading", "count"]):
            message_type = "report"
        else:
            message_type = self.rng.choice(["report", "observation", "update", "comment"])
        
        # Recipient/audience
        if thread_id:
            audience = "reply"
        elif message_type == "alert":
            audience = "broadcast_all"
        elif message_type == "instruction":
            audience = self.rng.choice(["direct_message", "team_channel", "shift_group"])
        else:
            audience = self.rng.choice(["shift_group", "team_channel", "department", "general"])
        
        # Location within facility
        location = self.rng.choice(self._facility_zones)
        
        # Response time (how long after the event did this message come)
        if message_type == "alert":
            response_time_seconds = self.rng.randint(5, 30)
        elif message_type == "response":
            response_time_seconds = self.rng.randint(15, 300)
        else:
            response_time_seconds = self.rng.randint(30, 900)
        
        # Duration of activity
        duration_map = {"daily_ops": (5, 60), "maintenance": (30, 480), "crisis": (10, 240),
                       "safety_accidents": (5, 120), "quality": (15, 120), "human_relations": (2, 30)}
        dur_range = duration_map.get(category_key, (5, 60))
        duration_minutes = self.rng.randint(dur_range[0], dur_range[1])
        
        # Deadline
        if category_key in ("crisis", "safety_accidents"):
            deadline = "immediate"
        elif category_key in ("maintenance", "quality"):
            deadline = self.rng.choice(["end_of_shift", "today", "this_week", "next_pm_window"])
        else:
            deadline = self.rng.choice(["none", "end_of_shift", "today", None])
        
        # Named entities extraction from message
        named_entities = self._extract_named_entities(message, primary, category_key)
        
        # Multilabel (event can be multiple categories)
        secondary_labels = []
        if category_key == "maintenance" and self.rng.random() < 0.3:
            secondary_labels.append("safety_risk")
        if category_key == "mistakes_failures" and self.rng.random() < 0.4:
            secondary_labels.append("quality_impact")
        if category_key == "crisis":
            secondary_labels.extend(["safety_risk", "business_impact"])
        if category_key == "supply_chain" and self.rng.random() < 0.3:
            secondary_labels.append("business_impact")
        
        # Media indicator
        has_media = self.rng.random() < 0.08  # 8% of messages reference media
        media_type = None
        if has_media:
            media_type = self.rng.choice(["photo", "photo", "video", "document", "voice_note", "screenshot"])
        
        # QA pair
        qa_pair = self._generate_qa_pair(category_key, subtype, message, primary)
        
        # Instruction-response pair
        instruction_pair = self._generate_instruction_response(category_key, subtype, message)
        
        # Embedding hint
        embedding_hint = self._generate_embedding_hint(category_key, subtype)
        
        # Final message with media reference
        final_message = apply_full_realism(
            apply_jargon(
                self.memory_engine.add_memory_to_message(message, category_key),
                self.industry.id, self.rng),
            self.rng, category_key,
            self.current_date.hour, self.mood_engine.get_mood(),
            industry_id=self.industry.id, subsector=self.industry.subsector)
        
        if has_media and self.rng.random() < 0.5:
            media_refs = {
                "photo": ["📸", " [photo attached]", " — see pic"],
                "video": [" [video attached]", " 🎥"],
                "document": [" [doc attached]", " — check the PDF"],
                "voice_note": [" [voice note]", " 🎤"],
                "screenshot": [" [screenshot]", " — see attached"],
            }
            final_message += self.rng.choice(media_refs.get(media_type, [""]))
        
        record = {
            # === CORE IDENTIFIERS ===
            "record_id": record_id,
            "timestamp": self.current_date.isoformat() + "Z",
            "industry": self.industry.id,
            "industry_label": self.industry.label,
            "company": self.company,
            "sector": self.industry.sector,
            "era": self.era["label"],
            "year": self.year,
            "location_country": self.country,
            "location_facility": location,
            
            # === EVENT CLASSIFICATION ===
            "event_category": category_key,
            "event_subtype": subtype,
            "secondary_labels": secondary_labels,
            "shift": self.shift,
            
            # === COMMUNICATION ===
            "message": final_message,
            "message_type": message_type,
            "audience": audience,
            "thread_id": thread_id,
            "reply_to": reply_to,
            "thread_position": self._thread_position if thread_id else None,
            "media_attached": media_type,
            
            # === ACTORS ===
            "primary_actor": {
                "id": primary["id"],
                "role": primary["role"],
                "experience_years": primary["experience_years"],
                "language": lang,
            },
            "recipient": audience,
            "involved_count": len(involved),
            
            # === TEMPORAL ===
            "response_time_seconds": response_time_seconds,
            "duration_minutes": duration_minutes,
            "deadline": deadline,
            "recurrence_count": recurrence_count,
            
            # === CONTEXT ===
            "mood": self.mood_engine.get_mood(),
            "outcome": self.rng.choice(OUTCOMES) if self.rng.random() > 0.6 else None,
            "assets_mentioned": self._pick_assets(),
            "tags": self._generate_tags(category_key, subtype),
            
            # === NAMED ENTITIES ===
            "named_entities": named_entities,
            
            # === AI TRAINING PAIRS ===
            "qa_pair": qa_pair,
            "instruction_response": instruction_pair,
            "embedding_hint": embedding_hint,
            
            # === ENGINE STATE ===
            "ecosystem_shocks": self.black_swan.get_impact_on_industry(self.industry.id),
            "_state_snapshot": self._cached_snapshot,
            "_ai_training": self._generate_ai_training_fields(
                category_key, subtype, message, primary, event_position),
            
            # === ENRICHMENT FIELDS (Final 15) ===
            "worker_name": self._get_worker_name(primary),
            "delivery_status": self.rng.choice(["sent", "delivered", "read", "read"]),
            "reactions": self._generate_reactions(),
            "is_edited": self.rng.random() < 0.03,
            "is_forwarded": self.rng.random() < 0.05 and category_key in ("regulation", "leadership", "safety_accidents"),
            "sentiment_score": self._compute_sentiment(final_message, category_key),
            "urgency_score": self._compute_urgency(category_key, subtype, eq_health),
            "detected_language": self._detect_message_language(final_message),
            "word_count": len(final_message.split()),
            "char_count": len(final_message),
            "previous_event_gap_minutes": round(self._last_event_gap, 1) if hasattr(self, '_last_event_gap') else 0.0,
            "cost_impact_usd": self._estimate_event_cost(category_key, subtype),
            "regulatory_reportable": category_key in ("safety_accidents", "crisis") and self.rng.random() < 0.4,
            "shift_hours_remaining": round(max(0, 8.0 - (self.state_tracker.fatigue_model.hours_into_shift)), 1),
            "weather": self._get_current_weather(),
            "equipment_age_hours": self._get_equipment_age(),
            # === UNIVERSAL FIELDS (all worlds share) ===
            "confidence_score": round(self.rng.uniform(0.4, 1.0), 2),
            "follow_up_required": category_key in ("maintenance", "crisis", "safety_accidents", "quality", "mistakes_failures"),
            "priority_level": "P0" if category_key == "crisis" else "P1" if category_key in ("safety_accidents",) else "P2" if category_key in ("maintenance", "quality") else "P3",
            "related_record_ids": [self._last_record_id] if self._last_record_id and self.rng.random() < 0.3 else [],
            "resolution_status": self.rng.choice(["open", "in_progress", "resolved"]) if category_key in ("maintenance", "crisis", "mistakes_failures") else None,
            "time_zone": {"IN": "Asia/Kolkata", "US": "America/New_York", "GB": "Europe/London", "JP": "Asia/Tokyo", "DE": "Europe/Berlin", "SA": "Asia/Riyadh", "AE": "Asia/Dubai", "CN": "Asia/Shanghai"}.get(self.country, "UTC"),
            "platform": self.rng.choice(["whatsapp", "radio", "scada_terminal", "teams", "email"]),
        }
        
        self._last_record_id = record_id
        
        # Occasionally update mood state
        if subtype in ("fire_outbreak", "explosion", "serious_injury", "system_crash"):
            self.mood_state = "crisis"
        elif subtype in ("breakdown_repair", "material_shortage", "customer_complaint"):
            self.mood_state = "urgent"
        elif subtype in ("tea_break_chat", "lunch_together", "birthday_celebration"):
            self.mood_state = "relaxed"
        elif self.rng.random() < 0.1:
            self.mood_state = "routine"
        
        return record
    
    def _generate_ai_training_fields(self, category: str, subtype: str,
                                      message: str, worker: Dict,
                                      event_position: int) -> Dict:
        """Generate world-class AI training enrichments.
        
        These fields make this dataset uniquely powerful for training:
        1. Counterfactuals — what would have happened otherwise
        2. Multi-perspective — same event seen by different roles
        3. Causal links — explicit cause/effect chains
        4. Prediction targets — future state with ground truth
        5. Difficulty labels — how hard is this to predict/classify
        """
        state = self._cached_snapshot
        eq_health = state.get("digital_twin", {}).get("worst_equipment", {}).get("health", 0.9)
        fatigue = state.get("operator_fatigue", {}).get("alertness_level", 0.8)
        
        # ═══ 1. COUNTERFACTUAL: What would happen if action not taken ═══
        counterfactual = self._generate_counterfactual(category, subtype, eq_health, fatigue)
        
        # ═══ 2. MULTI-PERSPECTIVE: Same event, different viewpoints ═══
        perspectives = self._generate_perspectives(category, subtype, message, worker)
        
        # ═══ 3. CAUSAL LINKS: What caused this, what this will cause ═══
        causal = self._generate_causal_links(category, subtype, event_position)
        
        # ═══ 4. PREDICTION TARGETS: Future state ground truth ═══
        predictions = self._generate_prediction_targets(eq_health, fatigue, event_position)
        
        # ═══ 5. DIFFICULTY LABEL: How hard is this event to classify ═══
        difficulty = self._compute_difficulty(category, subtype, message)
        
        # ═══ 6. REASONING CHAIN: Expert thought process ═══
        reasoning = self._generate_reasoning_chain(category, subtype, eq_health, fatigue, message)
        
        # ═══ 7. ANOMALY SCORE: How unusual is this event? ═══
        anomaly = self._compute_anomaly_score(category, subtype, eq_health, fatigue, event_position)
        
        # ═══ 8. RISK MATRIX: Probability × Impact ═══
        risk = self._compute_risk_matrix(category, subtype, eq_health)
        
        # ═══ 9. KNOWLEDGE GRAPH TRIPLES ═══
        kg_triples = self._generate_kg_triples(category, subtype, worker, message)
        
        # ═══ 10. MULTI-GRANULARITY SUMMARY ═══
        summaries = self._generate_summaries(category, subtype, message)
        
        # ═══ 11. LEARNING OBJECTIVES ═══
        objectives = self._generate_learning_objectives(category, subtype, difficulty)
        
        return {
            "counterfactual": counterfactual,
            "perspectives": perspectives,
            "causal_graph": causal,
            "prediction_targets": predictions,
            "difficulty": difficulty,
            "reasoning_chain": reasoning,
            "anomaly": anomaly,
            "risk_matrix": risk,
            "knowledge_graph": kg_triples,
            "summaries": summaries,
            "learning_objectives": objectives,
        }
    
    def _generate_counterfactual(self, category: str, subtype: str,
                                  eq_health: float, fatigue: float) -> Dict:
        """What would happen if this event was ignored/not addressed?
        
        Enables AI to learn decision-making: "if I don't act, X happens."
        """
        # Base severity of inaction
        severity_map = {
            "crisis": 0.95, "safety_accidents": 0.85, "maintenance": 0.6,
            "mistakes_failures": 0.5, "quality": 0.4, "supply_chain": 0.35,
            "business": 0.3, "daily_ops": 0.1, "human_relations": 0.05,
        }
        base_severity = severity_map.get(category, 0.2)
        
        # Equipment health affects consequences
        if eq_health < 0.4:
            base_severity = min(1.0, base_severity * 1.5)
        
        # Fatigue amplifies mistakes
        if fatigue < 0.5:
            base_severity = min(1.0, base_severity * 1.2)
        
        # Generate counterfactual outcome
        if base_severity > 0.7:
            outcome = self.rng.choice([
                "equipment failure within 24 hours",
                "safety incident probable",
                "production line stoppage",
                "cascading failure to downstream systems",
                "emergency shutdown required",
            ])
            cost_usd = self.rng.randint(10000, 500000)
            time_to_failure_hours = round(self.rng.uniform(2, 48), 1)
        elif base_severity > 0.3:
            outcome = self.rng.choice([
                "quality degradation over next shift",
                "minor equipment damage accumulates",
                "delayed delivery to customer",
                "overtime required to recover",
                "rework needed on affected batch",
            ])
            cost_usd = self.rng.randint(500, 50000)
            time_to_failure_hours = round(self.rng.uniform(24, 168), 1)
        else:
            outcome = self.rng.choice([
                "no significant impact",
                "minor inconvenience",
                "resolved naturally",
                "negligible effect on operations",
            ])
            cost_usd = 0
            time_to_failure_hours = None
        
        return {
            "if_ignored": outcome,
            "severity_score": round(base_severity, 3),
            "estimated_cost_if_ignored_usd": cost_usd,
            "time_to_consequence_hours": time_to_failure_hours,
            "action_criticality": (
                "critical" if base_severity > 0.7 else
                "important" if base_severity > 0.4 else
                "routine" if base_severity > 0.15 else
                "optional"
            ),
        }
    
    def _generate_perspectives(self, category: str, subtype: str,
                                message: str, worker: Dict) -> Dict:
        """Same event described from different viewpoints.
        
        Enables AI to understand role-based reasoning.
        """
        asset = self.rng.choice(self.industry.typical_assets).replace("_", " ")
        
        # Operator perspective (doing the work)
        operator_view = self.rng.choice([
            f"doing my job, noticed issue with {asset}",
            f"was working on {asset} when this happened",
            f"following procedure, everything by the book",
            f"routine task, nothing unusual from my end",
        ])
        
        # Supervisor perspective (managing risk)
        if category in ("crisis", "safety_accidents", "mistakes_failures"):
            supervisor_view = self.rng.choice([
                "need immediate containment. who else is in the area?",
                "escalating to management. document everything",
                "root cause investigation required. preserve evidence",
                "checking if this triggers any regulatory notification",
            ])
        else:
            supervisor_view = self.rng.choice([
                "noted. is this within normal parameters?",
                "keep monitoring. report if it gets worse",
                "log it and continue. we'll review in shift meeting",
                "acceptable. no action needed from my side",
            ])
        
        # Safety officer perspective
        if category in ("safety_accidents", "crisis"):
            safety_view = self.rng.choice([
                "immediate area isolation needed. check PPE compliance",
                "near miss classification. filing safety observation report",
                "review risk assessment for this activity",
                "toolbox talk topic for tomorrow: this exact scenario",
            ])
        else:
            safety_view = self.rng.choice([
                "no safety concern identified",
                "routine from safety perspective",
                "monitoring — no intervention needed",
            ])
        
        # Maintenance perspective
        maintenance_view = self.rng.choice([
            f"{asset} condition is within acceptable range",
            f"scheduling inspection of {asset} in next PM window",
            f"no maintenance action required at this time",
            f"added to watchlist for next planned downtime",
        ])
        
        return {
            "operator": operator_view,
            "supervisor": supervisor_view,
            "safety_officer": safety_view,
            "maintenance": maintenance_view,
        }
    
    def _generate_causal_links(self, category: str, subtype: str,
                                event_position: int) -> Dict:
        """Explicit cause-effect relationships.
        
        Enables AI to learn causal reasoning, not just correlation.
        """
        # What caused this event
        if category == "maintenance":
            caused_by = self.rng.choice([
                "normal wear over time",
                "previous overload event",
                "missed preventive maintenance",
                "environmental exposure",
                "operating beyond design parameters",
            ])
        elif category in ("crisis", "safety_accidents"):
            caused_by = self.rng.choice([
                "human error under fatigue",
                "equipment degradation undetected",
                "multiple safeguards bypassed",
                "unusual operating conditions",
                "inadequate training for this scenario",
                "communication failure between shifts",
            ])
        elif category == "quality":
            caused_by = self.rng.choice([
                "raw material variation",
                "process parameter drift",
                "instrument calibration error",
                "operator inexperience",
                "environmental condition change",
            ])
        else:
            caused_by = self.rng.choice([
                "normal operational sequence",
                "scheduled activity",
                "external trigger",
                "routine workflow",
            ])
        
        # What this event will likely trigger next
        consequence_map = {
            "maintenance": ["quality_check", "production_delay", "parts_ordering"],
            "crisis": ["investigation", "shutdown", "regulatory_report", "insurance_claim"],
            "safety_accidents": ["investigation", "retraining", "procedure_revision"],
            "quality": ["rework", "customer_notification", "process_adjustment"],
            "supply_chain": ["production_reschedule", "vendor_escalation", "buffer_depletion"],
            "daily_ops": ["shift_handover_note", "log_entry", "no_further_action"],
            "human_relations": ["mood_change", "team_dynamics_shift", "no_further_action"],
        }
        will_cause = self.rng.choice(
            consequence_map.get(category, ["no_further_action"])
        )
        
        # Causal chain depth (how many events back/forward is this connected)
        chain_depth = 1 if category in ("daily_ops", "human_relations") else self.rng.randint(1, 4)
        
        return {
            "caused_by": caused_by,
            "will_trigger": will_cause,
            "causal_chain_depth": chain_depth,
            "event_position_in_episode": event_position,
            "is_root_cause": self.rng.random() < 0.1,  # 10% of events are root causes
            "is_symptom": category in ("quality", "maintenance") and self.rng.random() < 0.4,
        }
    
    def _generate_prediction_targets(self, eq_health: float, fatigue: float,
                                      event_position: int) -> Dict:
        """Ground truth for prediction tasks.
        
        These are the ANSWERS the model should learn to predict.
        """
        # Time to next failure (based on equipment health trajectory)
        if eq_health < 0.3:
            ttf_hours = round(self.rng.uniform(1, 24), 1)
        elif eq_health < 0.6:
            ttf_hours = round(self.rng.uniform(24, 168), 1)
        elif eq_health < 0.85:
            ttf_hours = round(self.rng.uniform(168, 720), 1)
        else:
            ttf_hours = round(self.rng.uniform(720, 5000), 1)
        
        # Will escalation happen in next 10 events?
        escalation_prob = 0.0
        if eq_health < 0.4:
            escalation_prob += 0.3
        if fatigue < 0.5:
            escalation_prob += 0.2
        escalation_prob = min(0.95, escalation_prob + self.rng.uniform(0, 0.1))
        will_escalate = self.rng.random() < escalation_prob
        
        # Optimal action (what should be done)
        if eq_health < 0.4:
            optimal_action = "immediate_maintenance"
        elif eq_health < 0.7:
            optimal_action = "schedule_maintenance"
        elif fatigue < 0.4:
            optimal_action = "rotate_operator"
        else:
            optimal_action = "continue_monitoring"
        
        return {
            "time_to_next_failure_hours": ttf_hours,
            "will_escalate_within_10_events": will_escalate,
            "escalation_probability": round(escalation_prob, 3),
            "optimal_action": optimal_action,
            "equipment_health_in_50_events": round(max(0, eq_health - self.rng.uniform(0.02, 0.08)), 3),
        }
    
    def _compute_difficulty(self, category: str, subtype: str, message: str) -> Dict:
        """How hard is this event for an AI to process correctly?
        
        Enables curriculum learning — train on easy first, hard later.
        """
        difficulty_score = 0.5  # Base: medium
        
        # Category complexity
        easy_cats = {"daily_ops", "human_relations", "holidays_breaks"}
        hard_cats = {"crisis", "safety_accidents", "mistakes_failures"}
        if category in easy_cats:
            difficulty_score -= 0.2
        elif category in hard_cats:
            difficulty_score += 0.2
        
        # Message language complexity
        words = message.split()
        if len(words) < 3:
            difficulty_score -= 0.1  # Very short = easy to classify
        elif len(words) > 20:
            difficulty_score += 0.1  # Long = more context needed
        
        # Non-English adds difficulty
        ascii_ratio = sum(1 for c in message if ord(c) < 128) / max(1, len(message))
        if ascii_ratio < 0.5:
            difficulty_score += 0.15  # Non-Latin script
        
        # Mixed language (code-switching) is hardest
        if ascii_ratio > 0.3 and ascii_ratio < 0.7:
            difficulty_score += 0.2  # Mixed language
        
        difficulty_score = max(0.05, min(0.99, difficulty_score))
        
        return {
            "classification_difficulty": round(difficulty_score, 3),
            "reasoning_depth_required": (
                "shallow" if difficulty_score < 0.3 else
                "moderate" if difficulty_score < 0.6 else
                "deep" if difficulty_score < 0.8 else
                "expert"
            ),
            "requires_domain_knowledge": category in ("maintenance", "quality", "crisis"),
            "requires_temporal_context": category in ("crisis", "supply_chain", "business"),
            "curriculum_stage": (
                1 if difficulty_score < 0.3 else
                2 if difficulty_score < 0.5 else
                3 if difficulty_score < 0.7 else
                4
            ),
        }
    
    def _generate_reasoning_chain(self, category: str, subtype: str,
                                   eq_health: float, fatigue: float, message: str) -> Dict:
        """Expert reasoning chain (chain-of-thought for AI training).
        
        Shows HOW an expert would analyze this event step by step.
        """
        steps = []
        
        # Step 1: Observation
        steps.append(f"observe: {category} event detected — {subtype.replace('_', ' ')}")
        
        # Step 2: Context assessment
        if eq_health < 0.5:
            steps.append(f"context: equipment health critically low ({eq_health:.0%}) — amplifies risk")
        elif eq_health < 0.8:
            steps.append(f"context: equipment showing wear ({eq_health:.0%}) — monitor closely")
        else:
            steps.append(f"context: equipment in good condition ({eq_health:.0%})")
        
        # Step 3: Human factor
        if fatigue < 0.5:
            steps.append(f"human_factor: operator alertness low ({fatigue:.0%}) — higher error risk")
        else:
            steps.append(f"human_factor: operator alert ({fatigue:.0%}) — reliable observations")
        
        # Step 4: Risk judgment
        if category in ("crisis", "safety_accidents"):
            steps.append("risk_judgment: immediate attention required — safety takes priority")
            steps.append("action: escalate, isolate area, verify personnel safety")
        elif category == "maintenance" and eq_health < 0.6:
            steps.append("risk_judgment: degradation trend — schedule intervention before failure")
            steps.append("action: plan maintenance within next shift, prepare spare parts")
        elif category == "quality":
            steps.append("risk_judgment: product integrity at stake — contain and investigate")
            steps.append("action: quarantine affected batch, trace root cause")
        else:
            steps.append("risk_judgment: within normal operational range")
            steps.append("action: log and continue, no escalation needed")
        
        # Final conclusion
        conclusion = (
            "escalate_immediately" if category in ("crisis", "safety_accidents") else
            "schedule_action" if category in ("maintenance", "quality") and eq_health < 0.7 else
            "monitor_and_log"
        )
        
        return {
            "steps": steps,
            "conclusion": conclusion,
            "confidence": round(0.7 + self.rng.uniform(0, 0.25), 3),
            "reasoning_type": (
                "deductive" if category in ("maintenance", "quality") else
                "abductive" if category in ("crisis", "safety_accidents") else
                "inductive"
            ),
        }
    
    def _compute_anomaly_score(self, category: str, subtype: str,
                               eq_health: float, fatigue: float,
                               event_position: int) -> Dict:
        """How anomalous is this event in context?
        
        Enables unsupervised anomaly detection training.
        """
        # Base anomaly from category rarity
        rare_cats = {"crisis": 0.95, "safety_accidents": 0.8, "mergers_acquisitions": 0.9,
                     "evolution": 0.85, "mistakes_failures": 0.6}
        common_cats = {"daily_ops": 0.05, "human_relations": 0.08, "routine_monitoring": 0.03}
        
        if category in rare_cats:
            base_anomaly = rare_cats[category]
        elif category in common_cats:
            base_anomaly = common_cats[category]
        else:
            base_anomaly = 0.3
        
        # Context anomaly: does equipment state make this unexpected?
        context_boost = 0.0
        if eq_health > 0.9 and category in ("maintenance", "crisis"):
            context_boost = 0.2  # Equipment healthy but failure? Very anomalous
        if fatigue > 0.9 and category in ("mistakes_failures",):
            context_boost = -0.1  # Tired + mistake = expected, less anomalous
        
        # Temporal anomaly: early in shift = less likely for fatigue events
        if event_position < 10 and category in ("mistakes_failures",):
            context_boost += 0.15  # Too early for fatigue-related errors
        
        score = max(0.01, min(0.99, base_anomaly + context_boost + self.rng.gauss(0, 0.05)))
        
        return {
            "anomaly_score": round(score, 3),
            "anomaly_type": (
                "rare_event" if score > 0.8 else
                "contextual_anomaly" if context_boost > 0.1 else
                "mild_deviation" if score > 0.4 else
                "normal_operation"
            ),
            "expected_frequency": (
                "once_per_year" if score > 0.9 else
                "once_per_month" if score > 0.7 else
                "once_per_week" if score > 0.4 else
                "multiple_per_day"
            ),
            "isolation_forest_label": 1 if score > 0.7 else 0,  # Binary anomaly label
        }
    
    def _compute_risk_matrix(self, category: str, subtype: str, eq_health: float) -> Dict:
        """Risk = Probability × Impact with confidence bounds.
        
        Standard industrial risk matrix (5×5).
        """
        # Probability of recurrence (1-5 scale)
        prob_map = {"daily_ops": 5, "human_relations": 5, "maintenance": 3,
                    "quality": 3, "supply_chain": 2, "safety_accidents": 1,
                    "crisis": 1, "mistakes_failures": 2}
        probability = prob_map.get(category, 3)
        
        # Impact severity (1-5 scale)
        impact_map = {"daily_ops": 1, "human_relations": 1, "maintenance": 3,
                      "quality": 3, "supply_chain": 3, "safety_accidents": 4,
                      "crisis": 5, "mistakes_failures": 2, "business": 3}
        impact = impact_map.get(category, 2)
        
        # Equipment health modifies impact
        if eq_health < 0.4:
            impact = min(5, impact + 1)
        
        risk_score = probability * impact
        
        return {
            "probability": probability,
            "probability_label": ["", "rare", "unlikely", "possible", "likely", "almost_certain"][probability],
            "impact": impact,
            "impact_label": ["", "negligible", "minor", "moderate", "major", "catastrophic"][impact],
            "risk_score": risk_score,
            "risk_level": (
                "critical" if risk_score >= 20 else
                "high" if risk_score >= 12 else
                "medium" if risk_score >= 6 else
                "low"
            ),
            "confidence_interval": [max(1, risk_score - 3), min(25, risk_score + 3)],
            "mitigation_priority": min(5, max(1, risk_score // 5)),
        }
    
    def _generate_kg_triples(self, category: str, subtype: str,
                              worker: Dict, message: str) -> List:
        """Knowledge graph triples: (subject, relation, object).
        
        Enables building industry knowledge graphs from data.
        """
        asset = self.rng.choice(self.industry.typical_assets).replace("_", " ")
        process = self.rng.choice(self.industry.key_processes).replace("_", " ")
        
        triples = [
            # Core event triple
            [worker["role"].replace("_", " "), "reported", f"{subtype.replace('_', ' ')}"],
            # Asset relationship
            [asset, "involved_in", category],
            # Industry context
            [self.industry.id, "has_process", process],
        ]
        
        # Category-specific triples
        if category == "maintenance":
            triples.append([asset, "requires", "maintenance_action"])
            triples.append(["maintenance_event", "affects", "production_schedule"])
        elif category in ("crisis", "safety_accidents"):
            triples.append(["incident", "triggers", "investigation"])
            triples.append(["safety_event", "requires", "immediate_response"])
        elif category == "quality":
            triples.append(["quality_issue", "affects", "product_batch"])
            triples.append(["deviation", "requires", "root_cause_analysis"])
        
        return triples
    
    def _generate_summaries(self, category: str, subtype: str, message: str) -> Dict:
        """Multi-granularity summary of the event.
        
        Trains models to summarize at different levels.
        """
        # One-word classification
        one_word = category.split("_")[0] if "_" in category else category
        
        # One-line summary
        subtype_clean = subtype.replace("_", " ")
        one_line = f"{category.replace('_', ' ')} event: {subtype_clean}"
        
        # Detailed summary (what happened + context + implication)
        implications = {
            "crisis": "requires immediate response and investigation",
            "safety_accidents": "needs safety review and corrective action",
            "maintenance": "equipment needs attention to prevent further degradation",
            "quality": "product integrity may be compromised",
            "supply_chain": "may impact production schedule",
            "daily_ops": "normal operational activity",
            "human_relations": "workplace social interaction",
        }
        impl = implications.get(category, "operational event recorded")
        detailed = f"{one_line}. {impl}. shift: {self.shift}."
        
        return {
            "one_word": one_word,
            "one_line": one_line,
            "detailed": detailed,
            "category_hierarchy": [self.industry.sector, category, subtype],
        }
    
    def _generate_learning_objectives(self, category: str, subtype: str,
                                       difficulty: Dict) -> Dict:
        """What exactly should a model learn from this record?
        
        Defines supervised, unsupervised, and reinforcement learning targets.
        """
        return {
            "supervised_tasks": [
                {"task": "event_classification", "label": category, "granularity": "category"},
                {"task": "subtype_classification", "label": subtype, "granularity": "subtype"},
                {"task": "urgency_detection", "label": (
                    "critical" if category in ("crisis",) else
                    "high" if category in ("safety_accidents",) else
                    "medium" if category in ("maintenance", "quality") else
                    "low"
                )},
                {"task": "sentiment_analysis", "label": (
                    "negative" if category in ("crisis", "safety_accidents", "mistakes_failures") else
                    "positive" if category in ("human_relations", "holidays_breaks") else
                    "neutral"
                )},
            ],
            "unsupervised_tasks": [
                "anomaly_detection",
                "temporal_pattern_discovery",
                "topic_clustering",
                "worker_behavior_profiling",
            ],
            "reinforcement_learning": {
                "state": f"equipment_health + fatigue + event_history",
                "action_space": ["escalate", "schedule_maintenance", "monitor", "ignore"],
                "reward_signal": "minimize_downtime_cost + maximize_safety",
            },
            "curriculum_stage": difficulty.get("curriculum_stage", 2),
            "prerequisite_knowledge": [
                "industrial_operations" if difficulty.get("requires_domain_knowledge") else "general",
                "temporal_reasoning" if difficulty.get("requires_temporal_context") else "single_event",
            ],
        }
    
    def _detect_message_language(self, message: str) -> str:
        """Detect actual language of the final message text.
        Uses character-range detection on first 60 chars for speed.
        """
        if not message or len(message) < 2:
            return "en"
        
        # Only scan first 60 chars (enough to detect script, much faster)
        sample = message[:60]
        total = len(sample)
        arabic_chars = sum(1 for c in sample if '\u0600' <= c <= '\u06FF')
        devanagari_chars = sum(1 for c in sample if '\u0900' <= c <= '\u097F')
        telugu_chars = sum(1 for c in sample if '\u0C00' <= c <= '\u0C7F')
        tamil_chars = sum(1 for c in sample if '\u0B80' <= c <= '\u0BFF')
        kannada_chars = sum(1 for c in sample if '\u0C80' <= c <= '\u0CFF')
        japanese_chars = sum(1 for c in sample if '\u3040' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FFF')
        korean_chars = sum(1 for c in sample if '\uAC00' <= c <= '\uD7AF')
        cyrillic_chars = sum(1 for c in sample if '\u0400' <= c <= '\u04FF')
        thai_chars = sum(1 for c in sample if '\u0E00' <= c <= '\u0E7F')
        
        # Determine dominant script
        threshold = total * 0.3  # 30% of chars determines language
        
        if arabic_chars > threshold:
            return "ar"
        elif devanagari_chars > threshold:
            return "hi"
        elif telugu_chars > threshold:
            return "te"
        elif tamil_chars > threshold:
            return "ta"
        elif kannada_chars > threshold:
            return "kn"
        elif japanese_chars > threshold:
            return "ja"
        elif korean_chars > threshold:
            return "ko"
        elif cyrillic_chars > threshold:
            return "ru"
        elif thai_chars > threshold:
            return "th"
        
        # Latin script — check for non-English patterns
        msg_lower = sample.lower()
        if any(w in msg_lower for w in ['bhai', 'karo', 'hai', 'nahi', 'aaj', 'kal']):
            return "hi_latin"
        elif any(w in msg_lower for w in ['undi', 'cheyy', 'andi', 'ayyi', 'chesaru']):
            return "te_latin"
        elif any(w in msg_lower for w in ['irukku', 'panna', 'venum', 'thaan']):
            return "ta_latin"
        elif any(w in msg_lower for w in ['der ', 'die ', 'und ', 'ist ', 'nicht']):
            return "de"
        elif any(w in msg_lower for w in ['est ', 'les ', 'une ', 'pas ', 'pour']):
            return "fr"
        elif any(w in msg_lower for w in ['está', 'para', 'como', 'más', 'pero']):
            return "es"
        elif any(w in msg_lower for w in ['está', 'para', 'não', 'mais', 'como']):
            return "pt"
        
        # Mixed script = code-switch
        non_ascii = sum(1 for c in sample if ord(c) > 127)
        ascii_chars = total - non_ascii
        if non_ascii > total * 0.2 and ascii_chars > total * 0.2:
            return "code_switch"
        
        return "en"
    
    def _get_worker_name(self, worker: Dict) -> str:
        """Generate a realistic name based on worker's country/language."""
        # Use hash of worker ID for consistent name
        name_rng = random.Random(hash(worker["id"]) % (2**32))
        
        indian_names = ["Raju", "Suresh", "Venkat", "Priya", "Anand", "Lakshmi", "Kumar", 
                       "Srinivas", "Ramesh", "Deepa", "Gopal", "Sita", "Arjun", "Kavitha",
                       "Shankar", "Meena", "Ravi", "Sunita", "Mohan", "Geetha"]
        arabic_names = ["Ahmed", "Fatima", "Mohammad", "Aisha", "Omar", "Khalid", "Yusuf",
                       "Hassan", "Ali", "Noor", "Ibrahim", "Salma", "Tariq", "Layla"]
        western_names = ["James", "Sarah", "Michael", "Emma", "David", "Anna", "Robert",
                        "Lisa", "John", "Maria", "Thomas", "Sophie", "Mark", "Julia"]
        japanese_names = ["Tanaka", "Suzuki", "Sato", "Yamamoto", "Watanabe", "Nakamura",
                         "Kobayashi", "Takahashi", "Ito", "Kato"]
        chinese_names = ["Wei", "Fang", "Jun", "Hui", "Ming", "Xiao", "Lin", "Chen", "Zhang", "Wang"]
        
        country = worker.get("country", self.country)
        if country in ("IN",):
            return name_rng.choice(indian_names)
        elif country in ("SA", "AE", "EG"):
            return name_rng.choice(arabic_names)
        elif country in ("JP",):
            return name_rng.choice(japanese_names)
        elif country in ("CN", "TW"):
            return name_rng.choice(chinese_names)
        else:
            return name_rng.choice(western_names)
    
    def _generate_reactions(self) -> Optional[List]:
        """Generate emoji reactions (like WhatsApp/Slack reactions)."""
        if self.rng.random() > 0.12:  # 12% of messages get reactions
            return None
        reactions = ["👍", "👍", "👍", "✅", "❤️", "😂", "👀", "🙏", "💪", "🔥"]
        n = self.rng.randint(1, 3)
        return self.rng.sample(reactions, n)
    
    def _compute_sentiment(self, message: str, category: str) -> float:
        """Compute sentiment score (-1.0 to +1.0) for the message."""
        # Category-based base sentiment
        base = {"crisis": -0.8, "safety_accidents": -0.6, "mistakes_failures": -0.5,
                "human_relations": 0.4, "holidays_breaks": 0.6, "daily_ops": 0.1,
                "maintenance": -0.2, "quality": -0.3, "supply_chain": -0.2,
                "business": 0.0, "workforce": -0.1}
        sentiment = base.get(category, 0.0)
        
        # Message-level adjustments
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["😂", "🎉", "happy", "great", "good", "nice", "perfect"]):
            sentiment += 0.3
        if any(w in msg_lower for w in ["😤", "problem", "failed", "broken", "urgent", "stop"]):
            sentiment -= 0.3
        
        # Add noise
        sentiment += self.rng.gauss(0, 0.1)
        return round(max(-1.0, min(1.0, sentiment)), 3)
    
    def _compute_urgency(self, category: str, subtype: str, eq_health: float) -> float:
        """Compute urgency score 0.0-1.0."""
        base = {"crisis": 0.95, "safety_accidents": 0.8, "maintenance": 0.4,
                "mistakes_failures": 0.5, "quality": 0.4, "supply_chain": 0.3,
                "daily_ops": 0.1, "human_relations": 0.05}
        urgency = base.get(category, 0.2)
        
        # Equipment health amplifies urgency
        if eq_health < 0.3:
            urgency = min(1.0, urgency + 0.3)
        elif eq_health < 0.6:
            urgency = min(1.0, urgency + 0.1)
        
        urgency += self.rng.gauss(0, 0.05)
        return round(max(0.0, min(1.0, urgency)), 3)
    
    def _estimate_event_cost(self, category: str, subtype: str) -> float:
        """Estimate actual cost impact of this event in USD."""
        cost_ranges = {
            "crisis": (10000, 500000),
            "safety_accidents": (1000, 100000),
            "maintenance": (500, 50000),
            "mistakes_failures": (200, 20000),
            "quality": (100, 30000),
            "supply_chain": (500, 25000),
            "business": (0, 5000),
            "daily_ops": (0, 0),
            "human_relations": (0, 0),
        }
        low, high = cost_ranges.get(category, (0, 1000))
        if high == 0:
            return 0.0
        # Most events have low cost, few have high (exponential distribution)
        cost = low + self.rng.expovariate(3.0 / (high - low)) if high > low else 0
        return round(min(cost, high), 2)
    
    def _get_current_weather(self) -> Dict:
        """Get weather from cached state snapshot."""
        env = self._cached_snapshot.get("environment", {})
        return {
            "temperature_c": env.get("ambient_temperature_c", 25.0),
            "humidity_pct": env.get("humidity_pct", 50.0),
            "condition": env.get("weather_event") or "clear",
        }
    
    def _get_equipment_age(self) -> float:
        """Get worst equipment's age in hours from cached snapshot."""
        worst = self._cached_snapshot.get("digital_twin", {}).get("worst_equipment", {})
        rul = worst.get("remaining_useful_life_hours", 5000)
        health = worst.get("health", 0.9)
        total_life = rul / max(0.01, health)
        age = total_life - rul
        return round(max(0, age), 1)
    
    def _extract_named_entities(self, message: str, worker: Dict, category: str) -> Dict:
        """Extract structured named entities from message text."""
        entities = {"persons": [], "equipment": [], "measurements": [], "locations": [], "materials": []}
        
        # Equipment mentioned
        for asset in self.industry.typical_assets:
            clean = asset.replace("_", " ")
            if clean.lower() in message.lower():
                entities["equipment"].append(clean)
        
        # Measurements (numbers with units)
        import re
        measurements = re.findall(r'\d+\.?\d*\s*(?:°C|%|mm|bar|psi|kg|tonnes|TPH|MW|m³|ppm)', message)
        entities["measurements"] = measurements[:3]
        
        # Locations
        for zone in self._facility_zones:
            if zone.lower() in message.lower():
                entities["locations"].append(zone)
        
        # Materials
        for mat in self.industry.raw_materials[:5]:
            clean = mat.replace("_", " ")
            if clean.lower() in message.lower():
                entities["materials"].append(clean)
        
        # Worker role as person entity
        entities["persons"].append({"id": worker["id"], "role": worker["role"].replace("_", " ")})
        
        return entities
    
    def _generate_qa_pair(self, category: str, subtype: str, message: str, worker: Dict) -> Dict:
        """Generate QA pair by extracting from the ACTUAL message (no LLM needed).
        
        Uses pattern matching to find what the message is about,
        then builds a relevant question and answer from it.
        """
        msg_lower = message.lower()
        words = message.split()
        
        # Extract key entities from the actual message
        mentioned_asset = None
        for asset in self.industry.typical_assets:
            if asset.replace("_", " ").lower() in msg_lower:
                mentioned_asset = asset.replace("_", " ")
                break
        
        mentioned_material = None
        for mat in self.industry.raw_materials[:5]:
            if mat.replace("_", " ").lower() in msg_lower:
                mentioned_material = mat.replace("_", " ")
                break
        
        # Extract numbers/readings from message
        import re
        numbers = re.findall(r'(\d+\.?\d*)\s*(%|°C|bar|psi|mm|kg|hours?|min)', message)
        has_reading = len(numbers) > 0
        
        # Build question based on what's ACTUALLY in the message
        if mentioned_asset:
            # Asset-specific question
            q = self.rng.choice([
                f"What is the status of {mentioned_asset}?",
                f"Is there a problem with {mentioned_asset}?",
                f"What was reported about {mentioned_asset}?",
                f"Does {mentioned_asset} need attention?",
            ])
            # Answer references the actual message content
            if category in ("crisis", "safety_accidents"):
                a = f"{mentioned_asset} has an issue requiring immediate attention. {subtype.replace('_', ' ')} reported."
            elif category == "maintenance":
                a = f"{mentioned_asset} needs maintenance. Current status being monitored."
            else:
                a = f"{mentioned_asset} is operational. No immediate concerns."
        
        elif has_reading:
            # Measurement-specific question
            val, unit = numbers[0]
            q = f"What is the current reading showing {val}{unit}?"
            if float(val) > 80 and unit in ('%', '°C'):
                a = f"Reading at {val}{unit} — elevated. Monitoring for further changes."
            else:
                a = f"Reading at {val}{unit} — within normal operating range."
        
        elif category in ("crisis", "safety_accidents"):
            # Emergency-specific (use first meaningful words from message)
            first_phrase = " ".join(words[:6]) if len(words) > 6 else message
            q = f"What emergency was reported?"
            a = f"{subtype.replace('_', ' ')} event. {first_phrase}. Response initiated."
        
        elif category == "quality":
            q = "What quality issue was identified?"
            a = f"{subtype.replace('_', ' ')} detected. Investigation in progress."
        
        elif mentioned_material:
            q = f"What is the status of {mentioned_material} supply?"
            a = f"{mentioned_material} — {self.rng.choice(['adequate stock', 'running low', 'delivery pending', 'received today'])}."
        
        else:
            # Fallback: use the subtype as the topic
            subtype_clean = subtype.replace("_", " ")
            q = self.rng.choice([
                f"What is happening regarding {subtype_clean}?",
                f"Report on {subtype_clean}?",
                f"Status of {subtype_clean} situation?",
            ])
            # Use first part of actual message as answer basis
            answer_basis = " ".join(words[:8]) if len(words) > 8 else message
            a = f"{answer_basis}. Situation {'under control' if category in ('daily_ops', 'human_relations') else 'being addressed'}."
        
        return {"question": q, "answer": a, "context": message[:100]}
    
    def _generate_instruction_response(self, category: str, subtype: str, message: str) -> Dict:
        """Generate instruction→response pair for instruction-tuning LLMs."""
        asset = self.rng.choice(self.industry.typical_assets).replace("_", " ")
        process = self.rng.choice(self.industry.key_processes).replace("_", " ")
        
        if category == "maintenance":
            instruction = self.rng.choice([
                f"Check the condition of {asset} and report findings",
                f"Perform routine inspection on {asset}",
                f"Diagnose the issue with {asset} and recommend action",
            ])
            response = self.rng.choice([
                f"Inspected {asset}. Condition acceptable. Next service due in 2 weeks.",
                f"Found minor wear on {asset}. Recommending scheduled replacement at next downtime.",
                f"Checked {asset}. All parameters within spec. Documented in shift log.",
            ])
        elif category in ("crisis", "safety_accidents"):
            instruction = self.rng.choice([
                "Assess the situation and report severity",
                "Execute emergency response protocol",
                "Evacuate area and confirm all personnel safe",
            ])
            response = self.rng.choice([
                "Area secured. All personnel at muster point. Awaiting further instructions.",
                "Situation assessed: contained. No injuries. Investigation team notified.",
                "Emergency protocol executed. Situation under control. Standby for all-clear.",
            ])
        else:
            instruction = self.rng.choice([
                f"Provide status update on {process}",
                f"Complete the {process} task and confirm",
                f"Monitor {asset} for the next hour and report any changes",
            ])
            response = self.rng.choice([
                f"{process} proceeding normally. No deviations observed.",
                f"Task complete. Results documented. Moving to next activity.",
                f"Monitoring {asset}. All readings stable. Will update if any change.",
            ])
        
        return {"instruction": instruction, "response": response}
    
    def _generate_embedding_hint(self, category: str, subtype: str) -> Dict:
        """Semantic hints for embedding model training.
        
        Tells the model what this event is SIMILAR to and DIFFERENT from.
        """
        # Similar events (should have close embeddings)
        similarity_map = {
            "maintenance": ["equipment_repair", "preventive_check", "spare_parts", "tool_maintenance"],
            "crisis": ["emergency_response", "safety_incident", "plant_shutdown", "evacuation"],
            "safety_accidents": ["near_miss", "injury_report", "hazard_observation", "ppe_violation"],
            "quality": ["inspection_result", "defect_report", "specification_check", "rework"],
            "daily_ops": ["routine_check", "shift_start", "production_update", "normal_operation"],
            "human_relations": ["team_interaction", "break_time", "social_chat", "celebration"],
            "supply_chain": ["delivery_status", "inventory_check", "vendor_communication", "logistics"],
            "business": ["financial_update", "target_review", "client_communication", "planning"],
        }
        
        # Dissimilar events (should have distant embeddings)
        dissimilar_map = {
            "maintenance": ["celebration", "social_chat", "business_meeting"],
            "crisis": ["routine_check", "break_time", "normal_operation"],
            "human_relations": ["emergency_response", "equipment_failure", "quality_defect"],
            "daily_ops": ["crisis_event", "plant_shutdown", "major_accident"],
        }
        
        similar = similarity_map.get(category, ["general_operation"])
        dissimilar = dissimilar_map.get(category, ["unrelated_event"])
        
        return {
            "semantic_cluster": category,
            "similar_to": similar,
            "dissimilar_from": dissimilar,
            "topic_keywords": [category, subtype.replace("_", " "), self.industry.subsector],
        }
    
    def _pick_language(self, worker: Dict) -> str:
        """Pick language based on worker and situation."""
        langs = worker["languages"]
        # 58% English, 26% code-switch, 16% native
        r = self.rng.random()
        if r < 0.58:
            return "en"
        elif r < 0.84:
            return "code_switch"
        else:
            return langs[0] if langs[0] != "en" else "en"
    
    def _generate_message(self, lang: str, category: str, subtype: str,
                          worker: Dict) -> str:
        """Generate a realistic message in the chosen language."""
        # ═══ NIGHT BEHAVIOR: Use industry-specific night templates ═══
        hour = self.current_date.hour
        if (hour >= 22 or hour <= 5) and self.rng.random() < 0.35:
            # 35% of night events use industry-specific night templates
            night_msg = get_industry_message(
                self.industry.id, self.industry.subsector, "night", self.rng
            )
            if night_msg:
                return night_msg
        
        # Build industry-specific message first
        industry_msg = self._build_industry_message(category, subtype, worker)
        
        # Add context from active shocks if any affect this industry
        if self.black_swan.active_shocks and self.rng.random() < 0.25:
            affecting = [
                s for s in self.black_swan.active_shocks
                if (self.industry.id in s.affected_industries or
                    any(link.target_industry == self.industry.id
                        for aff in s.affected_industries
                        for link in self.dependency_graph.get_downstream_dependents(aff)))
            ]
            if affecting:
                shock = self.rng.choice(affecting)
                shock_mentions = {
                    "pandemic": [
                        "everyone talking about the lockdown situation",
                        "checking temperatures at the entrance due to the pandemic",
                        "many people absent today due to quarantine guidelines",
                    ],
                    "earthquake": [
                        "inspecting buildings for structural cracks after the tremor",
                        "roads are blocked nearby following the earthquake",
                        "vibrations felt during the shift, checking foundations",
                    ],
                    "cyberattack": [
                        "systems are extremely slow, IT says cyberattack on servers",
                        "manual logging today as database servers are offline",
                        "screens showing connection errors, cyber security team investigating",
                    ],
                    "port_shutdown": [
                        "customs cleared shipment, but port congestion is critical",
                        "vessels delayed at harbor, waiting for shipping clearance",
                        "raw material supply stuck at the main cargo port",
                    ],
                    "fuel_shortage": [
                        "fuel prices skyrocketed today, diesel limit enforced",
                        "truck deliveries delayed due to transport fuel shortage",
                        "conserving diesel for critical generators only",
                    ],
                    "flood": [
                        "heavy waterlogging in the yard, pumping out water",
                        "flooding near the highway slowing down shift changes",
                        "rainwater leaking into warehouse sector B",
                    ],
                    "trade_war": [
                        "new export tariffs announced, looking at price impact",
                        "shipment delayed at border due to regulatory dispute",
                        "tariffs affecting material costs on importing parts",
                    ],
                    "grid_collapse": [
                        "power cut, backup generators running at full capacity",
                        "unstable voltage from substation, equipment offline",
                        "grid collapse affecting regional industrial zone",
                    ],
                    "regulatory_ban": [
                        "new strict compliance checklist received from ministry",
                        "audit team inspects the premises under new environmental ban",
                        "urgently auditing the chemical storage for compliance",
                    ]
                }
                mentions = shock_mentions.get(shock.shock_type, ["disruption felt across the sector"])
                mention = self.rng.choice(mentions)
                industry_msg = f"{industry_msg} — {mention}"
        
        if lang == "code_switch":
            native = worker["languages"][0] if worker["languages"][0] != "en" else "te"
            if native in WORKPLACE_PHRASES and WORKPLACE_PHRASES[native]:
                native_part = self.rng.choice(WORKPLACE_PHRASES[native])
                # Natural code-switch: start in native, switch to English for technical terms
                parts = industry_msg.split(" ")
                switch_point = self.rng.randint(1, max(2, len(parts)//2))
                en_technical = " ".join(parts[switch_point:]) if switch_point < len(parts) else industry_msg
                # Take first half of a native fragment as the greeting/intro
                native_intro = native_part.split(",")[0] if "," in native_part else native_part[:30]
                return f"{native_intro}, {en_technical}"
            lang = "en"
        
        if lang != "en" and lang in WORKPLACE_PHRASES and WORKPLACE_PHRASES[lang]:
            return self.rng.choice(WORKPLACE_PHRASES[lang])
        
        return industry_msg
    
    def _build_industry_message(self, category: str, subtype: str, worker: Dict) -> str:
        """Build a message that's specific to THIS industry and event."""
        asset = self.rng.choice(self.industry.typical_assets).replace("_", " ")
        process = self.rng.choice(self.industry.key_processes).replace("_", " ")
        product = self.rng.choice(self.industry.typical_products).replace("_", " ")
        role = worker["role"].replace("_", " ")
        
        # ═══ INDUSTRY-SPECIFIC TEMPLATES (highest priority) ═══
        # Try to get a researched, industry-accurate message first
        specific_msg = get_industry_message(
            self.industry.id, self.industry.subsector, category, self.rng
        )
        if specific_msg and self.rng.random() < 0.65:  # 65% use specific, 35% generic variety
            self._last_msg_was_specific = True
            return specific_msg
        
        # ═══ DRILL & TRAINING EVENT INJECTION ═══
        # Realistic frequency based on actual regulations
        drill_msg = should_inject_drill(self.industry.subsector, self.rng)
        if drill_msg:
            self._last_msg_was_specific = True
            return drill_msg
        
        # ═══ SEASONAL PATTERN INJECTION ═══
        seasonal_msg = get_seasonal_message(
            self.industry.id, self.current_date.month, self.rng,
            country=self.country, subsector=self.industry.subsector)
        if seasonal_msg:
            self._last_msg_was_specific = True
            return seasonal_msg
        
        self._last_msg_was_specific = False
        
        # ═══ FIX 12: QUIET/MUNDANE "NOTHING HAPPENS" EVENTS ═══
        # Real shifts are 80% boring. Inject mundane events ~15% of the time.
        if self.rng.random() < 0.15 and category == "daily_ops":
            mundane_events = [
                f"all systems normal. {asset} running steady",
                f"routine check on {asset} — nothing to report",
                f"quiet shift so far. {process} running smooth",
                f"{asset} readings all within spec. boring day so far",
                f"hourly walkthrough complete. everything ok",
                f"no issues since last update. {product} production on track",
                f"same as usual. {process} area clear",
                f"just sitting here watching {asset} gauges. all green",
                f"nothing new to report on {asset}. next check in 2 hrs",
                f"end of round. all equipment status normal",
                f"did my rounds. {asset} ok, {process} area ok, everything ok",
                f"status update: nothing happening. literally nothing",
                f"all clear on floor. production steady at target",
                f"passed by {asset}. sounds normal. looks normal. is normal",
                f"log entry: {self.current_date.strftime('%H:%M')} — no abnormalities detected",
                f"zone walkthrough done. all panels green. all doors secure",
                f"checked {asset}. fine. checked {process} area. fine. going for chai",
                f"slow day. {product} line moving at normal speed. no complaints",
                f"nothing to escalate. {asset} operating within parameters",
                f"routine log: all KPIs green. shift proceeding normally",
                f"absolutely nothing happening here. just the hum of {asset}",
                f"update for logbook: nil report. all ok",
                f"third round this shift. still nothing out of ordinary",
                f"supervisor asked for update — told him same as last hour: all fine",
            ]
            return self.rng.choice(mundane_events)
        
        # ═══ FIX 13: FALSE ALARMS AND NEAR-MISSES ═══
        # Real plants have alarms that trigger for nothing (~3% of events)
        if self.rng.random() < 0.03:
            false_alarms = [
                f"alarm on {asset} — checked it, false alarm. sensor acting up again",
                f"🚨 got alert on {asset} panel but readings normal. resetting alarm",
                f"false alarm on {asset} temperature. probe needs recalibration",
                f"Level alarm triggered on {asset} but visual check shows normal",
                f"{asset} tripped alarm. went to check — it was a rat near the sensor 🐀",
                f"smoke detector went off near {process} area. just steam from the pipe. false alarm",
                f"got a high-pressure alert on {asset}. turned out to be a gauge malfunction",
                f"vibration alarm on {asset}. checked everything — it was the forklift passing nearby",
                f"fire panel showing zone {self.rng.randint(1,8)} alarm. investigated: nothing. dust on detector",
                f"emergency buzzer activated by mistake. someone bumped the panel. sorry all",
                f"gas detector alarming in {process} area. tested: all clear. sensor drift issue",
                f"alarm cleared. {asset} panel showed fault but diagnostic says healthy",
                f"third false alarm this week on {asset}. raising maintenance ticket for sensor check",
                f"overflow alarm on {asset} tank. actual level is fine. float switch stuck again",
                f"motion sensor triggered in restricted area. checked CCTV — it was a cat",
                f"⚠️ high temp alarm on {asset}. turned out ambient was high today, not equipment issue",
            ]
            return self.rng.choice(false_alarms)
        
        # Near-misses (~2% of events)
        if self.rng.random() < 0.02:
            near_misses = [
                f"close call near {asset}. {role} almost tripped on loose cable. fixed it immediately",
                f"near miss: wrench almost fell from top of {asset}. need to secure tools better",
                f"someone almost walked into {process} zone without clearance. stopped them just in time",
                f"load swung close to {role} team member near {asset}. everyone ok but scary moment",
                f"almost had a spill during {process}. caught it last second. cleaning up now",
                f"forklift came too close to pedestrian near {asset} area. driver warned",
                f"pressure spike on {asset} almost hit relief valve. backed off in time",
                f"near miss reported: loose {product} stack almost fell on walkway. restacked properly",
                f"caught {asset} belt slipping just before it could snap. lucky catch",
                f"hand almost got caught in {asset} pinch point. thank god for the guard rail",
                f"tripped near {asset} but didn't fall. uneven floor plate. marking it for repair",
                f"hot {product} almost dropped during transfer. grip was slippery. wearing new gloves now",
            ]
            return self.rng.choice(near_misses)
        
        # Category-specific templates (makes messages realistic)
        templates = {
            "daily_ops": [
                f"{process} started on schedule, {asset} running normal",
                f"shift handover: {asset} status is green, {product} output on target",
                f"starting {process} now, {role} team ready",
                f"daily checklist for {asset} completed, no issues found",
                f"{product} batch ready for next stage",
                f"all clear on {asset}, moving to {process}",
            ],
            "maintenance": [
                f"{asset} needs attention, vibration readings are off",
                f"scheduled maintenance on {asset}, will take 2 hours",
                f"replaced worn parts on {asset} during {process} downtime",
                f"lubrication done on {asset}, next due in 3 months",
                f"breakdown on {asset}, {process} halted until fixed",
                f"spare parts for {asset} ordered, ETA 2 days",
            ],
            "human_relations": [
                f"hey {role} team, chai break in 5 minutes",
                f"great work on yesterday's {product} batch everyone",
                f"who's coming for lunch? canteen has biryani today",
                f"congrats to the {process} team for zero defects this week",
                f"new colleague joining {role} team tomorrow",
                f"weekend plans anyone? thinking of a team outing",
            ],
            "safety_accidents": [
                f"near miss reported near {asset} during {process}",
                f"safety observation: PPE not worn near {asset} area",
                f"emergency drill scheduled for {process} section tomorrow",
                f"incident investigation: {asset} guard was removed",
                f"first aid given to {role} — minor cut during {process}",
                f"hazard identified: {self.rng.choice(self.industry.hazards).replace('_', ' ')}",
            ],
            "mistakes_failures": [
                f"wrong parameter set on {asset}, {product} batch affected",
                f"{role} forgot to log {process} completion in system",
                f"{asset} alarm ignored for too long, escalated now",
                f"miscommunication between shifts about {asset} status",
                f"quality issue: {product} out of spec due to {process} error",
                f"documentation not updated after {asset} maintenance",
            ],
            "supply_chain": [
                f"{self.rng.choice(self.industry.raw_materials).replace("_", " ")} delivery delayed by 2 days",
                f"inventory low on {self.rng.choice(self.industry.raw_materials).replace("_", " ")}, reorder placed",
                f"new vendor for {self.rng.choice(self.industry.raw_materials).replace("_", " ")} being evaluated",
                f"received wrong grade of {self.rng.choice(self.industry.raw_materials).replace("_", " ")} from supplier",
                f"{product} shipment dispatched to customer",
                f"warehouse at 90% capacity, need to expedite dispatch",
            ],
            "business": [
                f"this month's {product} production up 12% from last month",
                f"cost of {self.rng.choice(self.industry.raw_materials).replace("_", " ")} increased 8%",
                f"new contract signed for {product} supply",
                f"quarterly review: {process} efficiency improved",
                f"budget approved for {asset} upgrade next quarter",
                f"customer wants 20% more {product} starting next month",
            ],
            "crisis": [
                f"emergency shutdown initiated on {asset} due to critical situation",
                f"crisis team mobilized for {process} emergency",
                f"all hands on deck: major incident at {asset} area",
                f"safety sirens activated near {asset}, checking safety protocols",
                f"critical system failure on {asset} halting {process}!",
                f"blackout: lost all power to {asset} and {process} lines",
                f"catastrophe: massive disruption to {product} supply chain",
                f"disaster: unexpected event halting {process} completely",
            ],
        }
        
        # Get templates for this category, fall back to generic
        if category in templates:
            return self.rng.choice(templates[category])
        
        # Generic but still industry-specific
        generic = [
            f"{role} working on {process} with {asset}",
            f"update on {asset}: {process} progressing normally",
            f"{product} quality check passed",
            f"team discussion about {process} improvement",
            f"reminder: {asset} inspection due this week",
            f"meeting about {process} scheduling for next week",
            f"training session on {asset} operation completed",
            f"new procedure for {process} being rolled out",
            f"checking {asset} readings, looks normal today",
            f"{role} mentioned {asset} needs attention soon",
            f"today's {process} batch #{self.rng.randint(100,999)} going well",
            f"updating logbook entry for {asset} at {self.current_date.strftime('%H:%M')}",
            f"{product} output count: {self.rng.randint(50,500)} so far this shift",
            f"waiting for {self.rng.choice(self.industry.raw_materials).replace("_", " ")} delivery",
            f"just finished {process}, moving to next task",
            f"noise from {asset} section, probably normal",
            f"{role} team has {self.rng.randint(2,8)} people today",
            f"temperature reading on {asset}: {self.rng.randint(30,95)}C",
            f"shift progress: {self.rng.randint(40,90)}% of target done",
            f"all quiet in the {process} area right now",
        ]
        return self.rng.choice(generic)
    
    def _add_context(self, category: str, subtype: str) -> str:
        """Add contextual detail to message, including regional variations."""
        # 20% chance of region-specific context
        if self.rng.random() < 0.20:
            regional_contexts = self._get_regional_context()
            if regional_contexts:
                return self.rng.choice(regional_contexts)
        
        asset = self.rng.choice(self.industry.typical_assets).replace("_", " ")
        process = self.rng.choice(self.industry.key_processes).replace("_", " ")
        
        contexts = [
            f"happened near the {asset} area",
            f"third time this week",
            f"vendor was notified",
            f"shift lead is aware",
            f"will follow up tomorrow",
            f"same issue happened last month",
            f"need to order spare parts",
            f"weather isn't helping today",
            f"related to the {process} section",
            f"been going on since yesterday",
            f"nobody noticed till now",
            f"already informed maintenance",
            f"checking if this happened on previous shift too",
        ]
        return self.rng.choice(contexts)
    
    def _get_regional_context(self) -> list:
        """Get region-specific contextual messages based on country."""
        country = self.country
        
        # India-specific
        if country == "IN":
            return [
                "load shedding again... using DG set",
                "monsoon water coming inside from roof side",
                "local festival tomorrow, half the workers on leave",
                "KSEB/TNEB power cut from 2pm-4pm scheduled",
                "worker came late due to KSRTC bus delay",
                "humidity too high today, product quality affected",
                "local body inspection team coming tomorrow, prepare all files",
                "Diwali bonus announcement pending, everyone asking",
                "challan issued by pollution control board, need to fix stack emissions",
                "contractor labour didn't show up, local bandh today",
                "water tanker delayed, boiler makeup water running low",
                "union meeting after shift, attendance expected",
            ]
        # Middle East
        elif country in ("SA", "AE"):
            return [
                "outside temperature 48C today. limiting outdoor work to mornings only",
                "sandstorm warning, covering all outdoor equipment",
                "Ramadan shift timings starting next week",
                "compound visa renewal for 3 workers pending",
                "Friday prayer break — skeleton staff only",
                "dew point too high, compressor air quality affected",
                "labor camp transport delayed, 2nd shift starting late",
                "civil defense inspection scheduled tomorrow",
                "desert dust in air filters again, changing weekly instead of monthly",
            ]
        # Germany/Europe
        elif country in ("DE", "FR", "GB"):
            return [
                "works council meeting about overtime regulations",
                "TÜV inspection next month, documentation must be perfect",
                "energy costs up 40% since last quarter, management concerned",
                "Kurzarbeit discussion if orders don't recover by March",
                "betriebsrat approved new shift pattern starting Montag",
                "DIN standard update — reviewing impact on our process",
                "winter storm warning, checking backup power",
                "apprentice starting next week, need to prepare training plan",
                "environmental audit from Bezirksregierung next Tuesday",
            ]
        # Japan/Korea
        elif country in ("JP", "KR"):
            return [
                "earthquake drill scheduled for 14:00 today",
                "typhoon approaching, securing outdoor equipment",
                "golden week schedule posted — minimum manning confirmed",
                "kaizen suggestion from floor: relocate tool station 3m closer",
                "5S audit score improved from 3.2 to 4.1 this month",
                "new employee doing 3-month OJT rotation, assign mentor",
                "obon holidays — staggered shift coverage needed",
                "quality circle presentation next week, preparing slides",
            ]
        # China
        elif country in ("CN", "TW"):
            return [
                "CNY holiday schedule finalized — skeleton crew Jan 20-Feb 5",
                "new environmental inspection regulation from ministry",
                "power rationing notice from grid company",
                "worker dormitory AC repair request — summer heat unbearable",
                "customs clearance delay on imported spare parts",
                "local government safety campaign — extra inspections this month",
                "air quality alert today, limit outdoor operations",
            ]
        # Brazil/Latin America
        elif country in ("BR", "MX", "AR"):
            return [
                "Carnaval next week, production schedule adjusted",
                "heavy rain flooded access road, some workers stranded",
                "INMETRO calibration due this month",
                "power company scheduled maintenance — 4hr outage Sunday",
                "local sindicate meeting tomorrow afternoon",
                "dengue cases in area, fumigation team coming to premises",
                "customs hold on imported chemicals, production delayed",
            ]
        # Nigeria/Africa
        elif country in ("NG", "GH", "KE"):
            return [
                "NEPA power cut again, running on diesel generator",
                "fuel scarcity, generator diesel rationed this week",
                "rainy season flooding near access road",
                "local community liaison meeting scheduled",
                "import duty increase on spare parts — procurement impact",
                "harmattan dust affecting outdoor operations",
                "water borehole pump needs maintenance",
            ]
        # Thailand/SE Asia
        elif country in ("TH", "VN", "ID", "PH"):
            return [
                "Songkran holiday preparation — plant shutdown April 13-15",
                "monsoon season flooding risk, sandbagging loading dock",
                "motorcycle parking congestion causing shift change delays",
                "local labour shortage — workers prefer Bangkok factories",
                "power transformer overloaded in industrial estate",
                "Buddhist holiday tomorrow, Thai staff on leave",
            ]
        # Default / other
        return []
    
    def _add_detail(self, category: str, subtype: str, worker: Dict) -> str:
        """Add natural-sounding detail. No template labels or structured formats."""
        asset = self.rng.choice(self.industry.typical_assets).replace("_", " ")
        process = self.rng.choice(self.industry.key_processes).replace("_", " ")
        product = self.rng.choice(self.industry.typical_products).replace("_", " ")
        material = self.rng.choice(self.industry.raw_materials).replace("_", " ").replace("_", " ")
        hazard = self.rng.choice(self.industry.hazards).replace("_", " ")
        
        details = [
            f"been doing this for {worker['experience_years']:.0f} years, know the drill",
            f"the {asset} has been giving trouble lately",
            f"we're running low on {material}",
            f"this affects the {product} output",
            f"watch out for {hazard} in that area",
            f"{process} is the bottleneck right now",
            f"same thing happened last month with the {asset}",
            f"need to get this sorted before next shift arrives",
            f"supervisor wants an update on this by 4pm",
            f"vendor said the part will take 3 days to arrive",
            f"this is the third time this quarter",
            f"weather isn't helping today",
            f"we're behind schedule because of this",
            f"documented in the logbook already",
            f"next inspection is due in {self.rng.randint(2, 14)} days",
        ]
        return self.rng.choice(details)
    
    def _pick_assets(self) -> List[str]:
        """Pick relevant assets for this event."""
        n = self.rng.randint(0, 3)
        if n == 0:
            return []
        return self.rng.sample(self.industry.typical_assets, min(n, len(self.industry.typical_assets)))
    
    def _generate_tags(self, category: str, subtype: str) -> List[str]:
        """Generate tags for this record."""
        tags = [category, subtype, self.industry.subsector]
        if self.mood_state != "routine":
            tags.append(self.mood_state)
        if self.shift == "night":
            tags.append("night_shift")
        return tags


# Convenience function
seed = 42  # module-level for _generate_workers reference

def generate_episodes(industry_ids: List[str], lines_per_episode: int = 800,
                      episodes_per_industry: int = 3, year: int = 2024,
                      seed: int = 42) -> List[Dict]:
    """Generate episodes for multiple industries."""
    all_records = []
    
    for i, iid in enumerate(industry_ids):
        industry = INDUSTRIES[iid]
        for ep in range(episodes_per_industry):
            ep_seed = seed + i * 1000 + ep
            gen = EpisodeGenerator(industry, seed=ep_seed, year=year)
            records = gen.generate_episode(target_lines=lines_per_episode)
            all_records.extend(records)
    
    return all_records
